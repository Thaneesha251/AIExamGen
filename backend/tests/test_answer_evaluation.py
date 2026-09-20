import pytest
import io
from fastapi import status
try:
    from app.db.models import (
        Examination, Subject, User, QuestionPaper, QuestionPaperVersion,
        QuestionPaperItem, Question, AnswerKey, AnswerKeyItem, AnswerPaper, ExtractedAnswer
    )
    from app.db.guid import generate_uuid
except ImportError:
    from backend.app.db.models import (
        Examination, Subject, User, QuestionPaper, QuestionPaperVersion,
        QuestionPaperItem, Question, AnswerKey, AnswerKeyItem, AnswerPaper, ExtractedAnswer
    )
    from backend.app.db.guid import generate_uuid

def get_auth_token(client, email="faculty@example.com", password="faculty123"):
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return res.json()["data"]["access_token"] if res.status_code == 200 else None

def setup_full_eval_fixtures(db):
    user = db.query(User).filter(User.email == "faculty@example.com").first()
    student = db.query(User).filter(User.email == "student1@example.com").first()
    subject = db.query(Subject).first()
    if not subject:
        subject = Subject(name="Data Structures", code="CS201", credits=4)
        db.add(subject)
        db.flush()

    # Question
    question = Question(
        subject_id=subject.id,
        question_text="Explain Binary Search algorithm and its time complexity.",
        question_type="DESCRIPTIVE",
        difficulty="MEDIUM",
        bloom_level="UNDERSTAND",
        marks=10.0,
        expected_answer="Binary search requires sorted array and repeatedly checks middle element.",
        keywords=["binary search", "sorted array", "middle element"],
        concepts=["search space reduction", "divide and conquer"],
        created_by=user.id if user else None
    )
    db.add(question)
    db.flush()

    # Question Paper Version & Item
    qp = QuestionPaper(subject_id=subject.id, title="Midterm Paper", paper_code=f"QP-EVAL-{generate_uuid()[:6]}", total_marks=10.0)
    db.add(qp)
    db.flush()

    qp_ver = QuestionPaperVersion(question_paper_id=qp.id, version_number=1)
    db.add(qp_ver)
    db.flush()

    qp_item = QuestionPaperItem(
        question_paper_version_id=qp_ver.id,
        question_id=question.id,
        order_index=1,
        section="Section A",
        question_number="1",
        marks=10.0,
        question_text_snapshot=question.question_text
    )
    db.add(qp_item)
    db.flush()

    # Answer Key & Item
    ak = AnswerKey(question_paper_version_id=qp_ver.id, version_number=1, status="PUBLISHED")
    db.add(ak)
    db.flush()

    ak_item = AnswerKeyItem(
        answer_key_id=ak.id,
        question_paper_item_id=qp_item.id,
        model_answer="Binary search requires a sorted array and compares middle elements. Time complexity is O(log n).",
        keywords=["binary search", "sorted array", "middle element", "log n"],
        concepts=["search space reduction", "logarithmic complexity"],
        maximum_marks=10.0
    )
    db.add(ak_item)
    db.flush()

    # Examination
    exam = Examination(
        name="Data Structures Midterm 2026",
        subject_id=subject.id,
        question_paper_id=qp.id,
        question_paper_version_id=qp_ver.id,
        total_marks=10.0,
        created_by=user.id if user else None
    )
    db.add(exam)
    db.flush()

    # AnswerPaper & ExtractedAnswer
    paper = AnswerPaper(
        examination_id=exam.id,
        student_id=student.id if student else generate_uuid(),
        status="EVALUATION_PENDING"
    )
    db.add(paper)
    db.flush()

    ext_ans = ExtractedAnswer(
        answer_paper_id=paper.id,
        question_paper_item_id=qp_item.id,
        question_number="1",
        extracted_text="Binary search operates on a sorted array by checking the middle element and halving the search space.",
        ocr_confidence=0.95,
        segmentation_confidence=0.95
    )
    db.add(ext_ans)
    db.commit()
    db.refresh(paper)

    return paper, exam

def test_answer_evaluation_pipeline(client, db):
    token = get_auth_token(client)
    paper, exam = setup_full_eval_fixtures(db)

    res = client.post(
        f"/api/v1/evaluations/answer-papers/{paper.id}/evaluate",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert res.status_code == status.HTTP_201_CREATED
    data = res.json()
    assert data["answer_paper_id"] == paper.id
    assert data["version"] == 1
    assert data["total_ai_marks"] > 0.0
    assert data["total_ai_marks"] <= 10.0
    assert len(data["items"]) == 1
    assert data["items"][0]["keyword_score"] > 0.0
    assert data["items"][0]["concept_score"] > 0.0
