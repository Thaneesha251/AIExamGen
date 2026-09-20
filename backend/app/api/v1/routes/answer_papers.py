from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status, Response, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

try:
    from app.api.deps import get_db, get_current_user, require_admin_or_faculty
    from app.db.models import User, RoleEnum, AnswerPaperStatusEnum, AnswerPaper, AnswerPage, ExtractedAnswer, Examination, FileAsset
except ImportError:
    from backend.app.api.deps import get_db, get_current_user, require_admin_or_faculty
    from backend.app.db.models import User, RoleEnum, AnswerPaperStatusEnum, AnswerPaper, AnswerPage, ExtractedAnswer, Examination, FileAsset


from backend.app.schemas.answer_paper import (
    AnswerPaperResponse,
    AnswerPaperStatusResponse,
    ExtractedAnswerResponse,
    ExtractedAnswerUpdate,
    AnswerMappingRequest,
    AnswerMergeRequest
)
from backend.app.services.answer_paper_storage_service import AnswerPaperStorageService
from backend.app.services.answer_paper_processing_service import AnswerPaperProcessingService
from backend.app.services.ocr_review_service import OCRReviewService
from backend.app.services.storage.local_storage import LocalStorageService


router = APIRouter(prefix="/answer-papers", tags=["Answer Papers & OCR Pipeline"])

def user_is_student(user: User) -> bool:
    if not user or not user.role:
        return False
    r_val = user.role.name.value if hasattr(user.role.name, 'value') else str(user.role.name)
    return r_val == "STUDENT"

@router.post("/examinations/{exam_id}", response_model=AnswerPaperResponse, status_code=status.HTTP_201_CREATED)
async def upload_answer_paper(
    exam_id: str,
    background_tasks: BackgroundTasks,
    student_id: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload a student answer paper (PDF, JPG, PNG).
    Students upload for themselves; Faculty/Admin can upload on behalf of a student.
    """
    target_student_id = current_user.id
    if not user_is_student(current_user) and student_id:
        target_student_id = student_id
    elif user_is_student(current_user) and student_id and student_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Students cannot upload answer papers for other students."
        )

    storage_service = AnswerPaperStorageService(db)
    answer_paper = await storage_service.create_answer_paper_from_upload(
        examination_id=exam_id,
        student_id=target_student_id,
        file=file,
        uploaded_by_user_id=current_user.id
    )

    # Trigger OCR and segmentation processing in background task
    processing_service = AnswerPaperProcessingService(db)
    background_tasks.add_task(processing_service.process_answer_paper, answer_paper.id, current_user.id)

    return answer_paper


@router.get("/{paper_id}", response_model=AnswerPaperResponse)
def get_answer_paper_details(
    paper_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve detailed answer paper structure including pages and extracted answers."""
    paper = db.query(AnswerPaper).filter(AnswerPaper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Answer paper not found.")

    if user_is_student(current_user) and paper.student_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied to other student's submission.")

    return paper


@router.get("/{paper_id}/status", response_model=AnswerPaperStatusResponse)
def get_answer_paper_status(
    paper_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve live processing status and page count progress."""
    paper = db.query(AnswerPaper).filter(AnswerPaper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Answer paper not found.")

    if user_is_student(current_user) and paper.student_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied to other student's submission.")

    processing_service = AnswerPaperProcessingService(db)
    return processing_service.get_processing_status(paper_id)


@router.get("/examination/{exam_id}", response_model=List[AnswerPaperResponse])
def list_answer_papers_for_examination(
    exam_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List answer papers for an examination. Students only see their own submissions."""
    query = db.query(AnswerPaper).filter(AnswerPaper.examination_id == exam_id)

    if user_is_student(current_user):
        query = query.filter(AnswerPaper.student_id == current_user.id)

    return query.all()



@router.post("/{paper_id}/process", response_model=AnswerPaperResponse)
async def process_or_retry_answer_paper(
    paper_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_faculty)
):
    """Manually trigger or retry OCR processing and segmentation for an answer paper."""
    processing_service = AnswerPaperProcessingService(db)
    return await processing_service.process_answer_paper(paper_id, current_user.id)


@router.post("/{paper_id}/pages/{page_id}/ocr")
async def retry_single_page_ocr(
    paper_id: str,
    page_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_faculty)
):
    """Retry OCR extraction on a single page asset."""
    paper = db.query(AnswerPaper).filter(AnswerPaper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Answer paper not found.")

    page = db.query(AnswerPage).filter(
        AnswerPage.id == page_id,
        AnswerPage.answer_paper_id == paper_id
    ).first()
    if not page:
        raise HTTPException(status_code=404, detail="Answer page not found.")

    processing_service = AnswerPaperProcessingService(db)
    updated_page = await processing_service.process_single_page_ocr(page, paper)
    db.commit()
    return {"message": "Page OCR retried successfully", "page_id": page.id, "ocr_text": updated_page.ocr_text}


@router.put("/{paper_id}/extracted-answers/{answer_id}", response_model=ExtractedAnswerResponse)
def correct_ocr_text(
    paper_id: str,
    answer_id: str,
    req: ExtractedAnswerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_faculty)
):
    """Faculty edit OCR extracted answer text (marks extraction_method as HYBRID)."""
    review_service = OCRReviewService(db)
    return review_service.update_extracted_answer_text(
        answer_paper_id=paper_id,
        extracted_answer_id=answer_id,
        new_text=req.extracted_text,
        faculty_user_id=current_user.id
    )


@router.post("/{paper_id}/map-answer", response_model=ExtractedAnswerResponse)
def map_extracted_answer_to_question(
    paper_id: str,
    req: AnswerMappingRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_faculty)
):
    """Faculty map an extracted answer segment to a QuestionPaperItem."""
    review_service = OCRReviewService(db)
    return review_service.map_answer_to_question_item(
        answer_paper_id=paper_id,
        extracted_answer_id=req.extracted_answer_id,
        question_paper_item_id=req.question_paper_item_id,
        faculty_user_id=current_user.id
    )


