import pytest
from fastapi.testclient import TestClient

def get_admin_token(client: TestClient) -> str:
    res = client.post("/api/v1/auth/login", json={"email": "admin@example.com", "password": "admin123"})
    return res.json()["data"]["access_token"]

def test_admin_list_users(client: TestClient):
    token = get_admin_token(client)
    res = client.get("/api/v1/users", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["total"] >= 1
    assert len(data["items"]) >= 1

def test_admin_search_and_filter_users(client: TestClient):
    token = get_admin_token(client)
    
    # Filter by FACULTY role
    res = client.get("/api/v1/users?role=FACULTY", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()["data"]
    for item in data["items"]:
        assert item["role"]["name"] == "FACULTY"

    # Search by keyword
    search_res = client.get("/api/v1/users?search=Turing", headers={"Authorization": f"Bearer {token}"})
    assert search_res.status_code == 200
    assert search_res.json()["data"]["total"] >= 1

import uuid

def test_admin_create_and_deactivate_user(client: TestClient):
    token = get_admin_token(client)
    unique_email = f"newfaculty_{uuid.uuid4().hex[:6]}@example.com"
    unique_emp_id = f"FAC-{uuid.uuid4().hex[:6]}"

    # 1. Admin creates a new faculty member
    create_payload = {
        "email": unique_email,
        "password": "facultypassword123",
        "first_name": "Ada",
        "last_name": "Lovelace",
        "employee_id": unique_emp_id,
        "role": "FACULTY",
        "is_active": True
    }
    create_res = client.post("/api/v1/users", headers={"Authorization": f"Bearer {token}"}, json=create_payload)
    assert create_res.status_code == 200
    user_id = create_res.json()["data"]["id"]

    # 2. Deactivate user
    deact_res = client.delete(f"/api/v1/users/{user_id}", headers={"Authorization": f"Bearer {token}"})
    assert deact_res.status_code == 200

    # 3. Verify deactivated user cannot log in
    login_res = client.post("/api/v1/auth/login", json={"email": unique_email, "password": "facultypassword123"})
    assert login_res.status_code == 401
    assert "inactive" in login_res.json()["detail"].lower()

    # 4. Reactivate user
    react_res = client.patch(
        f"/api/v1/users/{user_id}/status",
        headers={"Authorization": f"Bearer {token}"},
        json={"is_active": True}
    )
    assert react_res.status_code == 200
    assert react_res.json()["data"]["is_active"] is True

    # 5. Verify user can now log in
    succ_login = client.post("/api/v1/auth/login", json={"email": unique_email, "password": "facultypassword123"})
    assert succ_login.status_code == 200

def test_admin_change_user_role(client: TestClient):
    token = get_admin_token(client)
    unique_email = f"promote_{uuid.uuid4().hex[:6]}@example.com"

    # Register student
    reg_res = client.post("/api/v1/auth/register", json={
        "email": unique_email,
        "password": "password123",
        "first_name": "Promote",
        "last_name": "User"
    })
    assert reg_res.status_code == 200
    user_id = reg_res.json()["data"]["id"]

    # Change role to FACULTY
    role_res = client.patch(
        f"/api/v1/users/{user_id}/role",
        headers={"Authorization": f"Bearer {token}"},
        json={"role": "FACULTY"}
    )
    assert role_res.status_code == 200
    assert role_res.json()["data"]["role"]["name"] == "FACULTY"
