import pytest
from fastapi import status
from app.db.models import (
    Examination, Subject, User, Question, QuestionPaper, QuestionPaperVersion,
    QuestionPaperItem, AnswerPaper, ExtractedAnswer, AnswerSimilarity, PlagiarismResult
)
from app.db.guid import generate_uuid
from backend.app.services.similarity_analysis_service import SimilarityAnalysisService

def get_auth_token(client, email="faculty@example.com", password="faculty123"):
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return res.json()["data"]["access_token"] if res.status_code == 200 else None

def setup_similarity_fixture(db):
    user = db.query(User).filter(User.email == "faculty@example.com").first()
    student1 = db.query(User).filter(User.email == "student1@example.com").first()

    # Create subject
    subject = db.query(Subject).first()
    if not subject:
        subject = Subject(name="Database Systems", code=f"CS_{generate_uuid()[:6]}", credits=4)
        db.add(subject)
        db.flush()

    # Create descriptive question
    question = Question(
        subject_id=subject.id,
        question_text="Explain B-Tree indexing and its advantages in relational databases.",
        question_type="DESCRIPTIVE",
        difficulty="MEDIUM",
        bloom_level="UNDERSTAND",
        marks=10.0,
        expected_answer="B-Tree indexes maintain sorted data and allow searches, sequential access, insertions, and deletions in logarithmic time.",
        created_by=user.id if user else None
    )
    db.add(question)
    db.flush()

    # Create exam
    exam = Examination(
        subject_id=subject.id,
        name=f"DBMS Final Exam {generate_uuid()[:4]}",
        total_marks=10.0,
        created_by=user.id if user else None
    )

    db.add(exam)
    db.flush()

    # Create two student answer papers with highly similar text
    paper1 = AnswerPaper(
        examination_id=exam.id,
        student_id=student1.id if student1 else generate_uuid(),
        status="FINALIZED"
    )
    paper2 = AnswerPaper(
        examination_id=exam.id,
        student_id=user.id if user else generate_uuid(),
        status="FINALIZED"
    )

    db.add(paper1)
    db.add(paper2)
    db.flush()

    qp = QuestionPaper(subject_id=subject.id, title="DBMS Paper", paper_code=f"QP_{generate_uuid()[:6]}", total_marks=10.0)
    db.add(qp)
    db.flush()

    qp_ver = QuestionPaperVersion(question_paper_id=qp.id, version_number=1)
    db.add(qp_ver)
    db.flush()

    qp_item = QuestionPaperItem(
        question_paper_version_id=qp_ver.id,
        question_id=question.id,
        order_index=1,
        section="Section A",
        question_number="1",
        marks=10.0,
        question_text_snapshot=question.question_text
    )
    db.add(qp_item)
    db.flush()

    # Highly similar answer text between student 1 and student 2
    similar_text = "B-Tree indexing maintains self-balancing search trees to optimize database queries, disk block reads, logarithmic search performance, and range queries."
    ans1 = ExtractedAnswer(
        answer_paper_id=paper1.id,
        question_paper_item_id=qp_item.id,
        question_number="1",
        extracted_text=similar_text,
        ocr_confidence=0.95
    )
    ans2 = ExtractedAnswer(
        answer_paper_id=paper2.id,
        question_paper_item_id=qp_item.id,
        question_number="1",
        extracted_text=similar_text,
        ocr_confidence=0.92
    )
    db.add(ans1)
    db.add(ans2)
    db.commit()


    return exam, paper1, paper2, question, ans1, ans2


def test_similarity_analysis_service_execution(db):
    exam, paper1, paper2, question, ans1, ans2 = setup_similarity_fixture(db)
    service = SimilarityAnalysisService(db)

    result = service.analyze_examination_similarity(
        examination_id=exam.id,
        lexical_weight=0.5,
        semantic_weight=0.5,
        flag_threshold=0.70
    )

    assert result["examination_id"] == exam.id
    assert result["total_papers"] == 2
    assert result["analyzed_pairs"] >= 1
    assert result["flagged_cases"] >= 1

    # Check persisted similarity record
    sim = db.query(AnswerSimilarity).filter(AnswerSimilarity.examination_id == exam.id).first()
    assert sim is not None
    assert sim.similarity_score > 0.8
    assert sim.flagged_for_review is True

    # Check aggregated plagiarism result
    pr1 = db.query(PlagiarismResult).filter(PlagiarismResult.answer_paper_id == paper1.id).first()
    assert pr1 is not None
    assert pr1.status == "FLAGGED"


def test_similarity_analysis_api_endpoint(client, db):
    exam, paper1, paper2, question, ans1, ans2 = setup_similarity_fixture(db)
    token = get_auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    res = client.post(
        f"/api/v1/plagiarism/examinations/{exam.id}/analyze",
        json={"lexical_weight": 0.5, "semantic_weight": 0.5, "flag_threshold": 0.70},
        headers=headers
    )
    assert res.status_code == 200
    data = res.json()
    assert data["examination_id"] == exam.id

    # Test summary API
    summary_res = client.get(f"/api/v1/plagiarism/examinations/{exam.id}/summary", headers=headers)
    assert summary_res.status_code == 200
    summary_data = summary_res.json()
    assert summary_data["total_answer_papers"] == 2
    assert summary_data["flagged_cases_count"] >= 1