@router.post("/{paper_id}/merge-answers", response_model=ExtractedAnswerResponse)
def merge_extracted_answer_segments(
    paper_id: str,
    req: AnswerMergeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_faculty)
):
    """Faculty merge multiple answer segments belonging to the same question."""
    review_service = OCRReviewService(db)
    return review_service.merge_answer_segments(
        answer_paper_id=paper_id,
        source_answer_ids=req.source_answer_ids,
        target_question_paper_item_id=req.target_question_paper_item_id,
        target_question_number=req.target_question_number,
        faculty_user_id=current_user.id
    )


@router.post("/{paper_id}/complete-review", response_model=AnswerPaperResponse)
def mark_ocr_review_complete(
    paper_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_faculty)
):
    """Faculty complete OCR review and mark status EVALUATION_PENDING."""
    review_service = OCRReviewService(db)
    return review_service.complete_ocr_review(answer_paper_id=paper_id, faculty_user_id=current_user.id)


@router.get("/{paper_id}/file")
def get_answer_paper_file(
    paper_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Serve uploaded answer paper binary file asset for viewing/PDF rendering."""
    paper = db.query(AnswerPaper).filter(AnswerPaper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Answer paper not found.")

    if user_is_student(current_user) and paper.student_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied.")

    if not paper.file_asset or not paper.file_asset.storage_path:
        raise HTTPException(status_code=404, detail="File asset not attached.")

    storage_service = LocalStorageService(base_dir="storage/uploads")
    abs_path = storage_service.base_dir / paper.file_asset.storage_path
    if not abs_path.exists():
        raise HTTPException(status_code=404, detail="File asset not found on storage.")

    return FileResponse(
        path=str(abs_path),
        media_type=paper.file_asset.mime_type,
        filename=paper.file_asset.original_filename
    )
