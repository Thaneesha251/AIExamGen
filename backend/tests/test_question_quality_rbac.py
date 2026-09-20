import pytest
from fastapi import status
from app.db.models import Examination, Subject, User
from app.db.guid import generate_uuid

def get_token_for(client, email, password):
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return res.json()["data"]["access_token"] if res.status_code == 200 else None

def test_student_blocked_from_quality_endpoints(client, db):
    student_token = get_token_for(client, "student1@example.com", "student123")
    assert student_token is not None
    headers = {"Authorization": f"Bearer {student_token}"}

    exam = db.query(Examination).first()
    exam_id = exam.id if exam else generate_uuid()
    subj = db.query(Subject).first()
    subj_id = subj.id if subj else generate_uuid()

    res_qual = client.get(f"/api/v1/analytics/exams/{exam_id}/quality", headers=headers)
    assert res_qual.status_code == status.HTTP_403_FORBIDDEN

    res_bp = client.get(f"/api/v1/analytics/exams/{exam_id}/blueprint", headers=headers)
    assert res_bp.status_code == status.HTTP_403_FORBIDDEN

    res_insights = client.get(f"/api/v1/analytics/question-bank/insights?subject_id={subj_id}", headers=headers)
    assert res_insights.status_code == status.HTTP_403_FORBIDDEN


def test_faculty_and_admin_allowed_access_to_quality(client, db):
    faculty_token = get_token_for(client, "faculty@example.com", "faculty123")
    admin_token = get_token_for(client, "admin@example.com", "admin123")

    exam = db.query(Examination).first()
    if not exam:
        subj = Subject(name="RBAC Quality Subj", code=f"SUBJ_Q_{generate_uuid()[:6]}")
        db.add(subj)
        db.flush()
        exam = Examination(name="Quality RBAC Exam", subject_id=subj.id)
        db.add(exam)
        db.commit()

    f_res = client.get(f"/api/v1/analytics/exams/{exam.id}/quality", headers={"Authorization": f"Bearer {faculty_token}"})
    assert f_res.status_code == 200

    a_res = client.get(f"/api/v1/analytics/exams/{exam.id}/quality", headers={"Authorization": f"Bearer {admin_token}"})
    assert a_res.status_code == 200
