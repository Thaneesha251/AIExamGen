import pytest
from backend.app.services.answer_evaluation_service import AnswerEvaluationService

def test_score_variance_calculation(db):
    service = AnswerEvaluationService(db)

    # Identical scores -> 0 variance
    var_zero = service._calculate_score_variance([0.8, 0.8, 0.8, 0.8])
    assert var_zero == 0.0

    # High variance scores -> positive variance
    var_high = service._calculate_score_variance([1.0, 0.2, 0.9, 0.1])
    assert var_high > 0.05
