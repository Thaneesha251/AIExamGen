"""
AI Question Validation Agent.
Validates generated questions against academic standards, MCQ structure rules,
Bloom taxonomy heuristics, and duplicate detection.
"""

from typing import List, Dict, Any, Optional
from ai.services.similarity_service import QuestionSimilarityService
from backend.app.schemas.question_generation import GeneratedQuestionSchema, QuestionValidationResult
from backend.app.db.models.enums import QuestionTypeEnum

class QuestionValidationAgent:
    """Agent responsible for checking question quality, structural completeness, and duplicate detection."""

    def __init__(self, duplicate_threshold: float = 0.75):
        self.similarity_service = QuestionSimilarityService(duplicate_threshold=duplicate_threshold)

    def validate_question(
        self,
        question: GeneratedQuestionSchema,
        existing_questions_pool: Optional[List[Dict[str, Any]]] = None
    ) -> QuestionValidationResult:
        """Runs full validation pipeline on a generated question schema."""
        warnings: List[str] = []
        is_valid = True
        
        alignment_score = 1.0
        difficulty_score = 1.0
        bloom_alignment_score = 1.0
        completeness_score = 1.0
        duplicate_score = 0.0
        similar_question_id = None

        # 1. Basic Text Completeness Check
        if not question.question_text or len(question.question_text.strip()) < 10:
            is_valid = False
            completeness_score = 0.2
            warnings.append("Question text is too short or empty.")

        if not question.expected_answer or len(question.expected_answer.strip()) < 2:
            completeness_score *= 0.7
            warnings.append("Expected answer / model answer is missing or incomplete.")

        # 2. MCQ Specific Validation
        if question.question_type == QuestionTypeEnum.MCQ:
            if not question.options or not isinstance(question.options, dict):
                is_valid = False
                warnings.append("MCQ question missing options dictionary.")
            else:
                opts = question.options.get("options", [])
                correct = question.options.get("correct_option")
                
                if not opts or len(opts) < 4:
                    is_valid = False
                    warnings.append(f"MCQ must have at least 4 options. Found {len(opts) if opts else 0}.")
                
                if not correct:
                    is_valid = False
                    warnings.append("MCQ must specify a correct option.")
                elif opts and correct not in opts:
                    # Soft warning if correct option isn't an exact match in the options array
                    warnings.append("Correct option string does not strictly match options array element.")

        # 3. Bloom & Difficulty Heuristics
        # E.g. CREATE level should generally have longer expected answers / code
        if question.bloom_level.value in ["EVALUATE", "CREATE"] and question.marks < 4.0:
            bloom_alignment_score = 0.8
            warnings.append("High Bloom level question (EVALUATE/CREATE) allocated low marks.")

        # 4. Duplicate Detection against Existing Questions
        if existing_questions_pool:
            max_sim, sim_id, _ = self.similarity_service.find_most_similar_question(
                candidate_text=question.question_text,
                existing_questions=existing_questions_pool
            )
            duplicate_score = round(max_sim, 4)
            if duplicate_score >= self.similarity_service.duplicate_threshold:
                is_valid = False
                similar_question_id = sim_id
                warnings.append(f"Potential duplicate question detected (Similarity: {duplicate_score * 100:.1f}%).")

        return QuestionValidationResult(
            is_valid=is_valid,
            alignment_score=alignment_score,
            difficulty_score=difficulty_score,
            bloom_alignment_score=bloom_alignment_score,
            duplicate_score=duplicate_score,
            completeness_score=completeness_score,
            warnings=warnings,
            similar_question_id=similar_question_id
        )
