from typing import List, Optional
from sqlalchemy.orm import Session

try:
    from app.db.models import Rubric, RubricCriterion, Question, QuestionPaperItem
    from app.schemas.rubric import RubricValidationResult
except ImportError:
    from backend.app.db.models import Rubric, RubricCriterion, Question, QuestionPaperItem
    from backend.app.schemas.rubric import RubricValidationResult

class RubricValidationService:
    def __init__(self, db: Session):
        self.db = db

    def validate_rubric(
        self,
        rubric: Rubric,
        target_item_marks: Optional[float] = None
    ) -> RubricValidationResult:
        errors: List[str] = []
        warnings: List[str] = []

        criteria = rubric.criteria or []
        if not criteria:
            errors.append("Rubric has no criteria.")
            return RubricValidationResult(
                is_valid=False,
                total_criterion_marks=0.0,
                configured_total_marks=rubric.total_marks,
                target_item_marks=target_item_marks,
                errors=errors,
                warnings=warnings
            )

        sum_criterion_marks = sum(c.marks for c in criteria)

        # 1. Rubric configured marks check
        if abs(sum_criterion_marks - rubric.total_marks) > 0.01:
            errors.append(
                f"Sum of criterion marks ({sum_criterion_marks}) does not equal configured rubric total marks ({rubric.total_marks})."
            )

        # 2. Target item marks check (if assigned)
        if target_item_marks is not None:
            if abs(rubric.total_marks - target_item_marks) > 0.01:
                errors.append(
                    f"Rubric total marks ({rubric.total_marks}) does not match target item maximum marks ({target_item_marks})."
                )

        # 3. Individual criterion checks
        orders = []
        for idx, c in enumerate(criteria):
            if c.marks <= 0:
                errors.append(f"Criterion '{c.criterion}' must have marks > 0 (found {c.marks}).")
            if c.min_marks < 0 or c.min_marks > c.marks:
                errors.append(f"Criterion '{c.criterion}' min_marks ({c.min_marks}) must be between 0 and maximum marks ({c.marks}).")
            orders.append(c.order_index)

        if len(orders) != len(set(orders)):
            warnings.append("Rubric criteria contain duplicate order indices.")

        is_valid = len(errors) == 0

        return RubricValidationResult(
            is_valid=is_valid,
            total_criterion_marks=sum_criterion_marks,
            configured_total_marks=rubric.total_marks,
            target_item_marks=target_item_marks,
            errors=errors,
            warnings=warnings
        )
