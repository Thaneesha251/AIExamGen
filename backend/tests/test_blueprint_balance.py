import pytest
from fastapi import status
from app.db.models import (
    Examination, Subject, Unit, User, Question,
    QuestionPaper, QuestionPaperVersion, QuestionPaperItem, Blueprint, BlueprintRule,
    QuestionTypeEnum, DifficultyLevelEnum, BloomLevelEnum
)
from app.db.guid import generate_uuid

def get_auth_token(client, email="faculty@example.com", password="faculty123"):
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return res.json()["data"]["access_token"] if res.status_code == 200 else None

def setup_blueprint_fixture(db):
    user = db.query(User).filter(User.email == "faculty@example.com").first()
    existing_subj = db.query(Subject).first()
    subject = Subject(
        name="Software Engineering",
        code=f"CS_SE_{generate_uuid()[:6]}",
        credits=4,
        course_id=existing_subj.course_id if existing_subj else None,
        department_id=existing_subj.department_id if existing_subj else None,
        semester_id=existing_subj.semester_id if existing_subj else None,
        academic_year_id=existing_subj.academic_year_id if existing_subj else None
    )
    db.add(subject)
    db.flush()

    u1 = Unit(subject_id=subject.id, unit_number=1, title="Agile Requirements", description="Scrum & User stories")
    u2 = Unit(subject_id=subject.id, unit_number=2, title="System Architecture", description="Microservices & Monolith")
    db.add(u1)
    db.add(u2)
    db.flush()

    bp = Blueprint(
        subject_id=subject.id,
        name="SE Exam Blueprint",
        total_marks=100.0,
        status="ACTIVE"
    )
    db.add(bp)
    db.flush()

    # Rule 1: Unit 1 target = 50 marks (50%)
    # Rule 2: Unit 2 target = 50 marks (50%)
    r1 = BlueprintRule(blueprint_id=bp.id, section="Section A", unit_id=u1.id, question_count=5, marks_per_question=10.0, total_marks=50.0)
    r2 = BlueprintRule(blueprint_id=bp.id, section="Section B", unit_id=u2.id, question_count=5, marks_per_question=10.0, total_marks=50.0)
    db.add(r1)
    db.add(r2)
    db.flush()

    qp = QuestionPaper(
        subject_id=subject.id,
        blueprint_id=bp.id,
        title="SE Final Paper",
        paper_code=f"QP_{generate_uuid()[:6]}",
        total_marks=100.0
    )
    db.add(qp)
    db.flush()

    qp_ver = QuestionPaperVersion(question_paper_id=qp.id, version_number=1)
    db.add(qp_ver)
    db.flush()

    # Create 5 questions in Unit 1 (50 marks) and 5 questions in Unit 2 (50 marks) -> Perfectly balanced 50% vs 50%
    for i in range(5):
        q = Question(
            subject_id=subject.id,
            unit_id=u1.id,
            question_text=f"SE Unit 1 Q{i+1}",
            question_type=QuestionTypeEnum.DESCRIPTIVE,
            difficulty=DifficultyLevelEnum.MEDIUM,
            bloom_level=BloomLevelEnum.UNDERSTAND,
            marks=10.0
        )
        db.add(q)
        db.flush()
        qp_item = QuestionPaperItem(question_paper_version_id=qp_ver.id, question_id=q.id, order_index=i+1, section="Section A", question_number=f"1.{i+1}", marks=10.0, question_text_snapshot=q.question_text)
        db.add(qp_item)

    for i in range(5):
        q = Question(
            subject_id=subject.id,
            unit_id=u2.id,
            question_text=f"SE Unit 2 Q{i+1}",
            question_type=QuestionTypeEnum.DESCRIPTIVE,
            difficulty=DifficultyLevelEnum.MEDIUM,
            bloom_level=BloomLevelEnum.UNDERSTAND,
            marks=10.0
        )
        db.add(q)
        db.flush()
        qp_item = QuestionPaperItem(question_paper_version_id=qp_ver.id, question_id=q.id, order_index=i+6, section="Section B", question_number=f"2.{i+1}", marks=10.0, question_text_snapshot=q.question_text)
        db.add(qp_item)

    exam = Examination(
        subject_id=subject.id,
        question_paper_id=qp.id,
        question_paper_version_id=qp_ver.id,
        name="SE Endterm Exam",
        total_marks=100.0
    )
    db.add(exam)
    db.commit()

    return exam, bp


def test_blueprint_balance_analysis(client, db):
    exam, bp = setup_blueprint_fixture(db)
    token = get_auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get(f"/api/v1/analytics/exams/{exam.id}/blueprint", headers=headers)
    assert res.status_code == 200
    data = res.json()

    assert data["examination_id"] == exam.id
    assert data["blueprint_id"] == bp.id
    assert data["overall_status"] == "BALANCED"
    assert data["max_variance"] == 0.0
    assert len(data["breakdown"]) >= 2
