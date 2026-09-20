import pytest
from fastapi import status
from app.db.models import (
    Examination, Subject, Unit, Topic, Question,
    QuestionPaper, QuestionPaperVersion, QuestionPaperItem,
    AnswerPaper, Evaluation, EvaluationItem, User
)
from app.db.guid import generate_uuid

def get_auth_token(client, email="faculty@example.com", password="faculty123"):
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return res.json()["data"]["access_token"] if res.status_code == 200 else None

def setup_weak_topic_fixture(db):
    user = db.query(User).filter(User.email == "faculty@example.com").first()
    student1 = db.query(User).filter(User.email == "student1@example.com").first()
    existing_subj = db.query(Subject).first()
    subject = Subject(
        name="Data Structures",
        code=f"CS_DS_{generate_uuid()[:6]}",
        credits=4,
        course_id=existing_subj.course_id if existing_subj else None,
        department_id=existing_subj.department_id if existing_subj else None,
        semester_id=existing_subj.semester_id if existing_subj else None,
        academic_year_id=existing_subj.academic_year_id if existing_subj else None
    )
    db.add(subject)
    db.flush()

    unit = Unit(subject_id=subject.id, unit_number=1, title="Hashing & Heaps", description="Hash tables and priority queues")
    db.add(unit)
    db.flush()

    weak_topic = Topic(unit_id=unit.id, name="Double Hashing", description="Collision resolution")
    db.add(weak_topic)
    db.flush()

    q_weak = Question(
        subject_id=subject.id,
        unit_id=unit.id,
        topic_id=weak_topic.id,
        question_text="Explain double hashing collision resolution.",
        question_type="DESCRIPTIVE",
        difficulty="HARD",
        bloom_level="APPLY",
        marks=10.0,
        created_by=user.id if user else None
    )
    db.add(q_weak)
    db.flush()

    exam = Examination(
        subject_id=subject.id,
        name=f"DS Midterm {generate_uuid()[:4]}",
        total_marks=10.0,
        created_by=user.id if user else None
    )
    db.add(exam)
    db.flush()

    qp = QuestionPaper(subject_id=subject.id, title="DS Paper", paper_code=f"QP_{generate_uuid()[:6]}", total_marks=10.0)
    db.add(qp)
    db.flush()

    qp_ver = QuestionPaperVersion(question_paper_id=qp.id, version_number=1)
    db.add(qp_ver)
    db.flush()

    qp_item = QuestionPaperItem(
        question_paper_version_id=qp_ver.id,
        question_id=q_weak.id,
        order_index=1,
        section="Section A",
        question_number="1",
        marks=10.0,
        question_text_snapshot=q_weak.question_text
    )
    db.add(qp_item)
    db.flush()

    # Create 3 student answer papers and finalized evaluations with low marks (3/10 -> 30%)
    for i in range(3):
        p = AnswerPaper(
            examination_id=exam.id,
            student_id=student1.id if (student1 and i == 0) else generate_uuid(),
            status="FINALIZED",
            submission_number=i + 1
        )
        db.add(p)
        db.flush()

        e = Evaluation(
            examination_id=exam.id,
            answer_paper_id=p.id,
            student_id=p.student_id,
            status="FINALIZED",
            total_ai_marks=3.0,
            total_final_marks=3.0,
            finalized_at="2026-09-20T12:00:00Z"
        )
        db.add(e)
        db.flush()

        item = EvaluationItem(
            evaluation_id=e.id,
            question_paper_item_id=qp_item.id,
            ai_marks=3.0,
            final_marks=3.0,
            maximum_marks=10.0,
            requires_faculty_review=False
        )
        db.add(item)

    db.commit()
    return exam, weak_topic, q_weak


def test_weak_topic_detection_threshold_logic(client, db):
    exam, weak_topic, q_weak = setup_weak_topic_fixture(db)
    token = get_auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get(
        f"/api/v1/analytics/examinations/{exam.id}/weak-topics?threshold=50.0&min_responses=2",
        headers=headers
    )
    assert res.status_code == 200
    data = res.json()

    assert data["weak_topics_count"] >= 1
    weak_t = data["weak_topics"][0]
    assert weak_t["topic_name"] == "Double Hashing"
    assert weak_t["percentage"] == 30.0
    assert weak_t["is_weak_topic"] is True
    assert len(weak_t["supporting_questions"]) >= 1
