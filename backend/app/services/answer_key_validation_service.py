from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

try:
    from app.db.models import AnswerKey, AnswerKeyItem, QuestionPaperVersion
    from app.schemas.answer_key import AnswerKeyValidationResult
except ImportError:
    from backend.app.db.models import AnswerKey, AnswerKeyItem, QuestionPaperVersion
    from backend.app.schemas.answer_key import AnswerKeyValidationResult

class AnswerKeyValidationService:
    def __init__(self, db: Session):
        self.db = db

    def validate_answer_key(
        self,
        answer_key: AnswerKey,
        paper_version: QuestionPaperVersion
    ) -> AnswerKeyValidationResult:
        errors: List[str] = []
        warnings: List[str] = []
        item_summaries: List[Dict[str, Any]] = []

        paper_items = paper_version.items or []
        ak_items = answer_key.items or []

        if not paper_items:
            errors.append("Question paper version contains no items.")
            return AnswerKeyValidationResult(
                is_valid=False,
                total_items=0,
                total_marks=0.0,
                target_paper_marks=0.0,
                errors=errors,
                warnings=warnings,
                item_summaries=[]
            )

        target_total_marks = sum(pi.marks for pi in paper_items)
        ak_total_marks = sum(aki.maximum_marks for aki in ak_items)

        # 1. Total Marks Check
        if abs(ak_total_marks - target_total_marks) > 0.01:
            errors.append(
                f"Answer key total marks ({ak_total_marks}) does not match question paper total marks ({target_total_marks})."
            )

        # Map paper items by ID
        paper_item_map = {pi.id: pi for pi in paper_items}
        ak_item_map = {aki.question_paper_item_id: aki for aki in ak_items}

        # 2. Coverage Check: Check every paper item has an answer key item
        for pi in paper_items:
            aki = ak_item_map.get(pi.id)
            if not aki:
                errors.append(f"Question #{pi.question_number} is missing an answer key item.")
                item_summaries.append({
                    "question_number": pi.question_number,
                    "paper_item_id": pi.id,
                    "status": "MISSING",
                    "error": "No model answer provided"
                })
                continue

            # Item marks check
            if abs(aki.maximum_marks - pi.marks) > 0.01:
                errors.append(
                    f"Question #{pi.question_number} answer key marks ({aki.maximum_marks}) does not match question marks ({pi.marks})."
                )

            # Content Quality check
            model_ans = (aki.model_answer or "").strip()
            if not model_ans:
                errors.append(f"Question #{pi.question_number} model answer is empty.")
            elif len(model_ans) < 5:
                warnings.append(f"Question #{pi.question_number} model answer is very brief.")

            q_type = pi.question_type_snapshot or "DESCRIPTIVE"
            if q_type in ["DESCRIPTIVE", "PROBLEM_SOLVING", "PROGRAMMING", "CASE_STUDY"]:
                if not aki.keywords and not aki.concepts and not aki.marking_notes:
                    warnings.append(f"Question #{pi.question_number} ({q_type}) has no keywords, concepts, or marking notes assigned.")

            item_summaries.append({
                "question_number": pi.question_number,
                "paper_item_id": pi.id,
                "answer_key_item_id": aki.id,
                "marks": aki.maximum_marks,
                "has_rubric": bool(aki.rubric_id),
                "status": "VALID" if bool(model_ans) and abs(aki.maximum_marks - pi.marks) <= 0.01 else "INVALID"
            })

        # 3. Orphan check: check if any answer key item references a paper item that doesn't exist
        for aki in ak_items:
            if aki.question_paper_item_id not in paper_item_map:
                errors.append(f"Answer key item '{aki.id}' references non-existent paper item '{aki.question_paper_item_id}'.")

        is_valid = len(errors) == 0

        return AnswerKeyValidationResult(
            is_valid=is_valid,
            total_items=len(ak_items),
            total_marks=ak_total_marks,
            target_paper_marks=target_total_marks,
            errors=errors,
            warnings=warnings,
            item_summaries=item_summaries
        )
