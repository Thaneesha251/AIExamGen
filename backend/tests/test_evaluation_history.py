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

def get_student_token(client):
    res = client.post("/api/v1/auth/login", json={"email": "student1@example.com", "password": "student123"})
    return res.json()["data"]["access_token"] if res.status_code == 200 else None

def setup_evaluation_fixture(db):
    user = db.query(User).filter(User.email == "faculty@example.com").first()
    student = db.query(User).filter(User.email == "student1@example.com").first()
    subject = db.query(Subject).first()
    if not subject:
        subject = Subject(name="Software Engineering", code="CS304", credits=4)
        db.add(subject)
        db.flush()

    question = Question(
        subject_id=subject.id,
        question_text="Explain Agile Methodology Principles.",
        question_type="DESCRIPTIVE",
        difficulty="EASY",
        bloom_level="REMEMBER",
        marks=10.0,
        expected_answer="Iterative development, continuous customer feedback, working software.",
        created_by=user.id if user else None
    )
    db.add(question)
    db.flush()

    qp = QuestionPaper(subject_id=subject.id, title="SE Midterm", paper_code=f"QP-SE-{generate_uuid()[:6]}", total_marks=10.0)
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
        model_answer="Agile principles emphasize iterative delivery and customer collaboration.",
        maximum_marks=10.0
    )
    db.add(ak_item)
    db.flush()

    exam = Examination(
        name="SE Exam 2026",
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
        extracted_text="Agile delivers working software in short iterations.",
        ocr_confidence=0.95,
        segmentation_confidence=0.95
    )
    db.add(ext_ans)
    db.commit()
    db.refresh(paper)

    return paper

def test_faculty_review_audit_history(client, db):
    token = get_auth_token(client)
    paper = setup_evaluation_fixture(db)

    eval_res = client.post(
        f"/api/v1/evaluations/answer-papers/{paper.id}/evaluate",
        headers={"Authorization": f"Bearer {token}"}
    )
    eval_data = eval_res.json()
    eval_id = eval_data["id"]
    item_id = eval_data["items"][0]["id"]

    # 1. Perform Accept
    client.post(
        f"/api/v1/evaluations/{eval_id}/items/{item_id}/accept",
        json={"comment": "First review step"},
        headers={"Authorization": f"Bearer {token}"}
    )

    # 2. Perform Override
    client.post(
        f"/api/v1/evaluations/{eval_id}/items/{item_id}/override",
        json={"final_marks": 9.5, "reason": "Awarding bonus for exceptional explanation.", "comment": "Updated"},
        headers={"Authorization": f"Bearer {token}"}
    )

    # 3. Fetch Reviews History
    rev_res = client.get(
        f"/api/v1/evaluations/{eval_id}/reviews",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert rev_res.status_code == status.HTTP_200_OK
    reviews = rev_res.json()
    assert len(reviews) == 2
    assert reviews[0]["action"] == "ACCEPT_AI_MARK"
    assert reviews[1]["action"] == "OVERRIDE_MARK"
    assert reviews[1]["revised_marks"] == 9.5


def test_student_denied_access_to_faculty_review_endpoints(client, db):
    faculty_token = get_auth_token(client)
    student_token = get_student_token(client)
    paper = setup_evaluation_fixture(db)

    eval_res = client.post(
        f"/api/v1/evaluations/answer-papers/{paper.id}/evaluate",
        headers={"Authorization": f"Bearer {faculty_token}"}
    )
    eval_id = eval_res.json()["id"]

    # Student attempts review history fetch -> Forbidden (403)
    res_reviews = client.get(
        f"/api/v1/evaluations/{eval_id}/reviews",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    assert res_reviews.status_code == status.HTTP_403_FORBIDDEN

    # Student attempts finalize -> Forbidden (403)
    res_fin = client.post(
        f"/api/v1/evaluations/{eval_id}/finalize",
        json={},
        headers={"Authorization": f"Bearer {student_token}"}
    )
    assert res_fin.status_code == status.HTTP_403_FORBIDDEN
