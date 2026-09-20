import pytest
import io
from fastapi import status
try:
    from app.db.models import Examination, Subject, User
    from app.db.guid import generate_uuid
except ImportError:
    from backend.app.db.models import Examination, Subject, User
    from backend.app.db.guid import generate_uuid


def get_auth_token(client, email="student1@example.com", password="student123"):
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    if res.status_code == 200:
        return res.json()["data"]["access_token"]
    return None

def get_or_create_exam(db):
    exam = db.query(Examination).first()
    if not exam:
        subject = db.query(Subject).first()
        if not subject:
            subject = Subject(name="Computer Science", code="CS101", credits=4)
            db.add(subject)
            db.flush()
        user = db.query(User).filter(User.email == "admin@example.com").first()
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

def test_student_upload_valid_pdf(client, db):
    token = get_auth_token(client, "student1@example.com", "student123")
    assert token is not None
    exam = get_or_create_exam(db)

    pdf_content = b"%PDF-1.4 sample pdf answer paper content for student exam"
    files = {"file": ("answer_paper.pdf", io.BytesIO(pdf_content), "application/pdf")}
    
    response = client.post(
        f"/api/v1/answer-papers/examinations/{exam.id}",
        files=files,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["examination_id"] == exam.id
    assert "id" in data
    assert len(data["pages"]) > 0


def test_upload_invalid_extension(client, db):
    token = get_auth_token(client, "student1@example.com", "student123")
    exam = get_or_create_exam(db)

    txt_content = b"Some plain text answer"
    files = {"file": ("answer.txt", io.BytesIO(txt_content), "text/plain")}
    
    response = client.post(
        f"/api/v1/answer-papers/examinations/{exam.id}",
        files=files,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Unsupported file extension" in response.json()["detail"]


def test_upload_empty_file(client, db):
    token = get_auth_token(client, "student1@example.com", "student123")
    exam = get_or_create_exam(db)

    empty_content = b""
    files = {"file": ("empty.pdf", io.BytesIO(empty_content), "application/pdf")}
    
    response = client.post(
        f"/api/v1/answer-papers/examinations/{exam.id}",
        files=files,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "empty" in response.json()["detail"]
