import pytest
from fastapi import status
try:
    from app.db.models import AnswerPaper, Examination, Subject, User
except ImportError:
    from backend.app.db.models import AnswerPaper, Examination, Subject, User

def get_auth_token(client, email, password):
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return res.json()["data"]["access_token"] if res.status_code == 200 else None

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

def test_student_rbac_isolation(client, db):
    student1_token = get_auth_token(client, "student1@example.com", "student123")
    student2_token = get_auth_token(client, "student2@example.com", "student123")
    
    exam = get_or_create_exam(db)
    st1 = db.query(User).filter(User.email == "student1@example.com").first()
    assert st1 is not None

    paper = db.query(AnswerPaper).filter(AnswerPaper.examination_id == exam.id, AnswerPaper.student_id == st1.id).first()
    if not paper:
        paper = AnswerPaper(examination_id=exam.id, student_id=st1.id, status="EVALUATION_PENDING")
        db.add(paper)
        db.commit()
        db.refresh(paper)

    # Student 2 tries to access Student 1's paper detail -> Forbidden (403)
    res = client.get(f"/api/v1/answer-papers/{paper.id}", headers={"Authorization": f"Bearer {student2_token}"})
    assert res.status_code == status.HTTP_403_FORBIDDEN

    # Student 1 accesses own paper detail -> OK (200)
    res_ok = client.get(f"/api/v1/answer-papers/{paper.id}", headers={"Authorization": f"Bearer {student1_token}"})
    assert res_ok.status_code == status.HTTP_200_OK

    # Student tries to call faculty review route -> Forbidden (403)
    review_res = client.post(
        f"/api/v1/answer-papers/{paper.id}/complete-review",
        headers={"Authorization": f"Bearer {student1_token}"}
    )
    assert review_res.status_code == status.HTTP_403_FORBIDDEN
