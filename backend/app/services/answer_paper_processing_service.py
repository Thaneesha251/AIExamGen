import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException

try:
    from app.db.models import AnswerPaper, AnswerPage, AnswerPaperStatusEnum, AuditActionEnum
except ImportError:
    from backend.app.db.models import AnswerPaper, AnswerPage, AnswerPaperStatusEnum, AuditActionEnum

from backend.app.services.answer_paper_storage_service import AnswerPaperStorageService
from backend.app.services.answer_segmentation_service import AnswerSegmentationService
from backend.app.services.storage.local_storage import LocalStorageService
from ai.services.ocr.ocr_service import OCRService
try:
    from app.services.audit_service import AuditLogService
except ImportError:
    from backend.app.services.audit_service import AuditLogService


class AnswerPaperProcessingService:
    """Orchestrates end-to-end processing pipeline for student answer papers."""

    def __init__(
        self,
        db: Session,
        ocr_service: Optional[OCRService] = None,
        storage_service: Optional[LocalStorageService] = None
    ):
        self.db = db
        self.ocr_service = ocr_service or OCRService()
        self.storage_service = storage_service or LocalStorageService(base_dir="storage/uploads")
        self.segmentation_service = AnswerSegmentationService(db)
        self.audit_service = AuditLogService(db)

    async def process_answer_paper(self, answer_paper_id: str, current_user_id: Optional[str] = None) -> AnswerPaper:
        """Executes full OCR, page extraction, and question segmentation pipeline."""
        answer_paper = self.db.query(AnswerPaper).filter(AnswerPaper.id == answer_paper_id).first()
        if not answer_paper:
            raise HTTPException(status_code=404, detail="Answer paper not found.")

        # Update status to PROCESSING
        answer_paper.status = AnswerPaperStatusEnum.PROCESSING
        self.db.commit()
        self.db.refresh(answer_paper)

        self.audit_service.log_action(
            action=AuditActionEnum.RUN_OCR,
            user_id=current_user_id or answer_paper.student_id,
            entity_type="AnswerPaper",
            entity_id=answer_paper.id,
            details={"status": "PROCESSING", "submission_number": answer_paper.submission_number}
        )

        try:
            # 1. OCR Page-by-Page
            for page in answer_paper.pages:
                await self.process_single_page_ocr(page, answer_paper)

            # 2. Answer Segmentation
            self.segmentation_service.segment_answers(answer_paper)

            # 3. Transition to EVALUATION_PENDING upon completion
            answer_paper.status = AnswerPaperStatusEnum.EVALUATION_PENDING
            answer_paper.processed_at = datetime.now(timezone.utc).isoformat()
            self.db.commit()
            self.db.refresh(answer_paper)

            self.audit_service.log_action(
                action=AuditActionEnum.RUN_OCR,
                user_id=current_user_id or answer_paper.student_id,
                entity_type="AnswerPaper",
                entity_id=answer_paper.id,
                details={"status": "EVALUATION_PENDING", "pages_processed": len(answer_paper.pages)}
            )
            return answer_paper

        except Exception as e:
            self.db.rollback()
            answer_paper = self.db.query(AnswerPaper).filter(AnswerPaper.id == answer_paper_id).first()
            if answer_paper:
                answer_paper.status = AnswerPaperStatusEnum.ERROR
                self.db.commit()
            raise HTTPException(
                status_code=500,
                detail=f"Answer paper processing failed: {str(e)}"
            )

    async def process_single_page_ocr(self, page: AnswerPage, answer_paper: AnswerPaper) -> AnswerPage:
        """Runs OCR on a single page asset."""
        start_time = time.time()
        try:
            # Determine path to image file
            if answer_paper.file_asset and answer_paper.file_asset.storage_path:
                file_path = str(self.storage_service.base_dir / answer_paper.file_asset.storage_path)
            else:
                file_path = "sample_page.png"

            ocr_result = await self.ocr_service.process_answer_sheet(file_path)

            page.ocr_text = ocr_result.get("text", "")
            page.ocr_confidence = ocr_result.get("confidence", 0.90)
            page.ocr_provider = ocr_result.get("provider", "MockOCR")
            page.processing_time = round(time.time() - start_time, 4)
            page.processing_status = "COMPLETED"
            page.error_message = None
            self.db.flush()
            return page
        except Exception as ex:
            page.processing_status = "ERROR"
            page.error_message = str(ex)
            page.processing_time = round(time.time() - start_time, 4)
            self.db.flush()
            return page

    def get_processing_status(self, answer_paper_id: str) -> Dict[str, Any]:
        """Calculates live progress and status summary for an answer paper."""
        answer_paper = self.db.query(AnswerPaper).filter(AnswerPaper.id == answer_paper_id).first()
        if not answer_paper:
            raise HTTPException(status_code=404, detail="Answer paper not found.")

        total_pages = len(answer_paper.pages)
        processed_pages = sum(1 for p in answer_paper.pages if p.processing_status == "COMPLETED")
        failed_pages = sum(1 for p in answer_paper.pages if p.processing_status == "ERROR")
        segmented_answers = len(answer_paper.extracted_answers)

        progress_percent = int((processed_pages / total_pages * 100)) if total_pages > 0 else 0

        return {
            "answer_paper_id": answer_paper.id,
            "status": answer_paper.status.value if hasattr(answer_paper.status, 'value') else str(answer_paper.status),
            "total_pages": total_pages,
            "processed_pages": processed_pages,
            "ocr_completed_pages": processed_pages,
            "segmented_answers": segmented_answers,
            "failed_pages": failed_pages,
            "progress_percent": progress_percent,
            "uploaded_at": answer_paper.uploaded_at,
            "processed_at": answer_paper.processed_at
        }
