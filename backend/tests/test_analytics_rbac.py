import pytest
from fastapi import status
from app.db.models import Examination, Subject, User
from app.db.guid import generate_uuid

def get_token_for(client, email, password):
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return res.json()["data"]["access_token"] if res.status_code == 200 else None

def test_student_blocked_from_plagiarism_and_analytics_endpoints(client, db):
    # Get student token
    student_token = get_token_for(client, "student1@example.com", "student123")
    assert student_token is not None
    headers = {"Authorization": f"Bearer {student_token}"}

    exam = db.query(Examination).first()
    exam_id = exam.id if exam else generate_uuid()

    # Attempt plagiarism endpoints as student
    res_plag = client.get(f"/api/v1/plagiarism/examinations/{exam_id}/summary", headers=headers)
    assert res_plag.status_code == status.HTTP_403_FORBIDDEN

    res_analyze = client.post(f"/api/v1/plagiarism/examinations/{exam_id}/analyze", json={}, headers=headers)
    assert res_analyze.status_code == status.HTTP_403_FORBIDDEN

    # Attempt analytics endpoints as student
    res_analytics = client.get(f"/api/v1/analytics/examinations/{exam_id}", headers=headers)
    assert res_analytics.status_code == status.HTTP_403_FORBIDDEN

    res_weak = client.get(f"/api/v1/analytics/examinations/{exam_id}/weak-topics", headers=headers)
    assert res_weak.status_code == status.HTTP_403_FORBIDDEN


def test_faculty_and_admin_allowed_access(client, db):
    faculty = db.query(User).filter(User.email == "faculty@example.com").first()
    faculty_token = get_token_for(client, "faculty@example.com", "faculty123")
    admin_token = get_token_for(client, "admin@example.com", "admin123")

    subject = db.query(Subject).first()
    if not subject:
        subject = Subject(name="RBAC Subject", code=f"SUBJ_RBAC_{generate_uuid()[:6]}", credits=4)
        db.add(subject)
        db.flush()

    exam = Examination(name="Test Exam RBAC", subject_id=subject.id, created_by=faculty.id if faculty else None)
    db.add(exam)
    db.commit()


    # Faculty access
    f_res = client.get(f"/api/v1/analytics/examinations/{exam.id}", headers={"Authorization": f"Bearer {faculty_token}"})
    assert f_res.status_code == 200

    # Admin access
    a_res = client.get(f"/api/v1/analytics/examinations/{exam.id}", headers={"Authorization": f"Bearer {admin_token}"})
    assert a_res.status_code == 200

