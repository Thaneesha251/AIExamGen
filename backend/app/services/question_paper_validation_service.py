from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

try:
    from app.db.models import QuestionPaper, QuestionPaperVersion, QuestionPaperItem, Question
    from app.schemas.question_paper import PaperValidationResult
    from app.db.models.enums import QuestionStatusEnum
except ImportError:
    from backend.app.db.models import QuestionPaper, QuestionPaperVersion, QuestionPaperItem, Question
    from backend.app.schemas.question_paper import PaperValidationResult
    from backend.app.db.models.enums import QuestionStatusEnum

class QuestionPaperValidationService:
    def __init__(self, db: Session):
        self.db = db

    def validate_paper_version(
        self,
        paper: QuestionPaper,
        paper_version: QuestionPaperVersion
    ) -> PaperValidationResult:
        errors: List[str] = []
        warnings: List[str] = []
        section_summaries: List[Dict[str, Any]] = []

        items = paper_version.items or []
        if not items:
            errors.append("Question paper version contains no items.")
            return PaperValidationResult(
                is_valid=False,
                total_marks=0.0,
                target_total_marks=paper.total_marks,
                total_question_count=0,
                errors=errors,
                warnings=warnings,
                section_summaries=[]
            )

        calculated_marks = sum(item.marks for item in items)
        total_questions = len(items)

        # 1. Total Marks Check
        if abs(calculated_marks - paper.total_marks) > 0.01:
            errors.append(
                f"Calculated paper total marks ({calculated_marks}) does not match target total marks ({paper.total_marks})."
            )

        # 2. Duplicate Question Check
        seen_qids = set()
        for item in items:
            if item.question_id:
                if item.question_id in seen_qids:
                    errors.append(f"Duplicate question ID '{item.question_id}' found in paper (Question #{item.question_number}).")
                seen_qids.add(item.question_id)

        # 3. Question Status Check
        if seen_qids:
            unapproved = self.db.query(Question).filter(
                Question.id.in_(list(seen_qids)),
                ~Question.status.in_([QuestionStatusEnum.APPROVED, QuestionStatusEnum.ACTIVE])
            ).all()
            if unapproved:
                for uq in unapproved:
                    errors.append(f"Question '{uq.id}' included in paper has unapproved status '{uq.status}'.")

        # 4. Section Summaries & Blueprint Alignment Check
        sections_map: Dict[str, Dict[str, Any]] = {}
        for item in items:
            sec = item.section or "General"
            if sec not in sections_map:
                sections_map[sec] = {"count": 0, "marks": 0.0}
            sections_map[sec]["count"] += 1
            sections_map[sec]["marks"] += item.marks

        if paper.blueprint and paper.blueprint.rules:
            blueprint_rules_map = {r.section: r for r in paper.blueprint.rules}
            for sec_name, r in blueprint_rules_map.items():
                sec_data = sections_map.get(sec_name, {"count": 0, "marks": 0.0})
                if sec_data["count"] != r.question_count:
                    errors.append(
                        f"Section '{sec_name}' question count ({sec_data['count']}) does not match blueprint rule count ({r.question_count})."
                    )
                if abs(sec_data["marks"] - r.total_marks) > 0.01:
                    errors.append(
                        f"Section '{sec_name}' total marks ({sec_data['marks']}) does not match blueprint rule marks ({r.total_marks})."
                    )

        for sec_name, data in sections_map.items():
            section_summaries.append({
                "section": sec_name,
                "question_count": data["count"],
                "total_marks": data["marks"]
            })

        is_valid = len(errors) == 0

        return PaperValidationResult(
            is_valid=is_valid,
            total_marks=calculated_marks,
            target_total_marks=paper.total_marks,
            total_question_count=total_questions,
            errors=errors,
            warnings=warnings,
            section_summaries=section_summaries
        )
