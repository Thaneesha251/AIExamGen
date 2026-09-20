import re
import math
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

try:
    from app.db.models import (
        AnswerPaper, ExtractedAnswer, QuestionPaperVersion, QuestionPaperItem,
        AnswerKey, AnswerKeyItem, Rubric, RubricCriterion, Evaluation, EvaluationItem,
        FacultyReview, ReviewActionEnum, EvaluatorTypeEnum, EvaluationStatusEnum, AnswerPaperStatusEnum, AuditActionEnum
    )
except ImportError:
    from backend.app.db.models import (
        AnswerPaper, ExtractedAnswer, QuestionPaperVersion, QuestionPaperItem,
        AnswerKey, AnswerKeyItem, Rubric, RubricCriterion, Evaluation, EvaluationItem,
        FacultyReview, ReviewActionEnum, EvaluatorTypeEnum, EvaluationStatusEnum, AnswerPaperStatusEnum, AuditActionEnum
    )

from ai.services.embedding_service import LocalEmbeddingService
from ai.services.similarity_service import QuestionSimilarityService
from ai.agents.answer_evaluation_agent import AnswerEvaluationAgent
from backend.app.services.audit_service import AuditLogService

CONFIDENCE_THRESHOLD = 0.65

class AnswerEvaluationService:
    """Core AI answer evaluation engine supporting multi-layer scoring, rubric parsing, and confidence calculation."""

    def __init__(self, db: Session, evaluation_agent: Optional[AnswerEvaluationAgent] = None):
        self.db = db
        self.evaluation_agent = evaluation_agent or AnswerEvaluationAgent()
        self.similarity_service = QuestionSimilarityService()
        self.audit_service = AuditLogService(db)

    async def evaluate_answer_paper(self, answer_paper_id: str, evaluator_user_id: Optional[str] = None) -> Evaluation:
        """Executes multi-layer evaluation pipeline for an entire student answer paper."""
        answer_paper = self.db.query(AnswerPaper).filter(AnswerPaper.id == answer_paper_id).first()
        if not answer_paper:
            raise HTTPException(status_code=404, detail="Answer paper not found.")

        # Validate examination and version integrity
        exam = answer_paper.examination
        if not exam:
            raise HTTPException(status_code=400, detail="Answer paper is not associated with an examination.")

        if not exam.question_paper_version_id:
            raise HTTPException(status_code=400, detail="Examination does not have an attached published QuestionPaperVersion.")

        qp_version = self.db.query(QuestionPaperVersion).filter(
            QuestionPaperVersion.id == exam.question_paper_version_id
        ).first()

        if not qp_version:
            raise HTTPException(status_code=404, detail="Question paper version record not found.")

        # Find answer key belonging to this exact question paper version
        answer_key = self.db.query(AnswerKey).filter(
            AnswerKey.question_paper_version_id == qp_version.id
        ).first()

        if not answer_key:
            raise HTTPException(
                status_code=400,
                detail=f"No AnswerKey found for QuestionPaperVersion '{qp_version.id}'. Evaluation blocked."
            )

        # Determine evaluation version (increment if paper re-evaluated)
        existing_evals = self.db.query(Evaluation).filter(
            Evaluation.answer_paper_id == answer_paper_id
        ).all()
        new_version = max([e.version for e in existing_evals] or [0]) + 1

        # Create new Evaluation record
        evaluation = Evaluation(
            examination_id=exam.id,
            answer_paper_id=answer_paper.id,
            student_id=answer_paper.student_id,
            version=new_version,
            evaluator_type=EvaluatorTypeEnum.AI,
            status=EvaluationStatusEnum.PROCESSING,
            started_at=datetime.now(timezone.utc).isoformat()
        )
        self.db.add(evaluation)
        self.db.flush()

        # Build items map
        qp_items = qp_version.items
        answer_key_items_map = {item.question_paper_item_id: item for item in answer_key.items if item.question_paper_item_id}

        extracted_answers_map: Dict[str, ExtractedAnswer] = {}
        for ext_ans in answer_paper.extracted_answers:
            if ext_ans.question_paper_item_id:
                extracted_answers_map[ext_ans.question_paper_item_id] = ext_ans

        total_ai_marks = 0.0
        total_max_marks = 0.0
        confidence_scores = []
        requires_review = False

        # Evaluate each QuestionPaperItem
        for qp_item in sorted(qp_items, key=lambda x: getattr(x, 'order_index', getattr(x, 'sequence_number', 0))):
            extracted_ans = extracted_answers_map.get(qp_item.id)
            ak_item = answer_key_items_map.get(qp_item.id)

            eval_item = await self._evaluate_single_item(
                evaluation_id=evaluation.id,
                qp_item=qp_item,
                ak_item=ak_item,
                extracted_ans=extracted_ans
            )
            self.db.add(eval_item)

            total_ai_marks += (eval_item.ai_marks or 0.0)
            total_max_marks += qp_item.marks
            if eval_item.confidence is not None:
                confidence_scores.append(eval_item.confidence)

            if eval_item.requires_faculty_review:
                requires_review = True

        avg_confidence = (sum(confidence_scores) / len(confidence_scores)) if confidence_scores else 0.85

        evaluation.total_ai_marks = round(total_ai_marks, 2)
        evaluation.total_final_marks = round(total_ai_marks, 2)
        evaluation.overall_confidence = round(avg_confidence, 4)
        evaluation.requires_review = requires_review
        evaluation.status = EvaluationStatusEnum.COMPLETED
        evaluation.completed_at = datetime.now(timezone.utc).isoformat()

        # Update AnswerPaper status
        answer_paper.status = AnswerPaperStatusEnum.EVALUATED if not requires_review else AnswerPaperStatusEnum.UNDER_REVIEW
        answer_paper.processed_at = datetime.now(timezone.utc).isoformat()

        self.db.commit()
        self.db.refresh(evaluation)

        self.audit_service.log_action(
            action=AuditActionEnum.RUN_EVALUATION,
            user_id=evaluator_user_id or answer_paper.student_id,
            entity_type="Evaluation",
            entity_id=evaluation.id,
            details={
                "version": new_version,
                "total_ai_marks": evaluation.total_ai_marks,
                "overall_confidence": evaluation.overall_confidence,
                "requires_review": requires_review
            }
        )

        return evaluation

    async def reevaluate_single_item(
        self,
        evaluation_id: str,
        item_id: str,
        faculty_user_id: str
    ) -> EvaluationItem:
        """Re-evaluates a single question item within an evaluation."""
        eval_item = self.db.query(EvaluationItem).filter(
            EvaluationItem.id == item_id,
            EvaluationItem.evaluation_id == evaluation_id
        ).first()

        if not eval_item:
            raise HTTPException(status_code=404, detail="Evaluation item not found.")

        qp_item = eval_item.question_paper_item
        extracted_ans = eval_item.extracted_answer

        # Find answer key item
        evaluation = eval_item.evaluation
        exam = evaluation.examination
        qp_version = self.db.query(QuestionPaperVersion).filter(QuestionPaperVersion.id == exam.question_paper_version_id).first()
        answer_key = self.db.query(AnswerKey).filter(AnswerKey.question_paper_version_id == qp_version.id).first() if qp_version else None
        ak_item = next((i for i in answer_key.items if i.question_paper_item_id == qp_item.id), None) if answer_key else None

        updated_item = await self._evaluate_single_item(
            evaluation_id=evaluation_id,
            qp_item=qp_item,
            ak_item=ak_item,
            extracted_ans=extracted_ans
        )

        # Update fields on pre-existing item to preserve foreign keys
        eval_item.keyword_score = updated_item.keyword_score
        eval_item.concept_score = updated_item.concept_score
        eval_item.semantic_score = updated_item.semantic_score
        eval_item.pattern_score = updated_item.pattern_score
        eval_item.rubric_score = updated_item.rubric_score
        eval_item.ai_score = updated_item.ai_score
        eval_item.ai_marks = updated_item.ai_marks
        eval_item.final_marks = updated_item.final_marks
        eval_item.confidence = updated_item.confidence
        eval_item.matched_keywords = updated_item.matched_keywords
        eval_item.missing_keywords = updated_item.missing_keywords
        eval_item.matched_concepts = updated_item.matched_concepts
        eval_item.missing_concepts = updated_item.missing_concepts
        eval_item.strengths = updated_item.strengths
        eval_item.missing_points = updated_item.missing_points
        eval_item.criterion_scores = updated_item.criterion_scores
        eval_item.requires_faculty_review = updated_item.requires_faculty_review
        eval_item.review_reason = updated_item.review_reason
        eval_item.evaluation_explanation = updated_item.evaluation_explanation

        self.db.commit()
        self.db.refresh(eval_item)

        self.audit_service.log_action(
            action=AuditActionEnum.FACULTY_OVERRIDE,
            user_id=faculty_user_id,
            entity_type="EvaluationItem",
            entity_id=eval_item.id,
            details={"action": "REEVALUATE_SINGLE_ITEM", "ai_marks": eval_item.ai_marks}
        )

        return eval_item

    async def _evaluate_single_item(
        self,
        evaluation_id: str,
        qp_item: QuestionPaperItem,
        ak_item: Optional[AnswerKeyItem],
        extracted_ans: Optional[ExtractedAnswer]
    ) -> EvaluationItem:
        """Core multi-layer evaluation calculation for a single QuestionPaperItem."""
        max_marks = float(qp_item.marks)
        q_text = qp_item.question.question_text if qp_item.question else qp_item.item_label or "Question"
        q_type = (qp_item.question.question_type.value if qp_item.question and hasattr(qp_item.question.question_type, 'value') else "DESCRIPTIVE").upper()

        student_text = extracted_ans.extracted_text.strip() if extracted_ans and extracted_ans.extracted_text else ""
        ocr_conf = extracted_ans.ocr_confidence if extracted_ans and extracted_ans.ocr_confidence is not None else 0.90
        seg_conf = extracted_ans.segmentation_confidence if extracted_ans and extracted_ans.segmentation_confidence is not None else 0.90

        # Check blank/unanswered question
        if not student_text:
            return EvaluationItem(
                evaluation_id=evaluation_id,
                question_paper_item_id=qp_item.id,
                extracted_answer_id=extracted_ans.id if extracted_ans else None,
                maximum_marks=max_marks,
                keyword_score=0.0,
                concept_score=0.0,
                semantic_score=0.0,
                pattern_score=0.0,
                rubric_score=0.0,
                ai_score=0.0,
                ai_marks=0.0,
                final_marks=0.0,
                confidence=1.0,
                matched_keywords={"keywords": []},
                missing_keywords={"keywords": ak_item.keywords if ak_item and ak_item.keywords else []},
                matched_concepts={"concepts": []},
                missing_concepts={"concepts": ak_item.concepts if ak_item and ak_item.concepts else []},
                strengths={"strengths": []},
                missing_points={"missing": ["No answer submitted"]},
                requires_faculty_review=False,
                evaluation_explanation="No student answer detected. Awarded 0 marks."
            )

        model_answer = ak_item.model_answer if ak_item and ak_item.model_answer else (qp_item.question.expected_answer if qp_item.question and qp_item.question.expected_answer else "")
        expected_keywords = ak_item.keywords if ak_item and ak_item.keywords else (qp_item.question.keywords if qp_item.question and qp_item.question.keywords else [])
        expected_concepts = ak_item.concepts if ak_item and ak_item.concepts else (qp_item.question.concepts if qp_item.question and qp_item.question.concepts else [])

        # 1. Deterministic Strategy for MCQ / True-False / Fill-Blank
        if q_type in ["MCQ", "TRUE_FALSE"]:
            correct_option = model_answer.strip().lower()
            student_option = student_text.strip().lower()
            is_correct = (student_option == correct_option or (len(correct_option) > 0 and correct_option in student_option))
            awarded = max_marks if is_correct else 0.0

            return EvaluationItem(
                evaluation_id=evaluation_id,
                question_paper_item_id=qp_item.id,
                extracted_answer_id=extracted_ans.id if extracted_ans else None,
                maximum_marks=max_marks,
                keyword_score=1.0 if is_correct else 0.0,
                concept_score=1.0 if is_correct else 0.0,
                semantic_score=1.0 if is_correct else 0.0,
                pattern_score=1.0 if is_correct else 0.0,
                rubric_score=1.0 if is_correct else 0.0,
                ai_score=1.0 if is_correct else 0.0,
                ai_marks=awarded,
                final_marks=awarded,
                confidence=1.0,
                matched_keywords={"keywords": [student_text] if is_correct else []},
                missing_keywords={"keywords": [model_answer] if not is_correct else []},
                matched_concepts={"concepts": []},
                missing_concepts={"concepts": []},
                strengths={"strengths": ["Selected option matches correct answer"] if is_correct else []},
                missing_points={"missing": ["Selected option is incorrect"] if not is_correct else []},
                requires_faculty_review=False,
                evaluation_explanation=f"Deterministic {q_type} option match: {'Correct' if is_correct else 'Incorrect'}."
            )

        # 2. Keyword Score Layer
        matched_kw, missing_kw, kw_score = self._evaluate_keywords(student_text, expected_keywords)

        # 3. Concept Score Layer
        matched_cp, missing_cp, cp_score = self._evaluate_concepts(student_text, expected_concepts)

        # 4. Semantic Similarity Layer
        sem_score = self.similarity_service.calculate_similarity(student_text, model_answer) if model_answer else 0.70

        # 5. Pattern / Structure Layer
        pat_score = self._evaluate_pattern_structure(student_text, q_type)

        # 6. Rubric Layer
        rubric_score, criterion_scores_list = self._evaluate_rubric(student_text, ak_item)

        # 7. AI Qualitative Agent Layer
        deterministic_metrics = {
            "keyword_score": kw_score,
            "concept_score": cp_score,
            "semantic_score": sem_score,
            "pattern_score": pat_score,
            "rubric_score": rubric_score,
            "composite_deterministic_score": round((kw_score + cp_score + sem_score + pat_score + rubric_score) / 5.0, 4),
            "confidence_estimate": round((ocr_conf + seg_conf) / 2.0, 4)
        }

        rubric_criteria_dict = []
        if ak_item and ak_item.rubric and ak_item.rubric.criteria:
            rubric_criteria_dict = [
                {
                    "id": c.id,
                    "title": getattr(c, 'criterion', getattr(c, 'criterion_title', 'Criterion')),
                    "max_marks": getattr(c, 'marks', getattr(c, 'max_marks', 2.0))
                } for c in ak_item.rubric.criteria
            ]

        ai_agent_result = await self.evaluation_agent.evaluate_answer(
            question_text=q_text,
            question_type=q_type,
            maximum_marks=max_marks,
            model_answer=model_answer,
            keywords=expected_keywords,
            concepts=expected_concepts,
            rubric_criteria=rubric_criteria_dict,
            student_answer_text=student_text,
            deterministic_metrics=deterministic_metrics
        )

        ai_agent_score = ai_agent_result["suggested_marks"] / max_marks if max_marks > 0 else 0.0

        # 8. Composite Weighted Final Marks Calculation
        weighted_score = (
            (0.15 * kw_score) +
            (0.25 * cp_score) +
            (0.25 * sem_score) +
            (0.10 * pat_score) +
            (0.15 * rubric_score) +
            (0.10 * ai_agent_score)
        )
        weighted_score = max(0.0, min(weighted_score, 1.0))
        ai_marks = round(weighted_score * max_marks, 2)

        # 9. Composite Evidence Confidence Metric
        layer_variance = self._calculate_score_variance([kw_score, cp_score, sem_score, ai_agent_score])
        agreement_factor = max(0.0, 1.0 - (layer_variance * 2.0))
        item_confidence = round((0.40 * ocr_conf) + (0.30 * seg_conf) + (0.30 * agreement_factor), 4)

        # Flag for review if confidence < threshold or OCR low confidence
        requires_review = (item_confidence < CONFIDENCE_THRESHOLD) or (ocr_conf < 0.70) or (extracted_ans is None)
        review_reason = None
        if item_confidence < CONFIDENCE_THRESHOLD:
            review_reason = f"Low composite confidence ({item_confidence * 100:.0f}%)"
        elif ocr_conf < 0.70:
            review_reason = f"Low page OCR confidence ({ocr_conf * 100:.0f}%)"
        elif extracted_ans is None:
            review_reason = "Answer question mapping unverified"

        return EvaluationItem(
            evaluation_id=evaluation_id,
            question_paper_item_id=qp_item.id,
            extracted_answer_id=extracted_ans.id if extracted_ans else None,
            maximum_marks=max_marks,
            keyword_score=round(kw_score, 4),
            concept_score=round(cp_score, 4),
            semantic_score=round(sem_score, 4),
            pattern_score=round(pat_score, 4),
            rubric_score=round(rubric_score, 4),
            ai_score=round(weighted_score, 4),
            ai_marks=ai_marks,
            final_marks=ai_marks,
            confidence=item_confidence,
            matched_keywords={"keywords": matched_kw},
            missing_keywords={"keywords": missing_kw},
            matched_concepts={"concepts": matched_cp},
            missing_concepts={"concepts": missing_cp},
            strengths={"strengths": ai_agent_result.get("strengths", [])},
            missing_points={"missing": ai_agent_result.get("missing_points", [])},
            criterion_scores={"criteria": criterion_scores_list},
            requires_faculty_review=requires_review,
            review_reason=review_reason,
            prompt_version=ai_agent_result.get("prompt_version", "v1"),
            evaluation_explanation=ai_agent_result.get("reasoning_summary", "Multi-layer AI evaluation completed.")
        )

    def _evaluate_keywords(self, student_text: str, keywords: List[str]) -> Tuple[List[str], List[str], float]:
        if not keywords:
            return [], [], 0.85

        text_lower = student_text.lower()
        matched = []
        missing = []

        for kw in keywords:
            kw_clean = kw.strip().lower()
            if kw_clean and kw_clean in text_lower:
                matched.append(kw)
            else:
                missing.append(kw)

        ratio = len(matched) / len(keywords) if keywords else 1.0
        return matched, missing, round(ratio, 4)

    def _evaluate_concepts(self, student_text: str, concepts: List[str]) -> Tuple[List[str], List[str], float]:
        if not concepts:
            return [], [], 0.85

        matched = []
        missing = []

        for cp in concepts:
            cp_clean = cp.strip().lower()
            sim = LocalEmbeddingService.cosine_similarity(student_text, cp_clean)
            words = [w for w in cp_clean.split() if len(w) >= 4]
            word_match = any(w[:4] in student_text.lower() for w in words) if words else False
            if sim >= 0.30 or cp_clean in student_text.lower() or word_match:
                matched.append(cp)
            else:
                missing.append(cp)


        ratio = len(matched) / len(concepts) if concepts else 1.0
        return matched, missing, round(ratio, 4)

    def _evaluate_pattern_structure(self, student_text: str, q_type: str) -> float:
        words = student_text.split()
        word_count = len(words)

        if q_type == "SHORT_ANSWER":
            if word_count >= 15:
                return 1.0
            return max(0.4, word_count / 15.0)
        elif q_type in ["DESCRIPTIVE", "CASE_STUDY"]:
            if word_count >= 40:
                return 1.0
            return max(0.3, word_count / 40.0)
        elif q_type == "NUMERICAL":
            # Check presence of numbers and equations
            has_numbers = bool(re.search(r'\d+', student_text))
            return 1.0 if has_numbers else 0.5
        return 0.85

    def _evaluate_rubric(self, student_text: str, ak_item: Optional[AnswerKeyItem]) -> Tuple[float, List[Dict[str, Any]]]:
        if not ak_item or not ak_item.rubric or not ak_item.rubric.criteria:
            return 0.85, []

        criteria_list = ak_item.rubric.criteria
        total_rubric_max = sum([getattr(c, 'marks', getattr(c, 'max_marks', 2.0)) for c in criteria_list]) or 1.0
        awarded_total = 0.0
        criterion_scores = []

        for crit in criteria_list:
            crit_max = float(getattr(crit, 'marks', getattr(crit, 'max_marks', 2.0)))
            crit_title = getattr(crit, 'criterion', getattr(crit, 'criterion_title', 'Criterion'))

            # Check keyword match against criterion description
            sim = LocalEmbeddingService.cosine_similarity(student_text, crit.description or crit_title)
            if sim >= 0.50:
                awarded = crit_max
            elif sim >= 0.25:
                awarded = round(crit_max * 0.5, 2)
            else:
                awarded = round(crit_max * 0.2, 2)

            awarded_total += awarded
            criterion_scores.append({
                "criterion_id": crit.id,
                "title": crit_title,
                "max_marks": crit_max,
                "awarded_marks": awarded,
                "feedback": f"Match similarity {sim*100:.0f}%"
            })

        score_ratio = awarded_total / total_rubric_max if total_rubric_max > 0 else 1.0
        return round(score_ratio, 4), criterion_scores


    def _calculate_score_variance(self, scores: List[float]) -> float:
        if not scores or len(scores) < 2:
            return 0.0
        mean = sum(scores) / len(scores)
        variance = sum((s - mean) ** 2 for s in scores) / len(scores)
        return float(variance)

    def accept_item_ai_mark(
        self,
        evaluation_id: str,
        item_id: str,
        faculty_user_id: str,
        comment: Optional[str] = None
    ) -> EvaluationItem:
        eval_record = self.db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
        if not eval_record:
            raise HTTPException(status_code=404, detail="Evaluation record not found.")

        if eval_record.status == EvaluationStatusEnum.FINALIZED:
            raise HTTPException(status_code=400, detail="Evaluation is finalized and locked from modification.")

        item = self.db.query(EvaluationItem).filter(
            EvaluationItem.id == item_id,
            EvaluationItem.evaluation_id == evaluation_id
        ).first()
        if not item:
            raise HTTPException(status_code=404, detail="Evaluation item not found.")

        original_ai_marks = item.ai_marks or 0.0
        item.final_marks = original_ai_marks
        item.review_status = "ACCEPTED"
        item.faculty_comment = comment
        item.reviewed_by = faculty_user_id
        item.reviewed_at = datetime.now(timezone.utc).isoformat()

        self._recalculate_evaluation_totals(eval_record, faculty_user_id)

        review = FacultyReview(
            evaluation_id=eval_record.id,
            evaluation_item_id=item.id,
            faculty_id=faculty_user_id,
            original_ai_marks=original_ai_marks,
            revised_marks=original_ai_marks,
            comment=comment,
            action=ReviewActionEnum.ACCEPT_AI_MARK,
            reviewed_at=datetime.now(timezone.utc).isoformat()
        )
        self.db.add(review)
        self.db.commit()
        self.db.refresh(item)

        self.audit_service.log_action(
            action=AuditActionEnum.AI_MARK_ACCEPTED,
            user_id=faculty_user_id,
            entity_type="EvaluationItem",
            entity_id=item.id,
            details={"evaluation_id": evaluation_id, "accepted_marks": original_ai_marks}
        )
        return item

    def override_item_mark(
        self,
        evaluation_id: str,
        item_id: str,
        faculty_user_id: str,
        final_marks: float,
        reason: str,
        comment: Optional[str] = None
    ) -> EvaluationItem:
        eval_record = self.db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
        if not eval_record:
            raise HTTPException(status_code=404, detail="Evaluation record not found.")

        if eval_record.status == EvaluationStatusEnum.FINALIZED:
            raise HTTPException(status_code=400, detail="Evaluation is finalized and locked from modification.")

        item = self.db.query(EvaluationItem).filter(
            EvaluationItem.id == item_id,
            EvaluationItem.evaluation_id == evaluation_id
        ).first()
        if not item:
            raise HTTPException(status_code=404, detail="Evaluation item not found.")

        if not reason or len(reason.strip()) < 10:
            raise HTTPException(status_code=400, detail="Override reason is mandatory and must be at least 10 characters long.")

        if final_marks < 0.0 or final_marks > item.maximum_marks:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid final marks ({final_marks}). Must be between 0.0 and maximum marks ({item.maximum_marks})."
            )

        original_ai_marks = item.ai_marks or 0.0
        item.final_marks = round(final_marks, 2)
        item.review_status = "OVERRIDDEN"
        item.override_reason = reason.strip()
        item.faculty_comment = comment
        item.reviewed_by = faculty_user_id
        item.reviewed_at = datetime.now(timezone.utc).isoformat()

        self._recalculate_evaluation_totals(eval_record, faculty_user_id)

        review = FacultyReview(
            evaluation_id=eval_record.id,
            evaluation_item_id=item.id,
            faculty_id=faculty_user_id,
            original_ai_marks=original_ai_marks,
            revised_marks=round(final_marks, 2),
            reason=reason.strip(),
            comment=comment,
            action=ReviewActionEnum.OVERRIDE_MARK,
            reviewed_at=datetime.now(timezone.utc).isoformat()
        )
        self.db.add(review)
        self.db.commit()
        self.db.refresh(item)

        self.audit_service.log_action(
            action=AuditActionEnum.MARK_OVERRIDDEN,
            user_id=faculty_user_id,
            entity_type="EvaluationItem",
            entity_id=item.id,
            details={
                "evaluation_id": evaluation_id,
                "original_ai_marks": original_ai_marks,
                "revised_marks": final_marks,
                "reason": reason.strip()
            }
        )
        return item

    def bulk_accept_high_confidence(
        self,
        evaluation_id: str,
        faculty_user_id: str,
        confidence_threshold: float = 0.65
    ) -> Dict[str, Any]:
        eval_record = self.db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
        if not eval_record:
            raise HTTPException(status_code=404, detail="Evaluation record not found.")

        if eval_record.status == EvaluationStatusEnum.FINALIZED:
            raise HTTPException(status_code=400, detail="Evaluation is finalized and locked from modification.")

        accepted_count = 0
        skipped_count = 0

        for item in eval_record.items:
            if (item.confidence or 0.0) >= confidence_threshold and not item.requires_faculty_review and (item.review_status is None or item.review_status == "PENDING"):
                original_ai_marks = item.ai_marks or 0.0
                item.final_marks = original_ai_marks
                item.review_status = "ACCEPTED"
                item.reviewed_by = faculty_user_id
                item.reviewed_at = datetime.now(timezone.utc).isoformat()

                review = FacultyReview(
                    evaluation_id=eval_record.id,
                    evaluation_item_id=item.id,
                    faculty_id=faculty_user_id,
                    original_ai_marks=original_ai_marks,
                    revised_marks=original_ai_marks,
                    comment="Bulk accepted high-confidence AI mark",
                    action=ReviewActionEnum.BULK_ACCEPT,
                    reviewed_at=datetime.now(timezone.utc).isoformat()
                )
                self.db.add(review)
                accepted_count += 1
            else:
                skipped_count += 1

        self._recalculate_evaluation_totals(eval_record, faculty_user_id)
        self.db.commit()

        self.audit_service.log_action(
            action=AuditActionEnum.BULK_AI_MARKS_ACCEPTED,
            user_id=faculty_user_id,
            entity_type="Evaluation",
            entity_id=evaluation_id,
            details={"accepted_count": accepted_count, "skipped_count": skipped_count}
        )

        return {
            "evaluation_id": evaluation_id,
            "accepted_count": accepted_count,
            "skipped_count": skipped_count,
            "total_items": len(eval_record.items)
        }

    def approve_evaluation(
        self,
        evaluation_id: str,
        faculty_user_id: str,
        notes: Optional[str] = None
    ) -> Evaluation:
        eval_record = self.db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
        if not eval_record:
            raise HTTPException(status_code=404, detail="Evaluation record not found.")

        if eval_record.status == EvaluationStatusEnum.FINALIZED:
            raise HTTPException(status_code=400, detail="Evaluation is already finalized.")

        unreviewed_items = [it for it in eval_record.items if (it.review_status is None or it.review_status == "PENDING")]
        if unreviewed_items:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot approve evaluation. {len(unreviewed_items)} item(s) are still pending faculty decision."
            )

        self._recalculate_evaluation_totals(eval_record, faculty_user_id)
        eval_record.status = EvaluationStatusEnum.APPROVED
        eval_record.approved_by = faculty_user_id
        eval_record.approved_at = datetime.now(timezone.utc).isoformat()
        eval_record.review_notes = notes

        review = FacultyReview(
            evaluation_id=eval_record.id,
            faculty_id=faculty_user_id,
            revised_marks=eval_record.total_final_marks or 0.0,
            comment=notes or "Evaluation approved by faculty",
            action=ReviewActionEnum.APPROVE,
            reviewed_at=datetime.now(timezone.utc).isoformat()
        )
        self.db.add(review)
        self.db.commit()
        self.db.refresh(eval_record)

        self.audit_service.log_action(
            action=AuditActionEnum.EVALUATION_APPROVED,
            user_id=faculty_user_id,
            entity_type="Evaluation",
            entity_id=eval_record.id,
            details={"total_final_marks": eval_record.total_final_marks}
        )
        return eval_record

    def finalize_evaluation(
        self,
        evaluation_id: str,
        faculty_user_id: str,
        notes: Optional[str] = None
    ) -> Evaluation:
        eval_record = self.db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
        if not eval_record:
            raise HTTPException(status_code=404, detail="Evaluation record not found.")

        if eval_record.status == EvaluationStatusEnum.FINALIZED:
            raise HTTPException(status_code=400, detail="Evaluation is already finalized.")

        unreviewed_items = [it for it in eval_record.items if (it.review_status is None or it.review_status == "PENDING")]
        if unreviewed_items:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot finalize evaluation. {len(unreviewed_items)} item(s) are still pending faculty decision."
            )

        self._recalculate_evaluation_totals(eval_record, faculty_user_id)
        eval_record.status = EvaluationStatusEnum.FINALIZED
        eval_record.finalized_by = faculty_user_id
        eval_record.finalized_at = datetime.now(timezone.utc).isoformat()
        eval_record.finalization_notes = notes

        if eval_record.answer_paper:
            eval_record.answer_paper.status = AnswerPaperStatusEnum.FINALIZED

        review = FacultyReview(
            evaluation_id=eval_record.id,
            faculty_id=faculty_user_id,
            revised_marks=eval_record.total_final_marks or 0.0,
            comment=notes or "Evaluation finalized",
            action=ReviewActionEnum.FINALIZE,
            reviewed_at=datetime.now(timezone.utc).isoformat()
        )
        self.db.add(review)
        self.db.commit()
        self.db.refresh(eval_record)

        self.audit_service.log_action(
            action=AuditActionEnum.EVALUATION_FINALIZED,
            user_id=faculty_user_id,
            entity_type="Evaluation",
            entity_id=eval_record.id,
            details={"total_final_marks": eval_record.total_final_marks}
        )
        return eval_record

    def reopen_evaluation(
        self,
        evaluation_id: str,
        admin_user_id: str,
        reason: str
    ) -> Evaluation:
        eval_record = self.db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
        if not eval_record:
            raise HTTPException(status_code=404, detail="Evaluation record not found.")

        if not reason or len(reason.strip()) < 10:
            raise HTTPException(status_code=400, detail="Administrative reopening reason is mandatory and must be at least 10 characters long.")

        eval_record.status = EvaluationStatusEnum.REOPENED
        if eval_record.answer_paper:
            eval_record.answer_paper.status = AnswerPaperStatusEnum.UNDER_REVIEW

        review = FacultyReview(
            evaluation_id=eval_record.id,
            faculty_id=admin_user_id,
            revised_marks=eval_record.total_final_marks or 0.0,
            reason=reason.strip(),
            comment=f"Finalized evaluation reopened by admin: {reason.strip()}",
            action=ReviewActionEnum.REOPEN,
            reviewed_at=datetime.now(timezone.utc).isoformat()
        )
        self.db.add(review)
        self.db.commit()
        self.db.refresh(eval_record)

        self.audit_service.log_action(
            action=AuditActionEnum.EVALUATION_REOPENED,
            user_id=admin_user_id,
            entity_type="Evaluation",
            entity_id=eval_record.id,
            details={"reason": reason.strip()}
        )
        return eval_record

    def get_evaluation_reviews(self, evaluation_id: str) -> List[FacultyReview]:
        eval_record = self.db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
        if not eval_record:
            raise HTTPException(status_code=404, detail="Evaluation record not found.")

        return self.db.query(FacultyReview).filter(
            FacultyReview.evaluation_id == evaluation_id
        ).order_by(FacultyReview.created_at.asc()).all()

    def _recalculate_evaluation_totals(self, evaluation: Evaluation, faculty_user_id: str) -> None:
        total_final = sum([item.final_marks for item in evaluation.items if item.final_marks is not None])
        evaluation.total_final_marks = round(total_final, 2)
        evaluation.reviewed_by = faculty_user_id
        evaluation.reviewed_at = datetime.now(timezone.utc).isoformat()
        if evaluation.status in [EvaluationStatusEnum.COMPLETED, EvaluationStatusEnum.PENDING]:
            evaluation.status = EvaluationStatusEnum.UNDER_REVIEW
