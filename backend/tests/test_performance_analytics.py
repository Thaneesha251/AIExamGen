import pytest
from fastapi import status
from app.db.models import (
    Examination, Subject, Unit, Topic, LearningOutcome, User, Question,
    QuestionPaper, QuestionPaperVersion, QuestionPaperItem,
    AnswerPaper, Evaluation, EvaluationItem, EvaluationStatusEnum
)
from app.db.guid import generate_uuid

def get_auth_token(client, email="faculty@example.com", password="faculty123"):
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return res.json()["data"]["access_token"] if res.status_code == 200 else None

def setup_analytics_fixture(db):
    user = db.query(User).filter(User.email == "faculty@example.com").first()
    student1 = db.query(User).filter(User.email == "student1@example.com").first()
    existing_subj = db.query(Subject).first()
    subject = Subject(
        name="Algorithms",
        code=f"CS_ALGO_{generate_uuid()[:6]}",
        credits=4,
        course_id=existing_subj.course_id if existing_subj else None,
        department_id=existing_subj.department_id if existing_subj else None,
        semester_id=existing_subj.semester_id if existing_subj else None,
        academic_year_id=existing_subj.academic_year_id if existing_subj else None
    )
    db.add(subject)
    db.flush()

    unit = Unit(subject_id=subject.id, unit_number=1, title="Graph Algorithms", description="DFS, BFS, Shortest path")
    db.add(unit)
    db.flush()

    topic = Topic(unit_id=unit.id, name="Dijkstra Algorithm", description="Single source shortest path")
    db.add(topic)
    db.flush()

    co = LearningOutcome(subject_id=subject.id, code="CO-01", description="Analyze shortest path algorithm complexities")
    db.add(co)
    db.flush()

    q1 = Question(
        subject_id=subject.id,
        unit_id=unit.id,
        topic_id=topic.id,
        learning_outcome_id=co.id,
        question_text="Explain Dijkstra's shortest path algorithm.",
        question_type="DESCRIPTIVE",
        difficulty="MEDIUM",
        bloom_level="ANALYZE",
        marks=10.0,
        created_by=user.id if user else None
    )
    db.add(q1)
    db.flush()

    exam = Examination(
        subject_id=subject.id,
        name=f"Algo Endterm {generate_uuid()[:4]}",
        total_marks=10.0,
        created_by=user.id if user else None
    )
    db.add(exam)
    db.flush()

    qp = QuestionPaper(subject_id=subject.id, title="Algo Paper", paper_code=f"QP_{generate_uuid()[:6]}", total_marks=10.0)
    db.add(qp)
    db.flush()

    qp_ver = QuestionPaperVersion(question_paper_id=qp.id, version_number=1)
    db.add(qp_ver)
    db.flush()

    qp_item = QuestionPaperItem(
        question_paper_version_id=qp_ver.id,
        question_id=q1.id,
        order_index=1,
        section="Section A",
        question_number="1",
        marks=10.0,
        question_text_snapshot=q1.question_text
    )
    db.add(qp_item)
    db.flush()

    # Finalized paper
    paper_fin = AnswerPaper(
        examination_id=exam.id,
        student_id=student1.id if student1 else generate_uuid(),
        status="FINALIZED"
    )
    # Draft paper (not finalized)
    paper_draft = AnswerPaper(
        examination_id=exam.id,
        student_id=user.id if user else generate_uuid(),
        status="PROCESSING",
        submission_number=2
    )

    db.add(paper_fin)
    db.add(paper_draft)
    db.flush()

    # Finalized evaluation
    eval_fin = Evaluation(
        examination_id=exam.id,
        answer_paper_id=paper_fin.id,
        student_id=paper_fin.student_id,
        status="FINALIZED",
        total_ai_marks=8.0,
        total_final_marks=8.5,
        finalized_at="2026-09-20T12:00:00Z"
    )
    # Draft evaluation (COMPLETED but NOT FINALIZED)
    eval_draft = Evaluation(
        examination_id=exam.id,
        answer_paper_id=paper_draft.id,
        student_id=paper_draft.student_id,
        status="COMPLETED",
        total_ai_marks=4.0,
        total_final_marks=4.0
    )

    db.add(eval_fin)
    db.add(eval_draft)
    db.flush()

    item_fin = EvaluationItem(
        evaluation_id=eval_fin.id,
        question_paper_item_id=qp_item.id,
        ai_marks=8.0,
        final_marks=8.5,
        maximum_marks=10.0,
        requires_faculty_review=False
    )
    item_draft = EvaluationItem(
        evaluation_id=eval_draft.id,
        question_paper_item_id=qp_item.id,
        ai_marks=4.0,
        final_marks=4.0,
        maximum_marks=10.0,
        requires_faculty_review=True
    )
    db.add(item_fin)
    db.add(item_draft)
    db.commit()

    return exam, paper_fin, eval_fin, q1, unit, topic, co


def test_performance_analytics_finalized_only_rule(client, db):
    exam, paper_fin, eval_fin, q1, unit, topic, co = setup_analytics_fixture(db)
    token = get_auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get(f"/api/v1/analytics/examinations/{exam.id}", headers=headers)
    assert res.status_code == 200
    data = res.json()

    # ONLY 1 finalized evaluation should be included (score 8.5/10 -> 85%)
    assert data["finalized_evaluations"] == 1
    assert data["average_marks"] == 8.5
    assert data["average_percentage"] == 85.0


def test_dimensional_analytics_breakdowns(client, db):
    exam, paper_fin, eval_fin, q1, unit, topic, co = setup_analytics_fixture(db)
    token = get_auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    # Questions breakdown
    q_res = client.get(f"/api/v1/analytics/examinations/{exam.id}/questions", headers=headers)
    assert q_res.status_code == 200
    q_data = q_res.json()
    assert len(q_data) >= 1
    assert q_data[0]["question_id"] == q1.id
    assert q_data[0]["average_marks"] == 8.5

    # Unit breakdown
    u_res = client.get(f"/api/v1/analytics/examinations/{exam.id}/units", headers=headers)
    assert u_res.status_code == 200
    assert len(u_res.json()) >= 1

    # Topic breakdown
    t_res = client.get(f"/api/v1/analytics/examinations/{exam.id}/topics", headers=headers)
    assert t_res.status_code == 200
    assert len(t_res.json()) >= 1

    # Learning Outcome breakdown
    co_res = client.get(f"/api/v1/analytics/examinations/{exam.id}/learning-outcomes", headers=headers)
    assert co_res.status_code == 200
    assert len(co_res.json()) >= 1
