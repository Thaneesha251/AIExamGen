import pytest
from fastapi.testclient import TestClient

def get_faculty_token(client: TestClient) -> str:
    res = client.post("/api/v1/auth/login", json={"email": "faculty@example.com", "password": "faculty123"})
    return res.json()["data"]["access_token"]

def get_test_subject_id(client: TestClient, token: str) -> str:
    res = client.get("/api/v1/academic/subjects", headers={"Authorization": f"Bearer {token}"})
    items = res.json()["data"]
    assert len(items) > 0
    return items[0]["id"]

def test_question_bank_lifecycle(client: TestClient):
    token = get_faculty_token(client)
    subject_id = get_test_subject_id(client, token)

    # 1. Create Question Bank
    create_bank_payload = {
        "subject_id": subject_id,
        "name": "Midterm Exam Preparation Bank",
        "description": "Selected question pool for mid-semester assessment"
    }
    res = client.post("/api/v1/question-banks", headers={"Authorization": f"Bearer {token}"}, json=create_bank_payload)
    assert res.status_code == 200
    bank_data = res.json()["data"]
    bank_id = bank_data["id"]
    assert bank_data["name"] == "Midterm Exam Preparation Bank"

    # 2. Create a question to add to bank
    q_res = client.post("/api/v1/questions", headers={"Authorization": f"Bearer {token}"}, json={
        "subject_id": subject_id,
        "question_text": "What is memory fragmentation in operating systems?",
        "question_type": "SHORT_ANSWER",
        "marks": 5.0
    })
    q_id = q_res.json()["data"]["id"]

    # 3. Add question to bank
    add_res = client.post(f"/api/v1/question-banks/{bank_id}/questions", headers={"Authorization": f"Bearer {token}"}, json={
        "question_ids": [q_id]
    })
    assert add_res.status_code == 200
    updated_bank = add_res.json()["data"]
    assert len(updated_bank["items"]) >= 1
    assert updated_bank["items"][0]["question_id"] == q_id

    # 4. List banks by subject
    list_res = client.get(f"/api/v1/question-banks/subject/{subject_id}", headers={"Authorization": f"Bearer {token}"})
    assert list_res.status_code == 200
    assert len(list_res.json()["data"]) >= 1

    # 5. Remove question from bank
    rem_res = client.delete(f"/api/v1/question-banks/{bank_id}/questions/{q_id}", headers={"Authorization": f"Bearer {token}"})
    assert rem_res.status_code == 200
    bank_after_remove = rem_res.json()["data"]
    assert len(bank_after_remove["items"]) == 0

    # 6. Delete bank
    del_res = client.delete(f"/api/v1/question-banks/{bank_id}", headers={"Authorization": f"Bearer {token}"})
    assert del_res.status_code == 200
