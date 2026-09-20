import pytest
from fastapi import status
from app.db.models import (
    Examination, Subject, User, QuestionPaper, QuestionPaperVersion,
    QuestionPaperItem, Question, AnswerKey, AnswerKeyItem, AnswerPaper, ExtractedAnswer, Evaluation, EvaluationItem
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
        subject = Subject(name="Operating Systems", code="CS301", credits=4)
        db.add(subject)
        db.flush()

    question = Question(
        subject_id=subject.id,
        question_text="Explain Process Scheduling in OS.",
        question_type="DESCRIPTIVE",
        difficulty="MEDIUM",
        bloom_level="UNDERSTAND",
        marks=10.0,
        expected_answer="Process scheduling manages process states and CPU execution time.",
        created_by=user.id if user else None
    )
    db.add(question)
    db.flush()

    qp = QuestionPaper(subject_id=subject.id, title="OS Midterm", paper_code=f"QP-OS-{generate_uuid()[:6]}", total_marks=10.0)
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
        model_answer="Process scheduling manages process states.",
        maximum_marks=10.0
    )
    db.add(ak_item)
    db.flush()

    exam = Examination(
        name="OS Exam 2026",
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
        extracted_text="Process scheduling handles process states in CPU queue.",
        ocr_confidence=0.95,
        segmentation_confidence=0.95
    )
    db.add(ext_ans)
    db.commit()
    db.refresh(paper)

    return paper, qp_item

def test_accept_ai_mark(client, db):
    token = get_auth_token(client)
    paper, qp_item = setup_evaluation_fixture(db)

    # 1. Trigger evaluation
    eval_res = client.post(
        f"/api/v1/evaluations/answer-papers/{paper.id}/evaluate",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert eval_res.status_code == status.HTTP_201_CREATED
    eval_data = eval_res.json()
    eval_id = eval_data["id"]
    item_id = eval_data["items"][0]["id"]

    # 2. Accept AI Mark
    accept_res = client.post(
        f"/api/v1/evaluations/{eval_id}/items/{item_id}/accept",
        json={"comment": "AI mark looks accurate"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert accept_res.status_code == status.HTTP_200_OK
    accepted_data = accept_res.json()
    assert accepted_data["review_status"] == "ACCEPTED"
    assert accepted_data["final_marks"] == accepted_data["ai_marks"]
    assert accepted_data["faculty_comment"] == "AI mark looks accurate"


def test_bulk_accept_high_confidence(client, db):
    token = get_auth_token(client)
    paper, qp_item = setup_evaluation_fixture(db)

    eval_res = client.post(
        f"/api/v1/evaluations/answer-papers/{paper.id}/evaluate",
        headers={"Authorization": f"Bearer {token}"}
    )
    eval_data = eval_res.json()
    eval_id = eval_data["id"]

    bulk_res = client.post(
        f"/api/v1/evaluations/{eval_id}/bulk-accept",
        json={"confidence_threshold": 0.50},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert bulk_res.status_code == status.HTTP_200_OK
    bulk_data = bulk_res.json()
    assert bulk_data["accepted_count"] >= 0
