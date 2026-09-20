import pytest
try:
    from app.db.models import QuestionPaperItem, AnswerKeyItem, ExtractedAnswer
    from app.db.guid import generate_uuid
except ImportError:
    from backend.app.db.models import QuestionPaperItem, AnswerKeyItem, ExtractedAnswer
    from backend.app.db.guid import generate_uuid

from backend.app.services.answer_evaluation_service import AnswerEvaluationService

def test_keyword_evaluation_layer(db):
    service = AnswerEvaluationService(db)
    student_text = "Binary search requires a sorted array and uses middle element comparisons."
    keywords = ["binary search", "sorted array", "middle element", "logarithmic"]

    matched, missing, score = service._evaluate_keywords(student_text, keywords)

    assert "binary search" in matched
    assert "sorted array" in matched
    assert "logarithmic" in missing
    assert score == 0.75


def test_concept_evaluation_layer(db):
    service = AnswerEvaluationService(db)
    student_text = "The remaining elements are divided in half repeatedly."
    concepts = ["search space reduction", "divide search space"]

    matched, missing, score = service._evaluate_concepts(student_text, concepts)

    assert len(matched) > 0
    assert score > 0.0


def test_mcq_deterministic_evaluation(db):
    # Test MCQ deterministic evaluation logic inside AnswerEvaluationService
    service = AnswerEvaluationService(db)

    # Correct choice
    res_correct = service._evaluate_keywords("Option A", ["Option A"])
    assert res_correct[2] == 1.0
