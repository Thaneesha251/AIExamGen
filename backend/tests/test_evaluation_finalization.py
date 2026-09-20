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

def get_admin_token(client):
    res = client.post("/api/v1/auth/login", json={"email": "admin@example.com", "password": "adminpassword123"})
    return res.json()["data"]["access_token"] if res.status_code == 200 else None

def setup_evaluation_fixture(db):
    user = db.query(User).filter(User.email == "faculty@example.com").first()
    student = db.query(User).filter(User.email == "student1@example.com").first()
    subject = db.query(Subject).first()
    if not subject:
        subject = Subject(name="Computer Networks", code="CS303", credits=4)
        db.add(subject)
        db.flush()

    question = Question(
        subject_id=subject.id,
        question_text="Explain TCP 3-Way Handshake.",
        question_type="DESCRIPTIVE",
        difficulty="MEDIUM",
        bloom_level="UNDERSTAND",
        marks=10.0,
        expected_answer="SYN, SYN-ACK, ACK sequence establishes reliable connection.",
        created_by=user.id if user else None
    )
    db.add(question)
    db.flush()

    qp = QuestionPaper(subject_id=subject.id, title="CN Midterm", paper_code=f"QP-CN-{generate_uuid()[:6]}", total_marks=10.0)
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
        model_answer="TCP handshake uses SYN, SYN-ACK, ACK.",
        maximum_marks=10.0
    )
    db.add(ak_item)
    db.flush()

    exam = Examination(
        name="CN Exam 2026",
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
        extracted_text="TCP establishes connection using SYN, SYN-ACK and ACK packets.",
        ocr_confidence=0.95,
        segmentation_confidence=0.95
    )
    db.add(ext_ans)
    db.commit()
    db.refresh(paper)

    return paper

def test_incomplete_review_approval_rejection(client, db):
    token = get_auth_token(client)
    paper = setup_evaluation_fixture(db)

    eval_res = client.post(
        f"/api/v1/evaluations/answer-papers/{paper.id}/evaluate",
        headers={"Authorization": f"Bearer {token}"}
    )
    eval_id = eval_res.json()["id"]

    # Attempt approve when item review_status is PENDING -> 400 Bad Request
    app_res = client.post(
        f"/api/v1/evaluations/{eval_id}/approve",
        json={"notes": "Premature approval test"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert app_res.status_code == status.HTTP_400_BAD_REQUEST


def test_complete_approval_and_finalization_workflow(client, db):
    token = get_auth_token(client)
    paper = setup_evaluation_fixture(db)

    eval_res = client.post(
        f"/api/v1/evaluations/answer-papers/{paper.id}/evaluate",
        headers={"Authorization": f"Bearer {token}"}
    )
    eval_data = eval_res.json()
    eval_id = eval_data["id"]
    item_id = eval_data["items"][0]["id"]

    # 1. Accept Item
    client.post(
        f"/api/v1/evaluations/{eval_id}/items/{item_id}/accept",
        json={"comment": "Verified"},
        headers={"Authorization": f"Bearer {token}"}
    )

    # 2. Approve Evaluation
    app_res = client.post(
        f"/api/v1/evaluations/{eval_id}/approve",
        json={"notes": "All questions reviewed and approved."},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert app_res.status_code == status.HTTP_200_OK
    assert app_res.json()["status"] == "APPROVED"

    # 3. Finalize Evaluation
    fin_res = client.post(
        f"/api/v1/evaluations/{eval_id}/finalize",
        json={"notes": "Finalized by faculty"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert fin_res.status_code == status.HTTP_200_OK
    assert fin_res.json()["status"] == "FINALIZED"

    # 4. Attempt modification after finalization -> 400 Bad Request (Locked)
    mod_res = client.post(
        f"/api/v1/evaluations/{eval_id}/items/{item_id}/override",
        json={"final_marks": 5.0, "reason": "Attempting override on finalized paper."},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert mod_res.status_code == status.HTTP_400_BAD_REQUEST


def test_reopen_finalized_evaluation_admin_only(client, db):
    faculty_token = get_auth_token(client)
    admin_token = get_admin_token(client)
    paper = setup_evaluation_fixture(db)

    eval_res = client.post(
        f"/api/v1/evaluations/answer-papers/{paper.id}/evaluate",
        headers={"Authorization": f"Bearer {faculty_token}"}
    )
    eval_data = eval_res.json()
    eval_id = eval_data["id"]
    item_id = eval_data["items"][0]["id"]

    # Accept & Finalize
    client.post(
        f"/api/v1/evaluations/{eval_id}/items/{item_id}/accept",
        json={},
        headers={"Authorization": f"Bearer {faculty_token}"}
    )
    client.post(
        f"/api/v1/evaluations/{eval_id}/finalize",
        json={},
        headers={"Authorization": f"Bearer {faculty_token}"}
    )

    # Faculty attempts reopening -> Forbidden 403
    fac_reopen = client.post(
        f"/api/v1/evaluations/{eval_id}/reopen",
        json={"reason": "Faculty trying to reopen paper"},
        headers={"Authorization": f"Bearer {faculty_token}"}
    )
    assert fac_reopen.status_code == status.HTTP_403_FORBIDDEN

    # Admin reopens -> Allowed 200 OK
    if admin_token:
        adm_reopen = client.post(
            f"/api/v1/evaluations/{eval_id}/reopen",
            json={"reason": "Admin reopening for student score dispute investigation."},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert adm_reopen.status_code == status.HTTP_200_OK
        assert adm_reopen.json()["status"] == "REOPENED"
