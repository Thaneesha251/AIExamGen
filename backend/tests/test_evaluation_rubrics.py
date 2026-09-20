import pytest
try:
    from app.db.models import AnswerKeyItem, Rubric, RubricCriterion
    from app.db.guid import generate_uuid
except ImportError:
    from backend.app.db.models import AnswerKeyItem, Rubric, RubricCriterion
    from backend.app.db.guid import generate_uuid

from backend.app.services.answer_evaluation_service import AnswerEvaluationService

def test_rubric_evaluation_partial_credit(db):
    service = AnswerEvaluationService(db)

    # Build dummy AnswerKeyItem with Rubric
    rubric = Rubric(
        name="Computer Science Algorithm Rubric",
        total_marks=10.0
    )
    c1 = RubricCriterion(
        rubric=rubric,
        criterion="Concept Definition",
        description="Clear definition of algorithm concept",
        marks=5.0
    )
    c2 = RubricCriterion(
        rubric=rubric,
        criterion="Time Complexity",
        description="Mentions O(log n) performance",
        marks=5.0
    )
    db.add_all([rubric, c1, c2])
    db.flush()

    ak_item = AnswerKeyItem(
        answer_key_id=generate_uuid(),
        rubric_id=rubric.id,
        model_answer="Clear definition of algorithm concept with O(log n) time complexity."
    )
    ak_item.rubric = rubric

    student_text = "Clear definition of algorithm concept."
    score, criterion_scores = service._evaluate_rubric(student_text, ak_item)

    assert score > 0.0
    assert len(criterion_scores) == 2
    assert criterion_scores[0]["awarded_marks"] > 0
