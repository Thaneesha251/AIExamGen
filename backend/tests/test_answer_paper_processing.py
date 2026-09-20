import pytest
import io
from fastapi import status
try:
    from app.db.models import AnswerPaper, AnswerPaperStatusEnum, Examination, Subject, User
except ImportError:
    from backend.app.db.models import AnswerPaper, AnswerPaperStatusEnum, Examination, Subject, User

def get_auth_token(client, email="student1@example.com", password="student123"):
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return res.json()["data"]["access_token"] if res.status_code == 200 else None

def get_faculty_token(client):
    res = client.post("/api/v1/auth/login", json={"email": "faculty@example.com", "password": "faculty123"})
    return res.json()["data"]["access_token"] if res.status_code == 200 else None

def get_or_create_exam(db):
    exam = db.query(Examination).first()
    if not exam:
        subject = db.query(Subject).first()
        if not subject:
            subject = Subject(name="Computer Science", code="CS101", credits=4)
            db.add(subject)
            db.flush()
        user = db.query(User).filter(User.email == "faculty@example.com").first()
        exam = Examination(
            name="Midterm Exam 2026",
            subject_id=subject.id,
            duration_minutes=120,
            total_marks=100.0,
            created_by=user.id if user else None
        )
        db.add(exam)
        db.commit()
        db.refresh(exam)
    return exam

def test_process_pipeline_and_status(client, db):
    student_token = get_auth_token(client, "student1@example.com", "student123")
    faculty_token = get_faculty_token(client)
    
    exam = get_or_create_exam(db)

    # Upload PDF paper
    pdf_content = b"%PDF-1.4 1. Define Stack\nA stack is LIFO.\n2. Define Queue\nA queue is FIFO."
    files = {"file": ("test_paper.pdf", io.BytesIO(pdf_content), "application/pdf")}
    
    upload_res = client.post(
        f"/api/v1/answer-papers/examinations/{exam.id}",
        files=files,
        headers={"Authorization": f"Bearer {student_token}"}
    )
    assert upload_res.status_code == status.HTTP_201_CREATED
    paper_id = upload_res.json()["id"]

    # Trigger process / retry endpoint
    proc_res = client.post(
        f"/api/v1/answer-papers/{paper_id}/process",
        headers={"Authorization": f"Bearer {faculty_token}"}
    )
    assert proc_res.status_code == 200
    paper_data = proc_res.json()
    assert paper_data["status"] == AnswerPaperStatusEnum.EVALUATION_PENDING.value
    assert len(paper_data["extracted_answers"]) > 0

    # Query status endpoint
    status_res = client.get(
        f"/api/v1/answer-papers/{paper_id}/status",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert status_data["answer_paper_id"] == paper_id
    assert status_data["progress_percent"] == 100
    assert status_data["segmented_answers"] > 0
