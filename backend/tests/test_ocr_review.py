import pytest
try:
    from app.db.models import AnswerPaper, ExtractedAnswer, ExtractionMethodEnum, AnswerPaperStatusEnum
    from app.db.guid import generate_uuid
except ImportError:
    from backend.app.db.models import AnswerPaper, ExtractedAnswer, ExtractionMethodEnum, AnswerPaperStatusEnum
    from backend.app.db.guid import generate_uuid

from backend.app.services.ocr_review_service import OCRReviewService

def test_ocr_review_text_correction(db):
    paper = AnswerPaper(
        examination_id=generate_uuid(),
        student_id=generate_uuid(),
        status="OCR_COMPLETED"
    )
    db.add(paper)
    db.flush()

    ans = ExtractedAnswer(
        answer_paper_id=paper.id,
        question_number="1",
        extracted_text="Original OCR misread text",
        extraction_method=ExtractionMethodEnum.OCR,
        manually_corrected=False
    )
    db.add(ans)
    db.flush()

    review_service = OCRReviewService(db)
    updated = review_service.update_extracted_answer_text(
        answer_paper_id=paper.id,
        extracted_answer_id=ans.id,
        new_text="Corrected student answer text for Q1",
        faculty_user_id=generate_uuid()
    )

    assert updated.extracted_text == "Corrected student answer text for Q1"
    assert updated.extraction_method == ExtractionMethodEnum.HYBRID
    assert updated.manually_corrected is True


def test_ocr_review_segment_merging(db):
    paper = AnswerPaper(
        examination_id=generate_uuid(),
        student_id=generate_uuid(),
        status="OCR_COMPLETED"
    )
    db.add(paper)
    db.flush()

    seg1 = ExtractedAnswer(
        answer_paper_id=paper.id,
        question_number="2",
        extracted_text="Part 1 of Q2 answer on Page 1",
        page_start=1,
        page_end=1,
        extraction_method=ExtractionMethodEnum.OCR
    )
    seg2 = ExtractedAnswer(
        answer_paper_id=paper.id,
        question_number="2",
        extracted_text="Part 2 of Q2 answer on Page 2",
        page_start=2,
        page_end=2,
        extraction_method=ExtractionMethodEnum.OCR
    )
    db.add_all([seg1, seg2])
    db.flush()

    review_service = OCRReviewService(db)
    merged = review_service.merge_answer_segments(
        answer_paper_id=paper.id,
        source_answer_ids=[seg1.id, seg2.id],
        target_question_paper_item_id=None,
        target_question_number="2",
        faculty_user_id=generate_uuid()
    )

    assert "Part 1" in merged.extracted_text
    assert "Part 2" in merged.extracted_text
    assert merged.page_start == 1
    assert merged.page_end == 2
    assert merged.extraction_method == ExtractionMethodEnum.HYBRID

    # Verify second segment was deleted
    remaining = db.query(ExtractedAnswer).filter(ExtractedAnswer.answer_paper_id == paper.id).all()
    assert len(remaining) == 1
