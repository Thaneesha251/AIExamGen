import pytest
from fastapi import status
from app.db.models import (
    Examination, Subject, User, QuestionPaper, QuestionPaperVersion,
    QuestionPaperItem, Question, AnswerKey, AnswerKeyItem, AnswerPaper, ExtractedAnswer
)
from app.db.guid import generate_uuid

def get_auth_token(client, email="faculty@example.com", password="faculty123"):
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return res.json()["data"]["access_token"] if res.status_code == 200 else None

def setup_evaluation_fixture(db):
    user = db.query(User).filter(User.email == "faculty@example.com").first()
    student = db.query(User).filter(User.email == "student1@example.com").first()
    subject = db.query(Subject).first()
    if not subject:
        subject = Subject(name="Database Systems", code="CS302", credits=4)
        db.add(subject)
        db.flush()

    question = Question(
        subject_id=subject.id,
        question_text="Explain B+ Tree indexing.",
        question_type="DESCRIPTIVE",
        difficulty="HARD",
        bloom_level="ANALYZE",
        marks=10.0,
        expected_answer="B+ Trees store all keys in leaves connected as linked list.",
        created_by=user.id if user else None
    )
    db.add(question)
    db.flush()

    qp = QuestionPaper(subject_id=subject.id, title="DB Midterm", paper_code=f"QP-DB-{generate_uuid()[:6]}", total_marks=10.0)
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

    ak = AnswerKey(question_paper_version_id=qp_ver.id, version_number=1, status="PUBLISHED")
    db.add(ak)
    db.flush()

    ak_item = AnswerKeyItem(
        answer_key_id=ak.id,
        question_paper_item_id=qp_item.id,
        model_answer="B+ trees connect leaf nodes into linked list.",
        maximum_marks=10.0
    )
    db.add(ak_item)
    db.flush()

    exam = Examination(
        name="DB Exam 2026",
        subject_id=subject.id,
        question_paper_id=qp.id,
        question_paper_version_id=qp_ver.id,
        total_marks=10.0,
        created_by=user.id if user else None
    )
    db.add(exam)
    db.flush()

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
        extracted_text="B+ Tree stores values at leaf nodes with sibling pointers.",
        ocr_confidence=0.95,
        segmentation_confidence=0.95
    )
    db.add(ext_ans)
    db.commit()
    db.refresh(paper)

    return paper

def test_override_valid_marks(client, db):
    token = get_auth_token(client)
    paper = setup_evaluation_fixture(db)

    eval_res = client.post(
        f"/api/v1/evaluations/answer-papers/{paper.id}/evaluate",
        headers={"Authorization": f"Bearer {token}"}
    )
    eval_data = eval_res.json()
    eval_id = eval_data["id"]
    item_id = eval_data["items"][0]["id"]

    override_res = client.post(
        f"/api/v1/evaluations/{eval_id}/items/{item_id}/override",
        json={
            "final_marks": 9.0,
            "reason": "Student provided valid alternative leaf node description.",
            "comment": "Full marks awarded for correct architectural concept"
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert override_res.status_code == status.HTTP_200_OK
    overridden = override_res.json()
    assert overridden["final_marks"] == 9.0
    assert overridden["review_status"] == "OVERRIDDEN"
    assert overridden["override_reason"] == "Student provided valid alternative leaf node description."


def test_override_invalid_marks_rejection(client, db):
    token = get_auth_token(client)
    paper = setup_evaluation_fixture(db)

    eval_res = client.post(
        f"/api/v1/evaluations/answer-papers/{paper.id}/evaluate",
        headers={"Authorization": f"Bearer {token}"}
    )
    eval_data = eval_res.json()
    eval_id = eval_data["id"]
    item_id = eval_data["items"][0]["id"]

    # Negative marks -> Rejected (400)
    res_neg = client.post(
        f"/api/v1/evaluations/{eval_id}/items/{item_id}/override",
        json={
            "final_marks": -2.0,
            "reason": "Negative marks test reason for validation.",
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res_neg.status_code == status.HTTP_400_BAD_REQUEST

    # Over maximum marks (10.0) -> Rejected (400)
    res_over = client.post(
        f"/api/v1/evaluations/{eval_id}/items/{item_id}/override",
        json={
            "final_marks": 15.0,
            "reason": "Marks exceed maximum limit allowed for item.",
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res_over.status_code == status.HTTP_400_BAD_REQUEST


def test_override_missing_reason_rejection(client, db):
    token = get_auth_token(client)
    paper = setup_evaluation_fixture(db)

    eval_res = client.post(
        f"/api/v1/evaluations/answer-papers/{paper.id}/evaluate",
        headers={"Authorization": f"Bearer {token}"}
    )
    eval_data = eval_res.json()
    eval_id = eval_data["id"]
    item_id = eval_data["items"][0]["id"]

    # Short/empty reason (<10 chars) -> Rejected (422 Pydantic or 400 Service validation)
    res_short = client.post(
        f"/api/v1/evaluations/{eval_id}/items/{item_id}/override",
        json={
            "final_marks": 8.0,
            "reason": "Short",
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res_short.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY]
