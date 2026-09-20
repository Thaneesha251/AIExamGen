import random
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

try:
    from app.db.models import Blueprint, BlueprintRule, Question
    from app.services.question_eligibility_service import QuestionEligibilityService
    from app.services.question_exposure_service import QuestionExposureService
    from app.db.models.enums import DifficultyLevelEnum, BloomLevelEnum
except ImportError:
    from backend.app.db.models import Blueprint, BlueprintRule, Question
    from backend.app.services.question_eligibility_service import QuestionEligibilityService
    from backend.app.services.question_exposure_service import QuestionExposureService
    from backend.app.db.models.enums import DifficultyLevelEnum, BloomLevelEnum

class QuestionSelectionService:
    def __init__(self, db: Session):
        self.db = db
        self.eligibility_service = QuestionEligibilityService(db)
        self.exposure_service = QuestionExposureService(db)

    def select_questions_for_blueprint(
        self,
        blueprint: Blueprint,
        seed: int = 42,
        exclude_question_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Deterministically selects questions for a blueprint based on rules and distributions.
        Returns a list of dicts:
        [
            {
                "section": "Section A",
                "question_number": "1",
                "question": <Question object>,
                "marks": 2.0,
                "order_index": 1
            },
            ...
        ]
        """
        rng = random.Random(seed)
        already_selected_ids = list(exclude_question_ids or [])
        paper_items: List[Dict[str, Any]] = []

        rules = blueprint.rules or []
        if not rules:
            raise ValueError("Blueprint contains no rules for paper generation.")

        global_order_index = 1

        for rule in rules:
            section_name = rule.section
            rule_question_count = rule.question_count
            dist = rule.distribution_json or {}

            diff_dist = dist.get("difficulty_distribution", {})
            bloom_dist = dist.get("bloom_distribution", {})
            unit_dist = dist.get("unit_distribution", {})

            # If granular distributions are provided, handle sub-selection buckets
            if diff_dist:
                selected_for_rule = self._select_by_difficulty_distribution(
                    blueprint.subject_id, rule, diff_dist, already_selected_ids, rng
                )
            elif bloom_dist:
                selected_for_rule = self._select_by_bloom_distribution(
                    blueprint.subject_id, rule, bloom_dist, already_selected_ids, rng
                )
            elif unit_dist:
                selected_for_rule = self._select_by_unit_distribution(
                    blueprint.subject_id, rule, unit_dist, already_selected_ids, rng
                )
            else:
                # Generic selection for rule
                selected_for_rule = self._select_generic_for_rule(
                    blueprint.subject_id, rule, rule_question_count, already_selected_ids, rng
                )

            if len(selected_for_rule) < rule_question_count:
                raise ValueError(
                    f"Insufficient approved questions in Question Bank for section '{section_name}'. "
                    f"Required: {rule_question_count}, Available matching criteria: {len(selected_for_rule)}."
                )

            # Assign question numbers and order indices
            q_num_counter = 1
            for q in selected_for_rule:
                already_selected_ids.append(q.id)
                paper_items.append({
                    "section": section_name,
                    "question_number": f"Q{global_order_index}",
                    "question": q,
                    "marks": rule.marks_per_question,
                    "order_index": global_order_index
                })
                q_num_counter += 1
                global_order_index += 1

        return paper_items

    def _select_generic_for_rule(
        self,
        subject_id: str,
        rule: BlueprintRule,
        count: int,
        exclude_ids: List[str],
        rng: random.Random
    ) -> List[Question]:
        candidates = self.eligibility_service.get_eligible_questions_for_rule(
            subject_id=subject_id,
            rule=rule,
            exclude_question_ids=exclude_ids
        )
        return self._pick_least_exposed(candidates, count, rng)

    def _select_by_difficulty_distribution(
        self,
        subject_id: str,
        rule: BlueprintRule,
        diff_dist: Dict[str, int],
        exclude_ids: List[str],
        rng: random.Random
    ) -> List[Question]:
        selected: List[Question] = []
        current_excludes = list(exclude_ids)

        for diff_str, count in diff_dist.items():
            if count <= 0:
                continue
            try:
                diff_enum = DifficultyLevelEnum(diff_str)
            except ValueError:
                continue

            candidates = self.eligibility_service.get_eligible_questions_for_rule(
                subject_id=subject_id,
                rule=rule,
                difficulty=diff_enum,
                exclude_question_ids=current_excludes
            )

            picked = self._pick_least_exposed(candidates, count, rng)
            if len(picked) < count:
                raise ValueError(
                    f"Insufficient questions for section '{rule.section}' with difficulty '{diff_str}'. "
                    f"Required: {count}, Available: {len(picked)}."
                )
            selected.extend(picked)
            current_excludes.extend([q.id for q in picked])

        return selected

    def _select_by_bloom_distribution(
        self,
        subject_id: str,
        rule: BlueprintRule,
        bloom_dist: Dict[str, int],
        exclude_ids: List[str],
        rng: random.Random
    ) -> List[Question]:
        selected: List[Question] = []
        current_excludes = list(exclude_ids)

        for bloom_str, count in bloom_dist.items():
            if count <= 0:
                continue
            try:
                bloom_enum = BloomLevelEnum(bloom_str)
            except ValueError:
                continue

            candidates = self.eligibility_service.get_eligible_questions_for_rule(
                subject_id=subject_id,
                rule=rule,
                bloom_level=bloom_enum,
                exclude_question_ids=current_excludes
            )

            picked = self._pick_least_exposed(candidates, count, rng)
            if len(picked) < count:
                raise ValueError(
                    f"Insufficient questions for section '{rule.section}' with Bloom level '{bloom_str}'. "
                    f"Required: {count}, Available: {len(picked)}."
                )
            selected.extend(picked)
            current_excludes.extend([q.id for q in picked])

        return selected

    def _select_by_unit_distribution(
        self,
        subject_id: str,
        rule: BlueprintRule,
        unit_dist: Dict[str, int],
        exclude_ids: List[str],
        rng: random.Random
    ) -> List[Question]:
        selected: List[Question] = []
        current_excludes = list(exclude_ids)

        for unit_id, count in unit_dist.items():
            if count <= 0:
                continue

            candidates = self.eligibility_service.get_eligible_questions_for_rule(
                subject_id=subject_id,
                rule=rule,
                unit_id=unit_id,
                exclude_question_ids=current_excludes
            )

            picked = self._pick_least_exposed(candidates, count, rng)
            if len(picked) < count:
                raise ValueError(
                    f"Insufficient questions for section '{rule.section}' in Unit ID '{unit_id}'. "
                    f"Required: {count}, Available: {len(picked)}."
                )
            selected.extend(picked)
            current_excludes.extend([q.id for q in picked])

        return selected

    def _pick_least_exposed(
        self,
        candidates: List[Question],
        count: int,
        rng: random.Random
    ) -> List[Question]:
        if not candidates or count <= 0:
            return []

        c_ids = [q.id for q in candidates]
        exposure_map = self.exposure_service.get_exposure_counts(c_ids)

        # Sort candidates by exposure_map value ascending, then by ID for stability
        sorted_candidates = sorted(candidates, key=lambda q: (exposure_map.get(q.id, 0), q.id))

        # Group by exposure level and shuffle within the same exposure level using rng
        # Or simple deterministic shuffle weighted by exposure level:
        exposure_groups: Dict[int, List[Question]] = {}
        for q in sorted_candidates:
            exp = exposure_map.get(q.id, 0)
            exposure_groups.setdefault(exp, []).append(q)

        selected: List[Question] = []
        for exp in sorted(exposure_groups.keys()):
            group = exposure_groups[exp]
            rng.shuffle(group) # Seeded shuffle
            for q in group:
                selected.append(q)
                if len(selected) == count:
                    return selected

        return selected
