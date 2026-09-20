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

def test_ai_question_generation_run(client: TestClient):
    token = get_faculty_token(client)
    subject_id = get_test_subject_id(client, token)

    req_payload = {
        "subject_id": subject_id,
        "question_type": "MCQ",
        "difficulty": "MEDIUM",
        "bloom_level": "APPLY",
        "marks": 2.0,
        "count": 3,
        "language": "English"
    }

    res = client.post("/api/v1/questions/generate", headers={"Authorization": f"Bearer {token}"}, json=req_payload)
    assert res.status_code == 200
    data = res.json()["data"]

    assert data["status"] == "COMPLETED"
    assert data["requested_count"] == 3
    assert data["generated_count"] == 3
    assert data["accepted_count"] >= 0
    assert len(data["questions"]) == 3

    # Verify AI generated questions are placed in UNDER_REVIEW status by default
    for q in data["questions"]:
        assert q["status"] == "UNDER_REVIEW"
        assert q["source"] == "AI_GENERATED"
        assert q["validation_data"] is not None
        assert "duplicate_score" in q["validation_data"]

def test_get_generation_run_detail(client: TestClient):
    token = get_faculty_token(client)
    subject_id = get_test_subject_id(client, token)

    gen_res = client.post("/api/v1/questions/generate", headers={"Authorization": f"Bearer {token}"}, json={
        "subject_id": subject_id,
        "question_type": "SHORT_ANSWER",
        "marks": 5.0,
        "count": 2
    })
    run_id = gen_res.json()["data"]["id"]

    run_res = client.get(f"/api/v1/questions/generation-runs/{run_id}", headers={"Authorization": f"Bearer {token}"})
    assert run_res.status_code == 200
    run_data = run_res.json()["data"]
    assert run_data["id"] == run_id
    assert run_data["status"] == "COMPLETED"
