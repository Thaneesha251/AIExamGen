from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

try:
    from app.db.models import Blueprint, BlueprintRule, Question
    from app.schemas.blueprint import BlueprintValidationResult
    from app.services.question_eligibility_service import QuestionEligibilityService
except ImportError:
    from backend.app.db.models import Blueprint, BlueprintRule, Question
    from backend.app.schemas.blueprint import BlueprintValidationResult
    from backend.app.services.question_eligibility_service import QuestionEligibilityService

class BlueprintValidationService:
    def __init__(self, db: Session):
        self.db = db
        self.eligibility_service = QuestionEligibilityService(db)

    def validate_blueprint(self, blueprint: Blueprint) -> BlueprintValidationResult:
        errors: List[str] = []
        warnings: List[str] = []
        section_summaries: List[Dict[str, Any]] = []

        rules = blueprint.rules or []
        if not rules:
            errors.append("Blueprint contains no rules or sections.")
            return BlueprintValidationResult(
                is_valid=False,
                total_marks=0.0,
                configured_total_marks=blueprint.total_marks,
                total_question_count=0,
                errors=errors,
                warnings=warnings,
                section_summaries=[]
            )

        sum_marks = sum(r.total_marks for r in rules)
        sum_questions = sum(r.question_count for r in rules)

        # 1. Total Marks Check
        if abs(sum_marks - blueprint.total_marks) > 0.01:
            errors.append(
                f"Total rules marks ({sum_marks}) does not match configured blueprint total marks ({blueprint.total_marks})."
            )

        # 2. Per-rule structural & distribution checks
        for r in rules:
            rule_errors: List[str] = []

            # Question count * marks per question check
            expected_total = r.question_count * r.marks_per_question
            if abs(expected_total - r.total_marks) > 0.01:
                rule_errors.append(
                    f"Section '{r.section}' total marks ({r.total_marks}) does not equal question count ({r.question_count}) × marks ({r.marks_per_question}) = {expected_total}."
                )

            # Distribution Checks
            dist = r.distribution_json or {}
            diff_dist = dist.get("difficulty_distribution", {})
            if diff_dist:
                sum_diff = sum(diff_dist.values())
                if sum_diff != r.question_count:
                    rule_errors.append(
                        f"Section '{r.section}' difficulty distribution total ({sum_diff}) does not match question count ({r.question_count})."
                    )

            bloom_dist = dist.get("bloom_distribution", {})
            if bloom_dist:
                sum_bloom = sum(bloom_dist.values())
                if sum_bloom != r.question_count:
                    rule_errors.append(
                        f"Section '{r.section}' Bloom distribution total ({sum_bloom}) does not match question count ({r.question_count})."
                    )

            unit_dist = dist.get("unit_distribution", {})
            if unit_dist:
                sum_unit = sum(unit_dist.values())
                if sum_unit != r.question_count:
                    rule_errors.append(
                        f"Section '{r.section}' Unit distribution total ({sum_unit}) does not match question count ({r.question_count})."
                    )

            # Check question bank pool availability
            eligible_qs = self.eligibility_service.get_eligible_questions_for_rule(
                subject_id=blueprint.subject_id,
                rule=r
            )
            available_count = len(eligible_qs)
            if available_count < r.question_count:
                rule_errors.append(
                    f"Section '{r.section}' requires {r.question_count} eligible questions, but only {available_count} exist in the approved question bank."
                )
            elif available_count < r.question_count + 2:
                warnings.append(
                    f"Section '{r.section}' has tight candidate pool ({available_count} available for {r.question_count} required)."
                )

            if rule_errors:
                errors.extend(rule_errors)

            section_summaries.append({
                "section": r.section,
                "question_count": r.question_count,
                "marks_per_question": r.marks_per_question,
                "total_marks": r.total_marks,
                "available_eligible_questions": available_count,
                "status": "VALID" if not rule_errors else "INVALID"
            })

        is_valid = len(errors) == 0

        return BlueprintValidationResult(
            is_valid=is_valid,
            total_marks=sum_marks,
            configured_total_marks=blueprint.total_marks,
            total_question_count=sum_questions,
            errors=errors,
            warnings=warnings,
            section_summaries=section_summaries
        )
