import pytest
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
try:
    from app.db.session import SessionLocal
    from app.db.models import (
        User, Role, RoleEnum, Department, Course, Semester, AcademicYear,
        Subject, Unit, Topic, LearningOutcome, Question, QuestionTypeEnum,
        DifficultyLevelEnum, BloomLevelEnum, QuestionBank, QuestionBankItem,
        Blueprint, BlueprintRule, QuestionPaper, QuestionPaperVersion,
        QuestionPaperItem, AnswerKey, AnswerKeyItem, Examination,
        ExaminationStudent, AnswerPaper, Evaluation, EvaluationItem,
        AuditLog, AuditActionEnum
    )
except ImportError:
    from backend.app.db.session import SessionLocal
    from backend.app.db.models import (
        User, Role, RoleEnum, Department, Course, Semester, AcademicYear,
        Subject, Unit, Topic, LearningOutcome, Question, QuestionTypeEnum,
        DifficultyLevelEnum, BloomLevelEnum, QuestionBank, QuestionBankItem,
        Blueprint, BlueprintRule, QuestionPaper, QuestionPaperVersion,
        QuestionPaperItem, AnswerKey, AnswerKeyItem, Examination,
        ExaminationStudent, AnswerPaper, Evaluation, EvaluationItem,
        AuditLog, AuditActionEnum
    )

@pytest.fixture
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

def test_user_role_relationship_and_uniqueness(db_session: Session):
    admin = db_session.query(User).filter(User.email == "admin@example.com").first()
    assert admin is not None
    assert admin.role.name == RoleEnum.ADMIN
    assert admin.full_name == "System Administrator"

    # Verify Email Uniqueness Constraint
    duplicate_user = User(
        role_id=admin.role_id,
        email="admin@example.com",
        password_hash="pass",
        first_name="Dup",
        last_name="User"
    )
    db_session.add(duplicate_user)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

def test_subject_unit_topic_hierarchy(db_session: Session):
    subject = db_session.query(Subject).filter(Subject.code == "CS301").first()
    assert subject is not None
    assert len(subject.units) == 5
    assert len(subject.learning_outcomes) == 5

    unit1 = db_session.query(Unit).filter(Unit.subject_id == subject.id, Unit.unit_number == 1).first()
    assert unit1 is not None
    assert len(unit1.topics) >= 1

def test_question_bank_duplicate_prevention(db_session: Session):
    qbank = db_session.query(QuestionBank).first()
    question = db_session.query(Question).first()
    assert qbank is not None
    assert question is not None

    # Adding same question twice should fail on unique constraint
    duplicate_item = QuestionBankItem(
        question_bank_id=qbank.id,
        question_id=question.id
    )
    db_session.add(duplicate_item)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

def test_historical_question_snapshot_integrity(db_session: Session):
    paper_item = db_session.query(QuestionPaperItem).first()
    assert paper_item is not None
    assert paper_item.question_text_snapshot is not None

    # Mutate original Question text
    question = db_session.get(Question, paper_item.question_id)
    original_text = question.question_text
    snapshot_text = paper_item.question_text_snapshot

    question.question_text = "MODIFIED QUESTION TEXT"
    db_session.commit()

    # Re-fetch paper item: snapshot MUST remain original
    reloaded_item = db_session.get(QuestionPaperItem, paper_item.id)
    assert reloaded_item.question_text_snapshot == snapshot_text
    assert reloaded_item.question_text_snapshot != "MODIFIED QUESTION TEXT"

    # Restore question text
    question.question_text = original_text
    db_session.commit()

def test_blueprint_and_rules(db_session: Session):
    blueprint = db_session.query(Blueprint).first()
    assert blueprint is not None
    assert len(blueprint.rules) == 3
    assert blueprint.total_marks == 100.0

def test_audit_log_record(db_session: Session):
    admin = db_session.query(User).filter(User.email == "admin@example.com").first()
    audit = AuditLog(
        user_id=admin.id,
        action=AuditActionEnum.GENERATE_PAPER,
        entity_type="QuestionPaper",
        entity_id="test-paper-123",
        old_values=None,
        new_values={"status": "APPROVED"}
    )
    db_session.add(audit)
    db_session.commit()
    db_session.refresh(audit)

    assert audit.id is not None
    assert audit.action == AuditActionEnum.GENERATE_PAPER
