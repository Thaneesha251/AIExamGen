from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

try:
    from app.db.models import AnswerPaper, ExtractedAnswer, QuestionPaperItem, AnswerPaperStatusEnum, ExtractionMethodEnum, AuditActionEnum
except ImportError:
    from backend.app.db.models import AnswerPaper, ExtractedAnswer, QuestionPaperItem, AnswerPaperStatusEnum, ExtractionMethodEnum, AuditActionEnum

try:
    from app.services.audit_service import AuditLogService
except ImportError:
    from backend.app.services.audit_service import AuditLogService


class OCRReviewService:
    """Service providing faculty review, manual text correction, question mapping, and segment merging capabilities."""

    def __init__(self, db: Session):
        self.db = db
        self.audit_service = AuditLogService(db)

    def update_extracted_answer_text(
        self,
        answer_paper_id: str,
        extracted_answer_id: str,
        new_text: str,
        faculty_user_id: str
    ) -> ExtractedAnswer:
        """Corrects OCR text for an extracted answer, marking extraction method as HYBRID."""
        answer = self.db.query(ExtractedAnswer).filter(
            ExtractedAnswer.id == extracted_answer_id,
            ExtractedAnswer.answer_paper_id == answer_paper_id
        ).first()

        if not answer:
            raise HTTPException(status_code=404, detail="Extracted answer record not found.")

        answer.extracted_text = new_text
        answer.extraction_method = ExtractionMethodEnum.HYBRID
        answer.manually_corrected = True
        answer.status = "CORRECTED"

        self.db.flush()

        self.audit_service.log_action(
            action=AuditActionEnum.FACULTY_OVERRIDE,
            user_id=faculty_user_id,
            entity_type="ExtractedAnswer",
            entity_id=answer.id,
            details={"field": "extracted_text", "new_text_len": len(new_text)}
        )

        self.db.commit()
        self.db.refresh(answer)
        return answer

    def map_answer_to_question_item(
        self,
        answer_paper_id: str,
        extracted_answer_id: str,
        question_paper_item_id: str,
        faculty_user_id: str
    ) -> ExtractedAnswer:
        """Assigns an unmapped or misclassified extracted answer to a QuestionPaperItem."""
        answer = self.db.query(ExtractedAnswer).filter(
            ExtractedAnswer.id == extracted_answer_id,
            ExtractedAnswer.answer_paper_id == answer_paper_id
        ).first()

        if not answer:
            raise HTTPException(status_code=404, detail="Extracted answer record not found.")

        # Verify target question paper item exists and belongs to the examination's paper version
        item = self.db.query(QuestionPaperItem).filter(
            QuestionPaperItem.id == question_paper_item_id
        ).first()
        if not item:
            raise HTTPException(status_code=404, detail="Target question paper item not found.")

        answer.question_paper_item_id = item.id
        if item.item_label:
            answer.question_number = item.item_label
        answer.segmentation_confidence = 1.0
        answer.extraction_method = ExtractionMethodEnum.HYBRID
        answer.manually_corrected = True

        self.db.flush()

        self.audit_service.log_action(
            action=AuditActionEnum.FACULTY_OVERRIDE,
            user_id=faculty_user_id,
            entity_type="ExtractedAnswer",
            entity_id=answer.id,
            details={"mapped_to_item_id": item.id, "question_number": answer.question_number}
        )

        self.db.commit()
        self.db.refresh(answer)
        return answer

    def merge_answer_segments(
        self,
        answer_paper_id: str,
        source_answer_ids: List[str],
        target_question_paper_item_id: Optional[str],
        target_question_number: str,
        faculty_user_id: str
    ) -> ExtractedAnswer:
        """Merges multiple extracted answer segments into a single unified ExtractedAnswer."""
        if len(source_answer_ids) < 2:
            raise HTTPException(status_code=400, detail="At least 2 answer segments are required for merging.")

        segments = self.db.query(ExtractedAnswer).filter(
            ExtractedAnswer.id.in_(source_answer_ids),
            ExtractedAnswer.answer_paper_id == answer_paper_id
        ).all()

        if len(segments) != len(source_answer_ids):
            raise HTTPException(status_code=404, detail="One or more source answer segments not found.")

        # Sort segments by page start or creation order
        segments.sort(key=lambda s: (s.page_start or 0, s.created_at or ""))

        combined_text = "\n\n".join([s.extracted_text for s in segments if s.extracted_text])
        min_page_start = min([s.page_start for s in segments if s.page_start is not None] or [1])
        max_page_end = max([s.page_end for s in segments if s.page_end is not None] or [1])
        avg_ocr_conf = sum([s.ocr_confidence or 0.85 for s in segments]) / len(segments)

        primary_segment = segments[0]
        primary_segment.question_number = target_question_number
        if target_question_paper_item_id:
            primary_segment.question_paper_item_id = target_question_paper_item_id
        primary_segment.extracted_text = combined_text
        primary_segment.page_start = min_page_start
        primary_segment.page_end = max_page_end
        primary_segment.ocr_confidence = round(avg_ocr_conf, 4)
        primary_segment.segmentation_confidence = 1.0
        primary_segment.extraction_method = ExtractionMethodEnum.HYBRID
        primary_segment.manually_corrected = True
        primary_segment.status = "MERGED"

        # Delete redundant merged secondary segments
        for sec in segments[1:]:
            self.db.delete(sec)

        self.db.flush()

        self.audit_service.log_action(
            action=AuditActionEnum.FACULTY_OVERRIDE,
            user_id=faculty_user_id,
            entity_type="AnswerPaper",
            entity_id=answer_paper_id,
            details={"action": "MERGE_SEGMENTS", "merged_count": len(segments), "result_id": primary_segment.id}
        )

        self.db.commit()
        self.db.refresh(primary_segment)
        return primary_segment

    def complete_ocr_review(self, answer_paper_id: str, faculty_user_id: str) -> AnswerPaper:
        """Marks OCR faculty review as complete, setting paper status to EVALUATION_PENDING."""
        paper = self.db.query(AnswerPaper).filter(AnswerPaper.id == answer_paper_id).first()
        if not paper:
            raise HTTPException(status_code=404, detail="Answer paper not found.")

        paper.status = AnswerPaperStatusEnum.EVALUATION_PENDING
        self.db.flush()

        self.audit_service.log_action(
            action=AuditActionEnum.FACULTY_OVERRIDE,
            user_id=faculty_user_id,
            entity_type="AnswerPaper",
            entity_id=paper.id,
            details={"status": "EVALUATION_PENDING", "review_complete": True}
        )

        self.db.commit()
        self.db.refresh(paper)
        return paper
