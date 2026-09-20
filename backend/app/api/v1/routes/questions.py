from typing import Optional, List
from fastapi import APIRouter, Depends, UploadFile, File, Query, HTTPException, status
from sqlalchemy.orm import Session

try:
    from app.api.deps import get_db, get_current_user, require_admin_or_faculty
    from app.services.question_service import QuestionService
    from app.services.question_generation_service import QuestionGenerationService
    from app.db.models import User, QuestionStatusEnum, QuestionTypeEnum, DifficultyLevelEnum, BloomLevelEnum
    from app.schemas.question import (
        QuestionCreate,
        QuestionUpdate,
        QuestionStatusUpdate,
        QuestionResponse,
        QuestionListResponse,
    )
    from app.schemas.question_generation import (
        QuestionGenerationRequest,
        QuestionGenerationRunResponse,
    )
except ImportError:
    from backend.app.api.deps import get_db, get_current_user, require_admin_or_faculty
    from backend.app.services.question_service import QuestionService
    from backend.app.services.question_generation_service import QuestionGenerationService
    from backend.app.db.models import User, QuestionStatusEnum, QuestionTypeEnum, DifficultyLevelEnum, BloomLevelEnum
    from backend.app.schemas.question import (
        QuestionCreate,
        QuestionUpdate,
        QuestionStatusUpdate,
        QuestionResponse,
        QuestionListResponse,
    )
    from backend.app.schemas.question_generation import (
        QuestionGenerationRequest,
        QuestionGenerationRunResponse,
    )

router = APIRouter(tags=["Question Bank & AI Generation"])


@router.post("/questions", response_model=None)
def create_question(
    req: QuestionCreate,
    user: User = Depends(require_admin_or_faculty),
    db: Session = Depends(get_db)
):
    service = QuestionService(db)
    q = service.create_question(req, user)
    return {"success": True, "data": QuestionResponse.model_validate(q)}


@router.get("/questions", response_model=None)
def search_questions(
    subject_id: Optional[str] = Query(None),
    unit_id: Optional[str] = Query(None),
    topic_id: Optional[str] = Query(None),
    learning_outcome_id: Optional[str] = Query(None),
    question_type: Optional[QuestionTypeEnum] = Query(None),
    difficulty: Optional[DifficultyLevelEnum] = Query(None),
    bloom_level: Optional[BloomLevelEnum] = Query(None),
    status: Optional[QuestionStatusEnum] = Query(None),
    source: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = QuestionService(db)
    skip = (page - 1) * page_size
    items, total = service.search_questions(
        user=user,
        subject_id=subject_id,
        unit_id=unit_id,
        topic_id=topic_id,
        learning_outcome_id=learning_outcome_id,
        question_type=question_type,
        difficulty=difficulty,
        bloom_level=bloom_level,
        status=status,
        source=source,
        search_query=search,
        skip=skip,
        limit=page_size
    )
    return {
        "success": True,
        "data": {
            "total": total,
            "items": [QuestionResponse.model_validate(q) for q in items],
            "page": page,
            "page_size": page_size
        }
    }


@router.get("/questions/{question_id}", response_model=None)
def get_question_detail(
    question_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = QuestionService(db)
    q = service.get_question(question_id, user)
    return {"success": True, "data": QuestionResponse.model_validate(q)}


@router.put("/questions/{question_id}", response_model=None)
def update_question(
    question_id: str,
    req: QuestionUpdate,
    user: User = Depends(require_admin_or_faculty),
    db: Session = Depends(get_db)
):
    service = QuestionService(db)
    q = service.update_question(question_id, req, user)
    return {"success": True, "data": QuestionResponse.model_validate(q)}


@router.patch("/questions/{question_id}/status", response_model=None)
def update_question_status(
    question_id: str,
    status_update: QuestionStatusUpdate,
    user: User = Depends(require_admin_or_faculty),
    db: Session = Depends(get_db)
):
    service = QuestionService(db)
    q = service.update_status(question_id, status_update, user)
    return {"success": True, "data": QuestionResponse.model_validate(q)}


@router.post("/questions/generate", response_model=None)
async def generate_questions(
    req: QuestionGenerationRequest,
    user: User = Depends(require_admin_or_faculty),
    db: Session = Depends(get_db)
):
    service = QuestionGenerationService(db)
    run = await service.run_generation(req, user)
    return {"success": True, "data": QuestionGenerationRunResponse.model_validate(run)}


@router.get("/questions/generation-runs/{run_id}", response_model=None)
def get_generation_run(
    run_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = QuestionGenerationService(db)
    run = service.get_generation_run(run_id, user)
    return {"success": True, "data": QuestionGenerationRunResponse.model_validate(run)}


@router.post("/subjects/{subject_id}/questions/import-csv", response_model=None)
async def import_csv_questions(
    subject_id: str,
    file: UploadFile = File(...),
    user: User = Depends(require_admin_or_faculty),
    db: Session = Depends(get_db)
):
    service = QuestionService(db)
    file_bytes = await file.read()
    result = service.import_csv_questions(subject_id, file_bytes, user)
    return {"success": True, "data": result}
