import pytest
from app.db.models import Blueprint, BlueprintRule, Subject, User, Question, QuestionStatusEnum, QuestionTypeEnum
from app.services.blueprint_service import BlueprintService
from app.schemas.blueprint import BlueprintCreate, BlueprintRuleCreate

def test_blueprint_crud_and_validation(db):
    sub = db.query(Subject).first()
    assert sub is not None

    admin_user = db.query(User).filter(User.email == "admin@example.com").first()
    assert admin_user is not None

    # Add candidate approved questions matching rule marks
    for i in range(10):
        q = Question(
            subject_id=sub.id,
            question_text=f"Blueprint Test Q_A_{i}",
            question_type=QuestionTypeEnum.SHORT_ANSWER,
            marks=2.0,
            status=QuestionStatusEnum.APPROVED
        )
        db.add(q)

    for i in range(5):
        q = Question(
            subject_id=sub.id,
            question_text=f"Blueprint Test Q_B_{i}",
            question_type=QuestionTypeEnum.DESCRIPTIVE,
            marks=16.0,
            status=QuestionStatusEnum.APPROVED
        )
        db.add(q)
    db.commit()

    bp_service = BlueprintService(db)

    rule1 = BlueprintRuleCreate(section="Part A", question_count=10, marks_per_question=2.0, total_marks=20.0)
    rule2 = BlueprintRuleCreate(section="Part B", question_count=5, marks_per_question=16.0, total_marks=80.0)

    req = BlueprintCreate(
        subject_id=sub.id,
        name="End-Sem Blueprint CS301",
        total_marks=100.0,
        rules=[rule1, rule2]
    )

    bp = bp_service.create_blueprint(req, admin_user)
    assert bp.id is not None
    assert bp.name == "End-Sem Blueprint CS301"
    assert len(bp.rules) == 2

    # Validation
    val_res = bp_service.validate_blueprint_by_id(bp.id)
    assert val_res.configured_total_marks == 100.0
    assert val_res.total_marks == 100.0
    assert val_res.is_valid is True
