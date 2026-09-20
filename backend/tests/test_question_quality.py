import pytest
from fastapi import status
from app.db.models import (
    Examination, Subject, Unit, Topic, LearningOutcome, User, Question,
    QuestionPaper, QuestionPaperVersion, QuestionPaperItem,
    AnswerPaper, Evaluation, EvaluationItem, EvaluationStatusEnum, QuestionQualityReview
)
from app.db.guid import generate_uuid

def get_auth_token(client, email="faculty@example.com", password="faculty123"):
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return res.json()["data"]["access_token"] if res.status_code == 200 else None

def setup_quality_fixture(db):
    user = db.query(User).filter(User.email == "faculty@example.com").first()
    existing_subj = db.query(Subject).first()
    subject = Subject(
        name="Operating Systems",
        code=f"CS_OS_{generate_uuid()[:6]}",
        credits=4,
        course_id=existing_subj.course_id if existing_subj else None,
        department_id=existing_subj.department_id if existing_subj else None,
        semester_id=existing_subj.semester_id if existing_subj else None,
        academic_year_id=existing_subj.academic_year_id if existing_subj else None
    )
    db.add(subject)
    db.flush()

    unit = Unit(subject_id=subject.id, unit_number=1, title="Process Management", description="CPU Scheduling & Threads")
    db.add(unit)
    db.flush()

    topic = Topic(unit_id=unit.id, name="Round Robin Scheduling", description="Time quantum scheduling")
    db.add(topic)
    db.flush()

    q1 = Question(
        subject_id=subject.id,
        unit_id=unit.id,
        topic_id=topic.id,
        question_text="Explain Round Robin CPU scheduling algorithm.",
        question_type="DESCRIPTIVE",
        difficulty="MEDIUM",
        bloom_level="UNDERSTAND",
        marks=10.0,
        created_by=user.id if user else None
    )
    db.add(q1)
    db.flush()

    exam = Examination(
        subject_id=subject.id,
        name=f"OS Midterm {generate_uuid()[:4]}",
        total_marks=10.0,
        created_by=user.id if user else None
    )
    db.add(exam)
    db.flush()

    qp = QuestionPaper(subject_id=subject.id, title="OS Paper", paper_code=f"QP_{generate_uuid()[:6]}", total_marks=10.0)
    db.add(qp)
    db.flush()

    qp_ver = QuestionPaperVersion(question_paper_id=qp.id, version_number=1)
    db.add(qp_ver)
    db.flush()

    exam.question_paper_id = qp.id
    exam.question_paper_version_id = qp_ver.id
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

    # Create 5 student answer papers and finalized evaluations with varying marks
    # Scores: 10, 9, 7, 4, 1 -> Top group (10, 9) avg 9.5; Bottom group (4, 1) avg 2.5; Discrimination = 0.70
    marks_list = [10.0, 9.0, 7.0, 4.0, 1.0]
    for i, m in enumerate(marks_list):
        p = AnswerPaper(
            examination_id=exam.id,
            student_id=generate_uuid(),
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
            total_ai_marks=m,
            total_final_marks=m,
            finalized_at="2026-09-20T12:00:00Z"
        )
        db.add(e)
        db.flush()

        item = EvaluationItem(
            evaluation_id=e.id,
            question_paper_item_id=qp_item.id,
            ai_marks=m,
            final_marks=m,
            maximum_marks=10.0,
            requires_faculty_review=False
        )
        db.add(item)

    db.commit()
    return exam, q1, qp_item, subject


def test_question_quality_dashboard_endpoint(client, db):
    exam, q1, qp_item, subject = setup_quality_fixture(db)
    token = get_auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get(f"/api/v1/analytics/exams/{exam.id}/quality", headers=headers)
    assert res.status_code == 200
    data = res.json()

    assert data["examination_id"] == exam.id
    assert data["finalized_responses"] == 5
    assert data["total_questions"] >= 1
    assert data["average_exam_score"] == 6.2 # (10+9+7+4+1)/5 = 6.2
    assert len(data["questions"]) >= 1


