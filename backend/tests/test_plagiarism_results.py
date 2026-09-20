import pytest
from fastapi import status
from app.db.models import Examination, Subject, User, Question, AnswerPaper, ExtractedAnswer, PlagiarismResult
from app.db.guid import generate_uuid
from backend.app.services.similarity_analysis_service import SimilarityAnalysisService

def get_auth_token(client, email="faculty@example.com", password="faculty123"):
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return res.json()["data"]["access_token"] if res.status_code == 200 else None

def setup_plagiarism_review_fixture(db):
    user = db.query(User).filter(User.email == "faculty@example.com").first()
    subject = db.query(Subject).first()
    if not subject:
        subject = Subject(name="Operating Systems", code=f"OS_{generate_uuid()[:6]}", credits=4)
        db.add(subject)
        db.flush()

    exam = Examination(
        subject_id=subject.id,
        name=f"OS Midterm {generate_uuid()[:4]}",
        total_marks=10.0,
        created_by=user.id if user else None
    )

    db.add(exam)
    db.flush()

    paper = AnswerPaper(
        examination_id=exam.id,
        student_id=user.id if user else generate_uuid(),
        status="FINALIZED"
    )

    db.add(paper)
    db.flush()

    pr = PlagiarismResult(
        examination_id=exam.id,
        answer_paper_id=paper.id,
        similarity_score=0.88,
        lexical_score=0.85,
        semantic_score=0.91,
        combined_score=0.88,
        threshold_used=0.70,
        status="FLAGGED"
    )
    db.add(pr)
    db.commit()

    return exam, paper, pr

def test_faculty_review_plagiarism_case(client, db):
    exam, paper, pr = setup_plagiarism_review_fixture(db)
    token = get_auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    # Review case as REVIEWED
    res = client.post(
        f"/api/v1/plagiarism/results/{pr.id}/review",
        json={"status": "REVIEWED", "review_notes": "Reviewed by faculty; similarities due to standard textbook formula definition."},
        headers=headers
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "REVIEWED"
    assert "textbook formula" in data["review_notes"]

    # Dismiss case
    res_dismiss = client.post(
        f"/api/v1/plagiarism/results/{pr.id}/review",
        json={"status": "DISMISSED", "review_notes": "Dismissed after manual verification."},
        headers=headers
    )
    assert res_dismiss.status_code == 200
    assert res_dismiss.json()["status"] == "DISMISSED"
