import pytest
from fastapi.testclient import TestClient

def get_token(client: TestClient, email: str, password: str) -> str:
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200
    return res.json()["data"]["access_token"]

def test_direct_api_rbac_enforcement(client: TestClient):
    admin_token = get_token(client, "admin@example.com", "admin123")
    faculty_token = get_token(client, "faculty@example.com", "faculty123")
    student_token = get_token(client, "student1@example.com", "student123")

    admin_endpoint = "/api/v1/users"

    # 1. ADMIN calling admin endpoint -> 200 OK
    res_admin = client.get(admin_endpoint, headers={"Authorization": f"Bearer {admin_token}"})
    assert res_admin.status_code == 200

    # 2. FACULTY calling admin endpoint -> 403 Forbidden
    res_faculty = client.get(admin_endpoint, headers={"Authorization": f"Bearer {faculty_token}"})
    assert res_faculty.status_code == 403
    assert "Operation not permitted" in res_faculty.json()["detail"]

    # 3. STUDENT calling admin endpoint -> 403 Forbidden
    res_student = client.get(admin_endpoint, headers={"Authorization": f"Bearer {student_token}"})
    assert res_student.status_code == 403
    assert "Operation not permitted" in res_student.json()["detail"]

def test_student_ownership_isolation(client: TestClient):
    # Get student1 token and info
    s1_token = get_token(client, "student1@example.com", "student123")
    s1_me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {s1_token}"}).json()["data"]
    s1_id = s1_me["id"]

    # Get student2 token and info
    s2_token = get_token(client, "student2@example.com", "student123")
    s2_me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {s2_token}"}).json()["data"]
    s2_id = s2_me["id"]

    faculty_token = get_token(client, "faculty@example.com", "faculty123")

    # 1. Student 1 accessing Student 1's results -> 200 OK
    res_own = client.get(f"/api/v1/users/students/{s1_id}/results", headers={"Authorization": f"Bearer {s1_token}"})
    assert res_own.status_code == 200
    assert res_own.json()["data"]["student_id"] == s1_id

    # 2. Student 1 attempting to access Student 2's results -> 403 Forbidden
    res_other = client.get(f"/api/v1/users/students/{s2_id}/results", headers={"Authorization": f"Bearer {s1_token}"})
    assert res_other.status_code == 403
    assert "Students can only access their own records" in res_other.json()["detail"]

    # 3. Faculty accessing Student 1's results -> 200 OK
    res_faculty = client.get(f"/api/v1/users/students/{s1_id}/results", headers={"Authorization": f"Bearer {faculty_token}"})
    assert res_faculty.status_code == 200
    assert res_faculty.json()["data"]["student_id"] == s1_id
