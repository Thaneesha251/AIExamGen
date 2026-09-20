import datetime
import statistics
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from fastapi import HTTPException, status

from backend.app.core.quality_config import (
    QUESTION_DIFFICULTY_EASY_THRESHOLD,
    QUESTION_DIFFICULTY_MODERATE_THRESHOLD,
    DISCRIMINATION_STRONG_THRESHOLD,
    DISCRIMINATION_ACCEPTABLE_THRESHOLD,
    DISCRIMINATION_WEAK_THRESHOLD,
    MINIMUM_COHORT_SIZE_FOR_DISCRIMINATION,
    DISCRIMINATION_TOP_BOTTOM_PERCENTILE,
    BLUEPRINT_VARIANCE_TOLERANCE
)

from backend.app.db.models import (
    Examination, ExaminationStudent, AnswerPaper, Evaluation, EvaluationItem,
    EvaluationStatusEnum, Question, QuestionPaper, QuestionPaperVersion, QuestionPaperItem,
    Blueprint, BlueprintRule, Unit, Topic, LearningOutcome, User, Subject,
    AnswerSimilarity, PlagiarismResult, QuestionQualityReview, AuditLog, AuditActionEnum
)


class QuestionQualityService:
    """Service providing question quality analytics, discrimination analysis, blueprint balance, and question bank insights."""

    def __init__(self, db: Session):
        self.db = db

    def _get_finalized_evaluations_for_exam(self, examination_id: str) -> List[Evaluation]:
        """Retrieves strictly FINALIZED evaluations for an examination."""
        finalized_status = EvaluationStatusEnum.FINALIZED.value if hasattr(EvaluationStatusEnum.FINALIZED, 'value') else "FINALIZED"
        return (
            self.db.query(Evaluation)
            .join(AnswerPaper, Evaluation.answer_paper_id == AnswerPaper.id)
            .filter(
                AnswerPaper.examination_id == examination_id,
                Evaluation.status == finalized_status
            )
            .all()
        )

    def get_question_performance_analysis(self, examination_id: str, question_id: str) -> Dict[str, Any]:
        """Calculates normalized performance statistics for a specific question in an examination."""
        finalized_evals = self._get_finalized_evaluations_for_exam(examination_id)
        if not finalized_evals:
            return {
                "question_id": question_id,
                "total_responses": 0,
                "valid_responses": 0,
                "average_marks": 0.0,
                "max_marks": 10.0,
                "average_percentage": 0.0,
                "minimum_marks": 0.0,
                "highest_marks": 0.0,
                "full_mark_percentage": 0.0,
                "zero_mark_percentage": 0.0,
                "partial_mark_percentage": 0.0
            }

        eval_ids = [e.id for e in finalized_evals]
        items = (
            self.db.query(EvaluationItem)
            .join(QuestionPaperItem, EvaluationItem.question_paper_item_id == QuestionPaperItem.id)
            .filter(
                EvaluationItem.evaluation_id.in_(eval_ids),
                QuestionPaperItem.question_id == question_id
            )
            .all()
        )

        if not items:
            return {
                "question_id": question_id,
                "total_responses": 0,
                "valid_responses": 0,
                "average_marks": 0.0,
                "max_marks": 10.0,
                "average_percentage": 0.0,
                "minimum_marks": 0.0,
                "highest_marks": 0.0,
                "full_mark_percentage": 0.0,
                "zero_mark_percentage": 0.0,
                "partial_mark_percentage": 0.0
            }

        raw_marks = []
        normalized_scores = []
        max_m = items[0].maximum_marks if (items[0].maximum_marks and items[0].maximum_marks > 0) else 10.0

        full_count = 0
        zero_count = 0
        partial_count = 0

        for item in items:
            mark = item.final_marks if item.final_marks is not None else (item.ai_marks if item.ai_marks is not None else 0.0)
            item_max = item.maximum_marks if (item.maximum_marks and item.maximum_marks > 0) else max_m
            norm = mark / item_max if item_max > 0 else 0.0

            raw_marks.append(mark)
            normalized_scores.append(norm)

            if norm >= 0.999:
                full_count += 1
            elif norm <= 0.001:
                zero_count += 1
            else:
                partial_count += 1

        total_r = len(items)
        avg_m = round(float(sum(raw_marks) / total_r), 2)
        avg_pct = round(float(sum(normalized_scores) / total_r * 100), 2)

        return {
            "question_id": question_id,
            "total_responses": total_r,
            "valid_responses": total_r,
            "average_marks": avg_m,
            "max_marks": max_m,
            "average_percentage": avg_pct,
            "minimum_marks": round(float(min(raw_marks)), 2),
            "highest_marks": round(float(max(raw_marks)), 2),
            "full_mark_percentage": round(float(full_count / total_r * 100), 2),
            "zero_mark_percentage": round(float(zero_count / total_r * 100), 2),
            "partial_mark_percentage": round(float(partial_count / total_r * 100), 2)
        }

    def get_difficulty_analysis(self, examination_id: str, question_id: str) -> Dict[str, Any]:
        """Calculates difficulty index & category based on normalized average percentage."""
        perf = self.get_question_performance_analysis(examination_id, question_id)
        diff_idx = perf["average_percentage"]

        if diff_idx >= QUESTION_DIFFICULTY_EASY_THRESHOLD:
            category = "EASY"
        elif diff_idx >= QUESTION_DIFFICULTY_MODERATE_THRESHOLD:
            category = "MODERATE"
        else:
            category = "DIFFICULT"

        return {
            "question_id": question_id,
            "difficulty_index": diff_idx,
            "difficulty_category": category
        }

    def get_discrimination_analysis(self, examination_id: str, question_id: str) -> Dict[str, Any]:
        """
        Calculates question discrimination index comparing top 27% and bottom 27% student cohorts.
        Discrimination Index = Upper Group Mean - Lower Group Mean (using normalized question scores).
        """
        finalized_evals = self._get_finalized_evaluations_for_exam(examination_id)
        cohort_size = len(finalized_evals)

        if cohort_size < MINIMUM_COHORT_SIZE_FOR_DISCRIMINATION:
            return {
                "question_id": question_id,
                "discrimination_index": None,
                "discrimination_category": "INSUFFICIENT_SAMPLE",
                "upper_group_mean": None,
                "lower_group_mean": None,
                "cohort_size": cohort_size
            }

        # Sort student evaluations by total finalized exam score descending
        sorted_evals = sorted(
            finalized_evals,
            key=lambda e: (e.total_final_marks if e.total_final_marks is not None else (e.total_ai_marks or 0.0)),
            reverse=True
        )

        group_size = max(1, int(round(cohort_size * DISCRIMINATION_TOP_BOTTOM_PERCENTILE)))
        upper_evals = sorted_evals[:group_size]
        lower_evals = sorted_evals[-group_size:]

        def _get_normalized_score_for_question(eval_obj: Evaluation) -> Optional[float]:
            item = (
                self.db.query(EvaluationItem)
                .join(QuestionPaperItem, EvaluationItem.question_paper_item_id == QuestionPaperItem.id)
                .filter(
                    EvaluationItem.evaluation_id == eval_obj.id,
                    QuestionPaperItem.question_id == question_id
                )
                .first()
            )
            if not item:
                return None
            mark = item.final_marks if item.final_marks is not None else (item.ai_marks if item.ai_marks is not None else 0.0)
            max_m = item.maximum_marks if (item.maximum_marks and item.maximum_marks > 0) else 10.0
            return mark / max_m if max_m > 0 else 0.0

        upper_scores = [s for e in upper_evals if (s := _get_normalized_score_for_question(e)) is not None]
        lower_scores = [s for e in lower_evals if (s := _get_normalized_score_for_question(e)) is not None]

        if not upper_scores or not lower_scores:
            return {
                "question_id": question_id,
                "discrimination_index": None,
                "discrimination_category": "INSUFFICIENT_SAMPLE",
                "upper_group_mean": None,
                "lower_group_mean": None,
                "cohort_size": cohort_size
            }

        upper_mean = sum(upper_scores) / len(upper_scores)
        lower_mean = sum(lower_scores) / len(lower_scores)
        disc_index = round(float(upper_mean - lower_mean), 2)

        if disc_index >= DISCRIMINATION_STRONG_THRESHOLD:
            category = "STRONG"
        elif disc_index >= DISCRIMINATION_ACCEPTABLE_THRESHOLD:
            category = "ACCEPTABLE"
        elif disc_index >= DISCRIMINATION_WEAK_THRESHOLD:
            category = "WEAK"
        else:
            category = "NEGATIVE"

        return {
            "question_id": question_id,
            "discrimination_index": disc_index,
            "discrimination_category": category,
            "upper_group_mean": round(float(upper_mean * 100), 2),
            "lower_group_mean": round(float(lower_mean * 100), 2),
            "cohort_size": cohort_size
        }

    def get_question_similarity_integration(self, examination_id: str, question_id: str) -> Dict[str, Any]:
        """Integrates Phase 11 answer similarity metrics for a question in an examination."""
        similarities = (
            self.db.query(AnswerSimilarity)
            .filter(
                AnswerSimilarity.examination_id == examination_id,
                AnswerSimilarity.question_id == question_id
            )
            .all()
        )

        if not similarities:
            return {
                "flagged_pair_count": 0,
                "highest_similarity": 0.0,
                "average_similarity": 0.0,
                "reviewed_cases": 0,
                "dismissed_cases": 0
            }

        scores = [s.similarity_score for s in similarities if s.similarity_score is not None]
        highest = round(float(max(scores)), 2) if scores else 0.0
        avg_sim = round(float(sum(scores) / len(scores)), 2) if scores else 0.0

        results = (
            self.db.query(PlagiarismResult)
            .filter(PlagiarismResult.examination_id == examination_id)
            .all()
        )

        reviewed = sum(1 for r in results if r.review_status == "REVIEWED")
        dismissed = sum(1 for r in results if r.review_status == "DISMISSED")

        return {
            "flagged_pair_count": len(similarities),
            "highest_similarity": highest,
            "average_similarity": avg_sim,
            "reviewed_cases": reviewed,
            "dismissed_cases": dismissed
        }

    def get_question_quality_classification(self, examination_id: str, question_id: str) -> Dict[str, Any]:
        """Provides holistic question quality analysis and faculty review indicator status."""
        perf = self.get_question_performance_analysis(examination_id, question_id)
        diff = self.get_difficulty_analysis(examination_id, question_id)
        disc = self.get_discrimination_analysis(examination_id, question_id)
        sim = self.get_question_similarity_integration(examination_id, question_id)

        review = (
            self.db.query(QuestionQualityReview)
            .filter(
                QuestionQualityReview.question_id == question_id,
                QuestionQualityReview.examination_id == examination_id
            )
            .order_by(QuestionQualityReview.created_at.desc())
            .first()
        )

        quality_status = "GOOD"
        issues = []

        if perf["total_responses"] < 3:
            quality_status = "INSUFFICIENT_DATA"
        else:
            if disc["discrimination_category"] in ("NEGATIVE", "WEAK"):
                issues.append("DISCRIMINATION")
            if diff["difficulty_category"] in ("DIFFICULT", "EASY"):
                issues.append("DIFFICULTY")
            if sim["flagged_pair_count"] > 0:
                issues.append("SIMILARITY")

            if len(issues) > 1:
                quality_status = "REVIEW_MULTIPLE_SIGNALS"
            elif "DISCRIMINATION" in issues:
                quality_status = "REVIEW_DISCRIMINATION"
            elif "DIFFICULTY" in issues:
                quality_status = "REVIEW_DIFFICULTY"
            elif "SIMILARITY" in issues:
                quality_status = "REVIEW_SIMILARITY"
            else:
                quality_status = "GOOD"

        return {
            "question_id": question_id,
            "difficulty_index": diff["difficulty_index"],
            "difficulty_category": diff["difficulty_category"],
            "discrimination_index": disc["discrimination_index"],
            "discrimination_category": disc["discrimination_category"],
            "response_count": perf["total_responses"],
            "average_percentage": perf["average_percentage"],
            "full_mark_percentage": perf["full_mark_percentage"],
            "zero_mark_percentage": perf["zero_mark_percentage"],
            "similarity_flag_count": sim["flagged_pair_count"],
            "quality_status": quality_status,
            "faculty_review_status": review.status if review else "UNREVIEWED",
            "faculty_review_note": review.note if review else None
        }

    def get_exam_quality_dashboard(self, examination_id: str) -> Dict[str, Any]:
        """Generates complete Exam Quality Dashboard metrics and question quality table."""
        exam = self.db.query(Examination).filter(Examination.id == examination_id).first()
        if not exam:
            raise HTTPException(status_code=404, detail="Examination not found")

        finalized_evals = self._get_finalized_evaluations_for_exam(examination_id)
        finalized_count = len(finalized_evals)

        # Get all question paper items for this exam
        version_id = exam.question_paper_version_id
        qp_items = []
        if version_id:
            qp_items = (
                self.db.query(QuestionPaperItem)
                .filter(QuestionPaperItem.question_paper_version_id == version_id)
                .order_by(QuestionPaperItem.order_index)
                .all()
            )
        elif exam.question_paper_id:
            version = (
                self.db.query(QuestionPaperVersion)
                .filter(QuestionPaperVersion.question_paper_id == exam.question_paper_id)
                .order_by(QuestionPaperVersion.version_number.desc())
                .first()
            )
            if version:
                qp_items = (
                    self.db.query(QuestionPaperItem)
                    .filter(QuestionPaperItem.question_paper_version_id == version.id)
                    .order_by(QuestionPaperItem.order_index)
                    .all()
                )

        if finalized_count == 0 or not qp_items:
            return {
                "examination_id": examination_id,
                "examination_title": exam.name,
                "subject_name": exam.subject.name if exam.subject else None,
                "total_questions": len(qp_items),
                "finalized_responses": finalized_count,
                "average_exam_score": 0.0,
                "average_exam_percentage": 0.0,
                "questions_analyzed": 0,
                "questions_requiring_review": 0,
                "difficulty_distribution": {"EASY": 0, "MODERATE": 0, "DIFFICULT": 0},
                "discrimination_distribution": {"STRONG": 0, "ACCEPTABLE": 0, "WEAK": 0, "NEGATIVE": 0, "INSUFFICIENT_SAMPLE": len(qp_items)},
                "quality_status_summary": {"GOOD": 0, "INSUFFICIENT_DATA": len(qp_items)},
                "questions": []
            }

        scores = [e.total_final_marks if e.total_final_marks is not None else (e.total_ai_marks or 0.0) for e in finalized_evals]
        max_possible = exam.total_marks or 100.0
        avg_score = round(float(sum(scores) / finalized_count), 2)
        avg_pct = round(float((avg_score / max_possible) * 100), 2) if max_possible > 0 else 0.0

        diff_dist = {"EASY": 0, "MODERATE": 0, "DIFFICULT": 0}
        disc_dist = {"STRONG": 0, "ACCEPTABLE": 0, "WEAK": 0, "NEGATIVE": 0, "INSUFFICIENT_SAMPLE": 0}
        status_dist = {}

        question_rows = []
        review_count = 0

        for qp_item in qp_items:
            q_id = qp_item.question_id
            if not q_id:
                continue

            question = self.db.query(Question).filter(Question.id == q_id).first()
            if not question:
                continue

            q_qual = self.get_question_quality_classification(examination_id, q_id)

            diff_cat = q_qual["difficulty_category"]
            disc_cat = q_qual["discrimination_category"]
            q_status = q_qual["quality_status"]

            diff_dist[diff_cat] = diff_dist.get(diff_cat, 0) + 1
            disc_dist[disc_cat] = disc_dist.get(disc_cat, 0) + 1
            status_dist[q_status] = status_dist.get(q_status, 0) + 1

            if q_status != "GOOD":
                review_count += 1

            unit = self.db.query(Unit).filter(Unit.id == question.unit_id).first() if question.unit_id else None
            topic = self.db.query(Topic).filter(Topic.id == question.topic_id).first() if question.topic_id else None
            co = self.db.query(LearningOutcome).filter(LearningOutcome.id == question.learning_outcome_id).first() if question.learning_outcome_id else None

            question_rows.append({
                "question_id": q_id,
                "question_number": qp_item.question_number or f"Q-{q_id[:6]}",
                "question_text": question.question_text,
                "unit_title": f"Unit {unit.unit_number}: {unit.title}" if unit else "Unmapped",
                "topic_name": topic.name if topic else "Unmapped",
                "co_code": co.code if co else "Unmapped",
                "bloom_level": str(question.bloom_level) if question.bloom_level else "UNSPECIFIED",
                "configured_difficulty": str(question.difficulty) if question.difficulty else "MEDIUM",
                "max_marks": qp_item.marks or question.marks or 10.0,
                "average_percentage": q_qual["average_percentage"],
                "difficulty_category": diff_cat,
                "discrimination_index": q_qual["discrimination_index"],
                "discrimination_category": disc_cat,
                "similarity_flag_count": q_qual["similarity_flag_count"],
                "quality_status": q_status,
                "faculty_review_status": q_qual["faculty_review_status"],
                "faculty_review_note": q_qual["faculty_review_note"]
            })

        return {
            "examination_id": examination_id,
            "examination_title": exam.name,
            "subject_name": exam.subject.name if exam.subject else None,
            "total_questions": len(qp_items),
            "finalized_responses": finalized_count,
            "average_exam_score": avg_score,
            "average_exam_percentage": avg_pct,
            "questions_analyzed": len(question_rows),
            "questions_requiring_review": review_count,
            "difficulty_distribution": diff_dist,
            "discrimination_distribution": disc_dist,
            "quality_status_summary": status_dist,
            "questions": question_rows
        }

    def get_exam_blueprint_balance(self, examination_id: str) -> Dict[str, Any]:
        """Analyzes exam marks variance against configured blueprint rules across academic dimensions."""
        exam = self.db.query(Examination).filter(Examination.id == examination_id).first()
        if not exam:
            raise HTTPException(status_code=404, detail="Examination not found")

        qp = exam.question_paper
        blueprint = qp.blueprint if qp and qp.blueprint else None

        if not qp:
            # Fallback if paper not linked directly
            version = exam.question_paper_version
            if version and version.question_paper:
                qp = version.question_paper
                blueprint = qp.blueprint if qp else None

        # Gather actual question paper items
        version_id = exam.question_paper_version_id or (qp.versions[0].id if qp and qp.versions else None)
        qp_items = (
            self.db.query(QuestionPaperItem)
            .filter(QuestionPaperItem.question_paper_version_id == version_id)
            .all()
        ) if version_id else []

        total_exam_marks = exam.total_marks or (qp.total_marks if qp else 100.0)

        # Actual distribution calculation
        unit_actual: Dict[str, float] = {}
        bloom_actual: Dict[str, float] = {}
        diff_actual: Dict[str, float] = {}

        for item in qp_items:
            q = self.db.query(Question).filter(Question.id == item.question_id).first() if item.question_id else None
            m = item.marks or (q.marks if q else 10.0)

            u_key = q.unit_id if (q and q.unit_id) else "UNMAPPED"
            b_key = str(q.bloom_level) if (q and q.bloom_level) else "UNSPECIFIED"
            d_key = str(q.difficulty) if (q and q.difficulty) else "MEDIUM"

            unit_actual[u_key] = unit_actual.get(u_key, 0.0) + m
            bloom_actual[b_key] = bloom_actual.get(b_key, 0.0) + m
            diff_actual[d_key] = diff_actual.get(d_key, 0.0) + m

        unit_breakdown = []
        max_variance = 0.0

        if blueprint and blueprint.rules:
            for rule in blueprint.rules:
                target_marks = rule.total_marks or (rule.question_count * rule.marks_per_question)
                target_pct = round(float((target_marks / blueprint.total_marks) * 100), 2) if blueprint.total_marks > 0 else 0.0

                u_key = rule.unit_id or "ALL"
                unit_obj = self.db.query(Unit).filter(Unit.id == rule.unit_id).first() if rule.unit_id else None
                unit_title = f"Unit {unit_obj.unit_number}: {unit_obj.title}" if unit_obj else (rule.section or "Section")

                actual_m = unit_actual.get(rule.unit_id, 0.0) if rule.unit_id else (target_marks)
                actual_pct = round(float((actual_m / total_exam_marks) * 100), 2) if total_exam_marks > 0 else 0.0
                variance = round(float(actual_pct - target_pct), 2)

                if abs(variance) > max_variance:
                    max_variance = abs(variance)

                unit_breakdown.append({
                    "dimension": "UNIT",
                    "category_name": unit_title,
                    "target_percentage": target_pct,
                    "actual_percentage": actual_pct,
                    "variance": variance,
                    "status": "BALANCED" if abs(variance) <= BLUEPRINT_VARIANCE_TOLERANCE else "REVIEW_VARIANCE"
                })
        else:
            # Build breakdown based on actual paper items
            for u_id, actual_m in unit_actual.items():
                unit_obj = self.db.query(Unit).filter(Unit.id == u_id).first() if u_id != "UNMAPPED" else None
                title = f"Unit {unit_obj.unit_number}: {unit_obj.title}" if unit_obj else "Unmapped Unit"
                actual_pct = round(float((actual_m / total_exam_marks) * 100), 2) if total_exam_marks > 0 else 0.0

                unit_breakdown.append({
                    "dimension": "UNIT",
                    "category_name": title,
                    "target_percentage": actual_pct, # No target configured
                    "actual_percentage": actual_pct,
                    "variance": 0.0,
                    "status": "BALANCED"
                })

        overall_status = "BALANCED" if max_variance <= BLUEPRINT_VARIANCE_TOLERANCE else "REVIEW_VARIANCE"

        return {
            "examination_id": examination_id,
            "blueprint_id": blueprint.id if blueprint else None,
            "blueprint_name": blueprint.name if blueprint else "No Blueprint Configured",
            "total_marks": total_exam_marks,
            "overall_status": overall_status,
            "max_variance": max_variance,
            "variance_tolerance_used": BLUEPRINT_VARIANCE_TOLERANCE,
            "breakdown": unit_breakdown
        }

    def get_question_bank_insights(self, subject_id: str) -> Dict[str, Any]:
        """Analyzes historical finalized exams and provides empirical usage, performance, and quality metrics."""
        subject = self.db.query(Subject).filter(Subject.id == subject_id).first()
        if not subject:
            raise HTTPException(status_code=404, detail="Subject not found")

        questions = self.db.query(Question).filter(Question.subject_id == subject_id).all()

        insights = []
        for q in questions:
            # Usage count across paper versions
            items = self.db.query(QuestionPaperItem).filter(QuestionPaperItem.question_id == q.id).all()
            times_used = len(set(i.question_paper_version_id for i in items))

            # Query all finalized evaluations containing this question
            eval_items = (
                self.db.query(EvaluationItem)
                .join(Evaluation, EvaluationItem.evaluation_id == Evaluation.id)
                .filter(
                    EvaluationItem.question_paper_item_id.in_([i.id for i in items]) if items else False,
                    Evaluation.status == EvaluationStatusEnum.FINALIZED
                )
                .all()
            ) if items else []

            if eval_items:
                marks = [ei.final_marks if ei.final_marks is not None else (ei.ai_marks or 0.0) for ei in eval_items]
                max_ms = [ei.maximum_marks if (ei.maximum_marks and ei.maximum_marks > 0) else 10.0 for ei in eval_items]
                norms = [m / max_m for m, max_m in zip(marks, max_ms)]

                tot_r = len(eval_items)
                hist_avg_pct = round(float(sum(norms) / tot_r * 100), 2)
                hist_status = "STABLE"
            else:
                tot_r = 0
                hist_avg_pct = None
                hist_status = "UNTESTED"

            unit = self.db.query(Unit).filter(Unit.id == q.unit_id).first() if q.unit_id else None

            insights.append({
                "question_id": q.id,
                "question_text": q.question_text[:80] + "..." if len(q.question_text) > 80 else q.question_text,
                "unit_title": f"Unit {unit.unit_number}: {unit.title}" if unit else "Unmapped",
                "configured_difficulty": str(q.difficulty) if q.difficulty else "MEDIUM",
                "bloom_level": str(q.bloom_level) if q.bloom_level else "UNSPECIFIED",
                "times_used": times_used,
                "total_responses": tot_r,
                "historical_average_percentage": hist_avg_pct,
                "status_indicator": hist_status
            })

        return {
            "subject_id": subject_id,
            "subject_name": subject.name,
            "total_questions_in_bank": len(questions),
            "questions": insights
        }

    def get_weak_assessment_coverage(self, subject_id: str) -> Dict[str, Any]:
        """Identifies syllabus areas (Units/Topics/COs) with low historical assessment coverage."""
        units = self.db.query(Unit).filter(Unit.subject_id == subject_id).all()

        unit_coverage = []
        for u in units:
            topics = self.db.query(Topic).filter(Topic.unit_id == u.id).all()
            q_count = self.db.query(Question).filter(Question.unit_id == u.id).count()

            # Find used question items
            q_ids = [q.id for q in self.db.query(Question.id).filter(Question.unit_id == u.id).all()]
            used_count = (
                self.db.query(QuestionPaperItem)
                .filter(QuestionPaperItem.question_id.in_(q_ids))
                .count()
            ) if q_ids else 0

            coverage_level = "LOW" if used_count < 2 else ("MODERATE" if used_count < 5 else "HIGH")

            unit_coverage.append({
                "unit_id": u.id,
                "unit_number": u.unit_number,
                "unit_title": u.title,
                "available_questions": q_count,
                "times_assessed": used_count,
                "coverage_level": coverage_level
            })

        return {
            "subject_id": subject_id,
            "units_analyzed": len(units),
            "unit_coverage": unit_coverage
        }

    def record_question_quality_review(
        self,
        question_id: str,
        examination_id: Optional[str],
        reviewer_id: str,
        status_val: str,
        note: Optional[str]
    ) -> QuestionQualityReview:
        """Records persistent faculty review decisions and emits audit logs."""
        question = self.db.query(Question).filter(Question.id == question_id).first()
        if not question:
            raise HTTPException(status_code=404, detail="Question not found")

        review = QuestionQualityReview(
            question_id=question_id,
            examination_id=examination_id,
            reviewer_id=reviewer_id,
            status=status_val,
            note=note,
            reviewed_at=datetime.datetime.utcnow().isoformat()
        )
        self.db.add(review)

        audit = AuditLog(
            user_id=reviewer_id,
            action=AuditActionEnum.QUESTION_QUALITY_REVIEWED,
            entity_type="QuestionQualityReview",
            entity_id=review.id,
            new_values={"question_id": question_id, "status": status_val, "note": note}
        )
        self.db.add(audit)
        self.db.commit()
        self.db.refresh(review)
        return review
