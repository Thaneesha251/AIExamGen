import pytest
try:
    from app.db.models import Evaluation, EvaluationItem
    from app.db.guid import generate_uuid
except ImportError:
    from backend.app.db.models import Evaluation, EvaluationItem
    from backend.app.db.guid import generate_uuid

def test_evaluation_version_preservation(db):
    exam_id = generate_uuid()
    paper_id = generate_uuid()
    st_id = generate_uuid()

    eval_v1 = Evaluation(
        examination_id=exam_id,
        answer_paper_id=paper_id,
        student_id=st_id,
        version=1,
        total_ai_marks=7.5,
        overall_confidence=0.85
    )
    eval_v2 = Evaluation(
        examination_id=exam_id,
        answer_paper_id=paper_id,
        student_id=st_id,
        version=2,
        total_ai_marks=8.0,
        overall_confidence=0.90
    )
    db.add_all([eval_v1, eval_v2])
    db.flush()

    history = db.query(Evaluation).filter(Evaluation.answer_paper_id == paper_id).order_by(Evaluation.version.asc()).all()
    assert len(history) == 2
    assert history[0].version == 1
    assert history[0].total_ai_marks == 7.5
    assert history[1].version == 2
    assert history[1].total_ai_marks == 8.0
