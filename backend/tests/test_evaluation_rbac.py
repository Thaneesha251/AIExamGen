import pytest
from fastapi import status

def get_auth_token(client, email, password):
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return res.json()["data"]["access_token"] if res.status_code == 200 else None

def test_student_denied_evaluation_access(client):
    student_token = get_auth_token(client, "student1@example.com", "student123")
    assert student_token is not None

    # Student attempts to trigger evaluation on a paper -> Forbidden (403)
    res = client.post(
        "/api/v1/evaluations/answer-papers/00000000-0000-0000-0000-000000000001/evaluate",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    assert res.status_code == status.HTTP_403_FORBIDDEN


def test_faculty_evaluation_access_allowed(client):
    faculty_token = get_auth_token(client, "faculty@example.com", "faculty123")
    assert faculty_token is not None

    # Faculty requests non-existent evaluation -> 404 Not Found (not 403 Forbidden)
    res = client.get(
        "/api/v1/evaluations/00000000-0000-0000-0000-000000000000",
        headers={"Authorization": f"Bearer {faculty_token}"}
    )
    assert res.status_code == status.HTTP_404_NOT_FOUND
