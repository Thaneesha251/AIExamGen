from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_

try:
    from app.db.models import Question, BlueprintRule
    from app.db.models.enums import QuestionStatusEnum, QuestionTypeEnum, DifficultyLevelEnum, BloomLevelEnum
except ImportError:
    from backend.app.db.models import Question, BlueprintRule
    from backend.app.db.models.enums import QuestionStatusEnum, QuestionTypeEnum, DifficultyLevelEnum, BloomLevelEnum

class QuestionEligibilityService:
    def __init__(self, db: Session):
        self.db = db

    def get_base_eligible_query(self, subject_id: str):
        """
        Base query for eligible questions.
        MUST be in APPROVED or ACTIVE status for the given subject.
        """
        return self.db.query(Question).filter(
            Question.subject_id == subject_id,
            Question.status.in_([QuestionStatusEnum.APPROVED, QuestionStatusEnum.ACTIVE])
        )

    def get_eligible_questions_for_rule(
        self,
        subject_id: str,
        rule: BlueprintRule,
        difficulty: Optional[DifficultyLevelEnum] = None,
        bloom_level: Optional[BloomLevelEnum] = None,
        unit_id: Optional[str] = None,
        exclude_question_ids: Optional[List[str]] = None
    ) -> List[Question]:
        """
        Get candidate questions matching subject, rule criteria (marks, question_type),
        and optional specific constraints (difficulty, bloom_level, unit_id), excluding requested IDs.
        """
        query = self.get_base_eligible_query(subject_id)

        # Filter by marks per question
        query = query.filter(Question.marks == rule.marks_per_question)

        # Filter by question type if rule specifies one
        if rule.question_type:
            query = query.filter(Question.question_type == rule.question_type)

        # Filter by difficulty if provided
        if difficulty:
            query = query.filter(Question.difficulty == difficulty)

        # Filter by bloom_level if provided
        if bloom_level:
            query = query.filter(Question.bloom_level == bloom_level)

        # Filter by unit_id if provided
        if unit_id:
            query = query.filter(Question.unit_id == unit_id)

        # Exclude IDs if provided
        if exclude_question_ids:
            query = query.filter(~Question.id.in_(exclude_question_ids))

        return query.all()
