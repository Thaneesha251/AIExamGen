import pytest
from fastapi.testclient import TestClient

def test_login_success(client: TestClient):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "admin123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "access_token" in data["data"]
    assert data["data"]["token_type"] == "bearer"
    assert data["data"]["user"]["email"] == "admin@example.com"
    assert data["data"]["user"]["role"] == "ADMIN"

def test_login_wrong_password(client: TestClient):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "wrongpassword"}
    )
    assert response.status_code == 401
    data = response.json()
    assert "Invalid email or password" in data["detail"]

def test_login_nonexistent_email(client: TestClient):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@example.com", "password": "somepassword"}
    )
    assert response.status_code == 401
    data = response.json()
    assert "Invalid email or password" in data["detail"]

def test_get_current_user_profile(client: TestClient):
    # 1. Login to get token
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "faculty@example.com", "password": "faculty123"}
    )
    token = login_res.json()["data"]["access_token"]

    # 2. Call /me with Bearer token
    me_res = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["success"] is True
    assert me_data["data"]["email"] == "faculty@example.com"
    assert me_data["data"]["role"]["name"] == "FACULTY"

def test_get_me_unauthenticated(client: TestClient):
    res = client.get("/api/v1/auth/me")
    assert res.status_code == 401

import uuid

def test_public_registration_forces_student(client: TestClient):
    unique_email = f"newstudent_{uuid.uuid4().hex[:6]}@example.com"
    reg_payload = {
        "email": unique_email,
        "password": "studentpassword123",
        "first_name": "New",
        "last_name": "Student",
        "registration_number": f"REG{uuid.uuid4().hex[:6]}",
        "role": "ADMIN" # Attempting to trick system into creating ADMIN
    }
    res = client.post("/api/v1/auth/register", json=reg_payload)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    # Verify created role is STUDENT despite sending ADMIN
    assert data["data"]["role"]["name"] == "STUDENT"

def test_public_registration_duplicate_email(client: TestClient):
    reg_payload = {
        "email": "admin@example.com", # already exists
        "password": "password123",
        "first_name": "Test",
        "last_name": "Dup"
    }
    res = client.post("/api/v1/auth/register", json=reg_payload)
    assert res.status_code == 400
    assert "already registered" in res.json()["detail"]

def test_change_password_flow(client: TestClient):
    unique_email = f"changepass_{uuid.uuid4().hex[:6]}@example.com"
    # 1. Register test user
    reg_res = client.post("/api/v1/auth/register", json={
        "email": unique_email,
        "password": "oldpassword123",
        "first_name": "Change",
        "last_name": "Pass"
    })
    assert reg_res.status_code == 200

    # 2. Login
    login_res = client.post("/api/v1/auth/login", json={
        "email": unique_email,
        "password": "oldpassword123"
    })
    token = login_res.json()["data"]["access_token"]

    # 3. Change password with wrong current password
    fail_res = client.post(
        "/api/v1/auth/change-password",
        headers={"Authorization": f"Bearer {token}"},
        json={"current_password": "wrongoldpassword", "new_password": "newpassword123"}
    )
    assert fail_res.status_code == 400

    # 4. Change password with correct current password
    succ_res = client.post(
        "/api/v1/auth/change-password",
        headers={"Authorization": f"Bearer {token}"},
        json={"current_password": "oldpassword123", "new_password": "newpassword123"}
    )
    assert succ_res.status_code == 200

    # 5. Verify old password fails and new password succeeds
    fail_login = client.post("/api/v1/auth/login", json={
        "email": unique_email,
        "password": "oldpassword123"
    })
    assert fail_login.status_code == 401

    succ_login = client.post("/api/v1/auth/login", json={
        "email": unique_email,
        "password": "newpassword123"
    })
    assert succ_login.status_code == 200