def test_question_discrimination_calculation(client, db):
    exam, q1, qp_item, subject = setup_quality_fixture(db)
    token = get_auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get(f"/api/v1/analytics/exams/{exam.id}/questions/{q1.id}", headers=headers)
    assert res.status_code == 200
    data = res.json()

    disc = data["discrimination"]
    assert disc["discrimination_category"] in ("STRONG", "ACCEPTABLE")
    assert disc["discrimination_index"] is not None
    assert disc["discrimination_index"] > 0.0


from app.db.models import (
    Examination, Subject, Unit, Topic, LearningOutcome, User, Question,
    QuestionPaper, QuestionPaperVersion, QuestionPaperItem,
    AnswerPaper, Evaluation, EvaluationItem, EvaluationStatusEnum, QuestionQualityReview,
    QuestionTypeEnum, DifficultyLevelEnum, BloomLevelEnum
)

def test_insufficient_sample_for_small_cohort(client, db):
    user = db.query(User).filter(User.email == "faculty@example.com").first()
    existing_subj = db.query(Subject).first()
    subject = Subject(
        name="Small Cohort Subj",
        code=f"SUBJ_SMALL_{generate_uuid()[:6]}",
        credits=4,
        course_id=existing_subj.course_id if existing_subj else None,
        department_id=existing_subj.department_id if existing_subj else None,
        semester_id=existing_subj.semester_id if existing_subj else None,
        academic_year_id=existing_subj.academic_year_id if existing_subj else None
    )
    db.add(subject)
    db.flush()

    q = Question(
        subject_id=subject.id,
        question_text="Small cohort question",
        question_type=QuestionTypeEnum.DESCRIPTIVE,
        difficulty=DifficultyLevelEnum.MEDIUM,
        bloom_level=BloomLevelEnum.UNDERSTAND,
        marks=10.0
    )
    db.add(q)
    db.flush()

    exam = Examination(subject_id=subject.id, name="Small Cohort Exam")
    db.add(exam)
    db.flush()

    qp = QuestionPaper(subject_id=subject.id, title="Small Paper", paper_code=f"QP_{generate_uuid()[:6]}")
    db.add(qp)
    db.flush()

    qp_ver = QuestionPaperVersion(question_paper_id=qp.id, version_number=1)
    db.add(qp_ver)
    db.flush()

    qp_item = QuestionPaperItem(question_paper_version_id=qp_ver.id, question_id=q.id, order_index=1, section="Section A", question_number="1", marks=10.0, question_text_snapshot=q.question_text)
    db.add(qp_item)
    db.flush()

    # Create only 2 evaluations (< 4 minimum cohort limit)
    for i in range(2):
        p = AnswerPaper(examination_id=exam.id, student_id=generate_uuid(), status="FINALIZED")
        db.add(p)
        db.flush()
        e = Evaluation(examination_id=exam.id, answer_paper_id=p.id, student_id=p.student_id, status="FINALIZED", total_final_marks=8.0)
        db.add(e)
        db.flush()
        item = EvaluationItem(evaluation_id=e.id, question_paper_item_id=qp_item.id, final_marks=8.0, maximum_marks=10.0)
        db.add(item)
    db.commit()

    token = get_auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}
    res = client.get(f"/api/v1/analytics/exams/{exam.id}/questions/{q.id}", headers=headers)
    assert res.status_code == 200
    disc = res.json()["discrimination"]
    assert disc["discrimination_category"] == "INSUFFICIENT_SAMPLE"
    assert disc["discrimination_index"] is None


def test_record_question_quality_review(client, db):
    exam, q1, qp_item, subject = setup_quality_fixture(db)
    token = get_auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "examination_id": exam.id,
        "status": "KEEP",
        "note": "Question performed well with strong discrimination."
    }

    res = client.post(f"/api/v1/analytics/questions/{q1.id}/review", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["question_id"] == q1.id
    assert data["status"] == "KEEP"
    assert data["note"] == "Question performed well with strong discrimination."
