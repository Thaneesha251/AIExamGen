import pytest
from app.db.models import Rubric, RubricCriterion, User, Subject
from app.services.rubric_service import RubricService
from app.schemas.rubric import RubricCreate, RubricCriterionCreate

def test_rubric_creation_validation_and_assignment(db):
    user = db.query(User).filter(User.email == "admin@example.com").first()
    sub = db.query(Subject).first()
    assert user is not None
    assert sub is not None

    rubric_service = RubricService(db)

    c1 = RubricCriterionCreate(criterion="Design Patterns", description="Use of Gang of Four patterns", marks=5.0)
    c2 = RubricCriterionCreate(criterion="UML Diagrams", description="Class and Sequence diagrams", marks=5.0)

    req = RubricCreate(
        name="Software Architecture Rubric",
        subject_id=sub.id,
        total_marks=10.0,
        criteria=[c1, c2]
    )

    rubric = rubric_service.create_rubric(req, user)
    assert rubric.id is not None
    assert len(rubric.criteria) == 2

    # Validate rubric marks
    val_res = rubric_service.validate_rubric_by_id(rubric.id, target_marks=10.0)
    assert val_res.is_valid is True

    # Validate incompatible target marks rejection
    val_res_bad = rubric_service.validate_rubric_by_id(rubric.id, target_marks=5.0)
    assert val_res_bad.is_valid is False
    assert any("does not match target item maximum marks" in e for e in val_res_bad.errors)
