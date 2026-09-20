import datetime
import statistics
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_
from fastapi import HTTPException, status

try:
    from app.db.models import (
        Examination, ExaminationStudent, AnswerPaper, Evaluation, EvaluationItem,
        EvaluationStatusEnum, Question, QuestionPaper, QuestionPaperItem,
        Unit, Topic, LearningOutcome, User, Subject
    )
except ImportError:
    from backend.app.db.models import (
        Examination, ExaminationStudent, AnswerPaper, Evaluation, EvaluationItem,
        EvaluationStatusEnum, Question, QuestionPaper, QuestionPaperItem,
        Unit, Topic, LearningOutcome, User, Subject
    )

class PerformanceAnalyticsService:
    """Service providing server-side performance analytics using strictly FINALIZED evaluations."""

    def __init__(self, db: Session):
        self.db = db

    def _get_finalized_evaluations_for_exam(self, examination_id: str) -> List[Evaluation]:
        """Retrieves only FINALIZED evaluations for an examination."""
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

    def get_examination_overview(self, examination_id: str) -> Dict[str, Any]:
        """Generates overview performance analytics for an examination based on finalized evaluations."""
        examination = self.db.query(Examination).filter(Examination.id == examination_id).first()
        if not examination:
            raise HTTPException(status_code=404, detail="Examination not found")

        # Total registered students
        total_students = (
            self.db.query(ExaminationStudent)
            .filter(ExaminationStudent.examination_id == examination_id)
            .count()
        )

        finalized_evaluations = self._get_finalized_evaluations_for_exam(examination_id)
        eval_count = len(finalized_evaluations)

        if eval_count == 0:
            return {
                "examination_id": examination_id,
                "examination_title": examination.name if hasattr(examination, 'name') else "Examination",
                "subject_id": examination.subject_id if hasattr(examination, 'subject_id') else None,

                "subject_name": examination.subject.name if hasattr(examination, 'subject') and examination.subject else None,
                "total_students": total_students,
                "finalized_evaluations": 0,
                "average_marks": 0.0,
                "median_marks": 0.0,
                "highest_marks": 0.0,
                "lowest_marks": 0.0,
                "max_possible_marks": examination.total_marks if hasattr(examination, 'total_marks') else 100.0,
                "average_percentage": 0.0,
                "pass_percentage": 0.0,
                "generated_at": datetime.datetime.utcnow().isoformat()
            }

        scores = [e.total_final_marks if e.total_final_marks is not None else e.total_ai_marks for e in finalized_evaluations]
        max_possible = examination.total_marks if hasattr(examination, 'total_marks') and examination.total_marks else 100.0

        avg_marks = round(float(sum(scores) / eval_count), 2)
        med_marks = round(float(statistics.median(scores)), 2)
        high_marks = round(float(max(scores)), 2)
        low_marks = round(float(min(scores)), 2)
        avg_pct = round(float((avg_marks / max_possible) * 100), 2) if max_possible > 0 else 0.0

        # Pass criteria: >= 40%
        passing_count = sum(1 for s in scores if (s / max_possible * 100 if max_possible > 0 else 0) >= 40.0)
        pass_pct = round(float((passing_count / eval_count) * 100), 2)

        return {
            "examination_id": examination_id,
            "examination_title": examination.name if hasattr(examination, 'name') else "Examination",
            "subject_id": examination.subject_id if hasattr(examination, 'subject_id') else None,
            "subject_name": examination.subject.name if hasattr(examination, 'subject') and examination.subject else None,
            "total_students": total_students,
            "finalized_evaluations": eval_count,
            "average_marks": avg_marks,
            "median_marks": med_marks,
            "highest_marks": high_marks,
            "lowest_marks": low_marks,
            "max_possible_marks": max_possible,
            "average_percentage": avg_pct,
            "pass_percentage": pass_pct,
            "generated_at": datetime.datetime.utcnow().isoformat()
        }

    def get_students_performance(self, examination_id: str) -> List[Dict[str, Any]]:
        """Generates student-level performance metrics for an examination."""
        finalized_evaluations = self._get_finalized_evaluations_for_exam(examination_id)
        examination = self.db.query(Examination).filter(Examination.id == examination_id).first()
        max_possible = examination.total_marks if examination and hasattr(examination, 'total_marks') and examination.total_marks else 100.0

        results = []
        for e in finalized_evaluations:
            paper = e.answer_paper
            if not paper:
                continue
            student = paper.student
            tot_marks = e.total_final_marks if e.total_final_marks is not None else e.total_ai_marks
            pct = round(float((tot_marks / max_possible) * 100), 2) if max_possible > 0 else 0.0

            results.append({
                "student_id": student.id if student else paper.student_id,
                "student_name": student.full_name if student else "Student",
                "student_email": student.email if student else None,
                "examination_id": examination_id,
                "examination_title": examination.name if examination else "Examination",
                "total_marks": round(float(tot_marks), 2),
                "max_marks": max_possible,
                "percentage": pct,
                "evaluation_status": str(e.status),
                "finalized_at": e.finalized_at,
                "rank": None
            })

        # Rank students by score descending
        results.sort(key=lambda x: x["total_marks"], reverse=True)
        for idx, r in enumerate(results, start=1):
            r["rank"] = idx

        return results

    def get_single_student_performance(self, student_id: str) -> Dict[str, Any]:
        """Retrieves performance metrics across all finalized examinations for a single student."""
        student = self.db.query(User).filter(User.id == student_id).first()
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")

        finalized_status = EvaluationStatusEnum.FINALIZED.value if hasattr(EvaluationStatusEnum.FINALIZED, 'value') else "FINALIZED"
        evaluations = (
            self.db.query(Evaluation)
            .join(AnswerPaper, Evaluation.answer_paper_id == AnswerPaper.id)
            .filter(
                AnswerPaper.student_id == student_id,
                Evaluation.status == finalized_status
            )
            .all()
        )

        exam_breakdown = []
        total_obtained = 0.0
        total_possible = 0.0

        for e in evaluations:
            paper = e.answer_paper
            exam = paper.examination if paper else None
            tot_marks = e.total_final_marks if e.total_final_marks is not None else e.total_ai_marks

            max_m = exam.total_marks if exam and hasattr(exam, 'total_marks') and exam.total_marks else 100.0
            pct = round(float((tot_marks / max_m) * 100), 2) if max_m > 0 else 0.0

            total_obtained += tot_marks
            total_possible += max_m

            exam_breakdown.append({
                "examination_id": exam.id if exam else "",
                "examination_title": exam.name if exam else "Exam",
                "subject_name": exam.subject.name if exam and hasattr(exam, 'subject') and exam.subject else "Subject",

                "marks_obtained": round(float(tot_marks), 2),
                "max_marks": max_m,
                "percentage": pct,
                "finalized_at": e.finalized_at
            })

        avg_pct = round(float((total_obtained / total_possible) * 100), 2) if total_possible > 0 else 0.0

        return {
            "student_id": student_id,
            "student_name": student.full_name,
            "student_email": student.email,
            "total_examinations": len(evaluations),
            "overall_average_percentage": avg_pct,
            "examinations": exam_breakdown
        }

    def get_question_analytics(self, examination_id: str) -> List[Dict[str, Any]]:
        """Calculates performance statistics for each question on an examination paper."""
        finalized_evals = self._get_finalized_evaluations_for_exam(examination_id)
        if not finalized_evals:
            return []

        eval_ids = [e.id for e in finalized_evals]
        items = (
            self.db.query(EvaluationItem)
            .filter(EvaluationItem.evaluation_id.in_(eval_ids))
            .all()
        )

        question_scores: Dict[str, List[float]] = {}
        question_max: Dict[str, float] = {}

        for item in items:
            q_id = item.question_paper_item.question_id if (hasattr(item, 'question_paper_item') and item.question_paper_item and item.question_paper_item.question_id) else getattr(item, 'question_id', None)
            if not q_id:
                continue
            mark = item.final_marks if item.final_marks is not None else (item.ai_marks if item.ai_marks is not None else 0.0)
            max_m = item.maximum_marks if (hasattr(item, 'maximum_marks') and item.maximum_marks is not None) else getattr(item, 'max_marks', 10.0)
            question_scores.setdefault(q_id, []).append(mark)
            question_max[q_id] = max_m

        results = []
        for q_id, scores in question_scores.items():
            question = self.db.query(Question).filter(Question.id == q_id).first()
            if not question:
                continue

            max_m = question_max.get(q_id, question.marks or 10.0)
            avg_m = round(float(sum(scores) / len(scores)), 2)
            pct = round(float((avg_m / max_m) * 100), 2) if max_m > 0 else 0.0

            results.append({
                "question_id": q_id,
                "question_number": f"Q-{q_id[:6]}",
                "question_text": question.question_text,
                "question_type": str(question.question_type) if question.question_type else "DESCRIPTIVE",
                "bloom_level": str(question.bloom_level) if question.bloom_level else None,
                "difficulty_level": str(question.difficulty) if question.difficulty else None,
                "max_marks": max_m,
                "average_marks": avg_m,
                "percentage_achieved": pct,
                "total_responses": len(scores),
                "highest_marks": round(float(max(scores)), 2),
                "lowest_marks": round(float(min(scores)), 2)
            })

        return results

    def get_dimension_analytics(self, examination_id: str, dimension: str) -> List[Dict[str, Any]]:
        """
        Calculates performance aggregated by academic dimension:
        dimension in ('unit', 'topic', 'learning_outcome', 'bloom', 'difficulty')
        """
        finalized_evals = self._get_finalized_evaluations_for_exam(examination_id)
        if not finalized_evals:
            return []

        eval_ids = [e.id for e in finalized_evals]
        items = (
            self.db.query(EvaluationItem)
            .filter(EvaluationItem.evaluation_id.in_(eval_ids))
            .all()
        )

        dim_scores: Dict[str, Dict[str, Any]] = {}

        for item in items:
            q_id = item.question_paper_item.question_id if (hasattr(item, 'question_paper_item') and item.question_paper_item and item.question_paper_item.question_id) else getattr(item, 'question_id', None)
            question = self.db.query(Question).filter(Question.id == q_id).first() if q_id else None
            if not question:
                continue

            dim_key = None
            meta = {}

            if dimension == "unit":
                if question.unit_id:
                    unit = self.db.query(Unit).filter(Unit.id == question.unit_id).first()
                    dim_key = question.unit_id
                    meta = {
                        "unit_id": question.unit_id,
                        "unit_name": f"Unit {unit.unit_number}: {unit.title}" if unit else f"Unit {question.unit_id[:6]}",
                        "unit_number": unit.unit_number if unit else None
                    }
            elif dimension == "topic":
                if question.topic_id:
                    topic = self.db.query(Topic).filter(Topic.id == question.topic_id).first()
                    unit = self.db.query(Unit).filter(Unit.id == topic.unit_id).first() if topic and topic.unit_id else None
                    dim_key = question.topic_id
                    meta = {
                        "topic_id": question.topic_id,
                        "topic_name": topic.name if topic else f"Topic {question.topic_id[:6]}",
                        "unit_id": topic.unit_id if topic else None,
                        "unit_name": unit.title if unit else None
                    }
            elif dimension == "learning_outcome":
                if question.learning_outcome_id:
                    co = self.db.query(LearningOutcome).filter(LearningOutcome.id == question.learning_outcome_id).first()
                    dim_key = question.learning_outcome_id
                    meta = {
                        "learning_outcome_id": question.learning_outcome_id,
                        "code": co.code if co else "CO",
                        "description": co.description if co else f"Learning Outcome {question.learning_outcome_id[:6]}"
                    }
            elif dimension == "bloom":
                dim_key = str(question.bloom_level) if question.bloom_level else "UNSPECIFIED"
                meta = {"bloom_level": dim_key}
            elif dimension == "difficulty":
                dim_key = str(question.difficulty) if question.difficulty else "MEDIUM"
                meta = {"difficulty_level": dim_key}

            if not dim_key:
                dim_key = "UNMAPPED"
                if dimension == "unit":
                    meta = {"unit_id": "UNMAPPED", "unit_name": "Unmapped Unit", "unit_number": None}
                elif dimension == "topic":
                    meta = {"topic_id": "UNMAPPED", "topic_name": "Unmapped Topic", "unit_id": None, "unit_name": None}
                elif dimension == "learning_outcome":
                    meta = {"learning_outcome_id": "UNMAPPED", "code": "CO-GENERAL", "description": "Unmapped Outcome"}
                elif dimension == "bloom":
                    meta = {"bloom_level": "UNSPECIFIED"}
                elif dimension == "difficulty":
                    meta = {"difficulty_level": "UNSPECIFIED"}

            mark = item.final_marks if item.final_marks is not None else (item.ai_marks if item.ai_marks is not None else 0.0)
            max_m = item.maximum_marks if (hasattr(item, 'maximum_marks') and item.maximum_marks is not None) else getattr(item, 'max_marks', 10.0)

            if dim_key not in dim_scores:
                dim_scores[dim_key] = {
                    "meta": meta,
                    "obtained": 0.0,
                    "possible": 0.0,
                    "responses": 0,
                    "question_ids": set()
                }

            dim_scores[dim_key]["obtained"] += mark
            dim_scores[dim_key]["possible"] += max_m
            dim_scores[dim_key]["responses"] += 1
            dim_scores[dim_key]["question_ids"].add(question.id)

        results = []
        for key, data in dim_scores.items():
            tot_obt = round(float(data["obtained"]), 2)
            tot_pos = round(float(data["possible"]), 2)
            pct = round(float((tot_obt / tot_pos) * 100), 2) if tot_pos > 0 else 0.0
            avg_m = round(float(tot_obt / data["responses"]), 2) if data["responses"] > 0 else 0.0

            res_obj = dict(data["meta"])
            res_obj.update({
                "question_count": len(data["question_ids"]),
                "max_marks": tot_pos,
                "average_marks": avg_m,
                "percentage": pct,
                "response_count": data["responses"]
            })
            results.append(res_obj)

        results.sort(key=lambda x: x["percentage"])
        return results
