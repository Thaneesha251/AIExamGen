import pytest
try:
    from app.db.models import AnswerPaper, AnswerPage, ExtractedAnswer
    from app.db.guid import generate_uuid
except ImportError:
    from backend.app.db.models import AnswerPaper, AnswerPage, ExtractedAnswer
    from backend.app.db.guid import generate_uuid

from backend.app.services.answer_segmentation_service import AnswerSegmentationService

def test_question_segmentation_parsing(db):
    # Create sample AnswerPaper with 3 pages
    paper = AnswerPaper(
        examination_id=generate_uuid(),
        student_id=generate_uuid(),
        submission_number=1,
        status="PROCESSING"
    )
    db.add(paper)
    db.flush()

    # Page 1: Q1 and Q2
    page1 = AnswerPage(
        answer_paper_id=paper.id,
        page_number=1,
        ocr_text="1. Define Stack.\nA stack is a linear LIFO structure.\n\n2. Explain Queue.\nA queue follows FIFO order.",
        ocr_confidence=0.95
    )
    # Page 2: Continuation of Q2 and Q3
    page2 = AnswerPage(
        answer_paper_id=paper.id,
        page_number=2,
        ocr_text="Queues are used in OS scheduling.\n\n3. What is Binary Tree?\nA tree with max two children.",
        ocr_confidence=0.90
    )
    # Page 3: Q4
    page3 = AnswerPage(
        answer_paper_id=paper.id,
        page_number=3,
        ocr_text="Question 4: Define Hash Table.\nHash tables use key-value mapping.",
        ocr_confidence=0.88
    )
    db.add_all([page1, page2, page3])
    db.flush()

    segmenter = AnswerSegmentationService(db)
    extracted = segmenter.segment_answers(paper)

    assert len(extracted) >= 3
    q_nums = [e.question_number for e in extracted]
    assert "1" in q_nums or "1." in q_nums
    assert "2" in q_nums or "2." in q_nums

    # Check multi-page answer for Q2
    q2_ans = next(e for e in extracted if e.question_number in ["2", "2."])
    assert "FIFO" in q2_ans.extracted_text
    assert q2_ans.page_start == 1
    assert q2_ans.page_end == 2
