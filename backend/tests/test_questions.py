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

def test_manual_question_creation_and_versioning(client: TestClient):
    token = get_faculty_token(client)
    subject_id = get_test_subject_id(client, token)

    # 1. Create a manual question
    create_payload = {
        "subject_id": subject_id,
        "question_text": "What is the computational complexity of quicksort in average case?",
        "question_type": "SHORT_ANSWER",
        "marks": 5.0,
        "difficulty": "MEDIUM",
        "bloom_level": "UNDERSTAND",
        "expected_answer": "O(N log N)",
        "keywords": ["quicksort", "complexity", "big-o"]
    }
    res = client.post("/api/v1/questions", headers={"Authorization": f"Bearer {token}"}, json=create_payload)
    assert res.status_code == 200
    q_data = res.json()["data"]
    q_id = q_data["id"]

    assert q_data["version"] == 1
    assert len(q_data["versions"]) == 1
    assert q_data["versions"][0]["version_number"] == 1

    # 2. Update question text (triggers version bump to v2)
    update_payload = {
        "question_text": "What is the average and worst-case time complexity of quicksort algorithm?",
        "marks": 10.0,
        "change_reason": "Expanded scope to include worst-case complexity"
    }
    up_res = client.put(f"/api/v1/questions/{q_id}", headers={"Authorization": f"Bearer {token}"}, json=update_payload)
    assert up_res.status_code == 200
    up_data = up_res.json()["data"]

    assert up_data["version"] == 2
    assert len(up_data["versions"]) == 2
    assert up_data["marks"] == 10.0

def test_mcq_question_validation_rules(client: TestClient):
    token = get_faculty_token(client)
    subject_id = get_test_subject_id(client, token)

    # Missing options should fail with 400
    invalid_mcq = {
        "subject_id": subject_id,
        "question_text": "Which data structure operates in FIFO order?",
        "question_type": "MCQ",
        "marks": 2.0
    }
    res = client.post("/api/v1/questions", headers={"Authorization": f"Bearer {token}"}, json=invalid_mcq)
    assert res.status_code == 400

    # Valid MCQ
    valid_mcq = {
        "subject_id": subject_id,
        "question_text": "Which data structure operates in FIFO order?",
        "question_type": "MCQ",
        "marks": 2.0,
        "options": {
            "options": ["A) Queue", "B) Stack", "C) Tree", "D) Graph"],
            "correct_option": "A) Queue",
            "explanation": "Queue is First-In-First-Out."
        }
    }
    res2 = client.post("/api/v1/questions", headers={"Authorization": f"Bearer {token}"}, json=valid_mcq)
    assert res2.status_code == 200
    assert res2.json()["data"]["question_type"] == "MCQ"

def test_question_status_workflow(client: TestClient):
    token = get_faculty_token(client)
    subject_id = get_test_subject_id(client, token)

    # Create question
    res = client.post("/api/v1/questions", headers={"Authorization": f"Bearer {token}"}, json={
        "subject_id": subject_id,
        "question_text": "Define a linked list data structure.",
        "question_type": "SHORT_ANSWER",
        "marks": 3.0
    })
    q_id = res.json()["data"]["id"]

    # Status transition to APPROVED
    patch_res = client.patch(
        f"/api/v1/questions/{q_id}/status",
        headers={"Authorization": f"Bearer {token}"},
        json={"status": "APPROVED", "reason": "Verified accuracy"}
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["data"]["status"] == "APPROVED"

def test_search_and_filter_questions(client: TestClient):
    token = get_faculty_token(client)
    subject_id = get_test_subject_id(client, token)

    res = client.get(f"/api/v1/questions?subject_id={subject_id}&question_type=MCQ", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()["data"]
    assert "items" in data
    assert "total" in data

def test_csv_import_questions(client: TestClient):
    token = get_faculty_token(client)
    subject_id = get_test_subject_id(client, token)

    csv_content = (
        "question_text,question_type,difficulty,bloom_level,marks,expected_answer,option_a,option_b,option_c,option_d,correct_option\n"
        "What is 2+2?,MCQ,EASY,REMEMBER,2.0,4,A) 3,B) 4,C) 5,D) 6,B) 4\n"
        "Define polymorphism in OOP.,SHORT_ANSWER,MEDIUM,UNDERSTAND,5.0,Ability of objects to take multiple forms,,,,,\n"
    )

    files = {"file": ("test_questions.csv", csv_content.encode("utf-8"), "text/csv")}
    res = client.post(f"/api/v1/subjects/{subject_id}/questions/import-csv", headers={"Authorization": f"Bearer {token}"}, files=files)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["created_count"] == 2
    assert data["failed_count"] == 0
