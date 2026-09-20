from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

try:
    from app.db.models import (
        Examination, AnswerPaper, Evaluation, EvaluationItem,
        EvaluationStatusEnum, Question, Topic, Unit, Subject
    )
except ImportError:
    from backend.app.db.models import (
        Examination, AnswerPaper, Evaluation, EvaluationItem,
        EvaluationStatusEnum, Question, Topic, Unit, Subject
    )

class WeakTopicService:
    """Service to detect weak academic topics based on student performance in finalized evaluations."""

    def __init__(self, db: Session):
        self.db = db

    def _get_finalized_evaluations_for_exam(self, examination_id: str) -> List[Evaluation]:
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

    def detect_weak_topics_for_examination(
        self,
        examination_id: str,
        threshold_percentage: float = 50.0,
        minimum_responses: int = 3
    ) -> Dict[str, Any]:
        """Identifies topics where class cohort performance falls below the threshold percentage."""
        examination = self.db.query(Examination).filter(Examination.id == examination_id).first()
        if not examination:
            raise HTTPException(status_code=404, detail="Examination not found")

        finalized_evals = self._get_finalized_evaluations_for_exam(examination_id)
        if not finalized_evals:
            return {
                "examination_id": examination_id,
                "total_topics_analyzed": 0,
                "weak_topics_count": 0,
                "threshold_used": threshold_percentage,
                "minimum_responses_used": minimum_responses,
                "weak_topics": []
            }

        eval_ids = [e.id for e in finalized_evals]
        items = (
            self.db.query(EvaluationItem)
            .filter(EvaluationItem.evaluation_id.in_(eval_ids))
            .all()
        )

        topic_stats: Dict[str, Dict[str, Any]] = {}

        for item in items:
            q_id = item.question_paper_item.question_id if (hasattr(item, 'question_paper_item') and item.question_paper_item and item.question_paper_item.question_id) else getattr(item, 'question_id', None)
            question = self.db.query(Question).filter(Question.id == q_id).first() if q_id else None
            if not question or not question.topic_id:
                continue

            t_id = question.topic_id
            if t_id not in topic_stats:
                topic = self.db.query(Topic).filter(Topic.id == t_id).first()
                unit = self.db.query(Unit).filter(Unit.id == topic.unit_id).first() if topic and topic.unit_id else None
                subject = self.db.query(Subject).filter(Subject.id == question.subject_id).first() if question.subject_id else None

                topic_stats[t_id] = {
                    "topic_id": t_id,
                    "topic_name": topic.name if topic else f"Topic {t_id[:6]}",
                    "unit_id": topic.unit_id if topic else None,
                    "unit_name": unit.title if unit else None,
                    "subject_id": question.subject_id,
                    "subject_name": subject.name if subject else None,
                    "obtained": 0.0,
                    "possible": 0.0,
                    "responses": 0,
                    "questions": {}
                }

            mark = item.final_marks if item.final_marks is not None else (item.ai_marks if item.ai_marks is not None else 0.0)
            max_m = item.maximum_marks if (hasattr(item, 'maximum_marks') and item.maximum_marks is not None) else getattr(item, 'max_marks', 10.0)

            topic_stats[t_id]["obtained"] += mark
            topic_stats[t_id]["possible"] += max_m
            topic_stats[t_id]["responses"] += 1

            # Track question level metrics under topic
            q_id = question.id
            if q_id not in topic_stats[t_id]["questions"]:
                topic_stats[t_id]["questions"][q_id] = {
                    "question_id": q_id,
                    "question_number": f"Q-{q_id[:6]}",
                    "question_text": question.question_text,
                    "obtained": 0.0,
                    "possible": 0.0,
                    "responses": 0
                }
            topic_stats[t_id]["questions"][q_id]["obtained"] += mark
            topic_stats[t_id]["questions"][q_id]["possible"] += max_m
            topic_stats[t_id]["questions"][q_id]["responses"] += 1

        all_topics_evidence = []
        weak_topics_list = []

        for t_id, data in topic_stats.items():
            tot_obt = round(float(data["obtained"]), 2)
            tot_pos = round(float(data["possible"]), 2)
            pct = round(float((tot_obt / tot_pos) * 100), 2) if tot_pos > 0 else 0.0
            avg_m = round(float(tot_obt / data["responses"]), 2) if data["responses"] > 0 else 0.0

            # Build supporting questions evidence
            sup_questions = []
            for q_id, q_data in data["questions"].items():
                q_obt = q_data["obtained"]
                q_pos = q_data["possible"]
                q_pct = round(float((q_obt / q_pos) * 100), 2) if q_pos > 0 else 0.0
                q_avg = round(float(q_obt / q_data["responses"]), 2) if q_data["responses"] > 0 else 0.0

                sup_questions.append({
                    "question_id": q_id,
                    "question_number": q_data["question_number"],
                    "question_text": q_data["question_text"],
                    "average_marks": q_avg,
                    "max_marks": q_pos / q_data["responses"] if q_data["responses"] > 0 else 0.0,
                    "percentage": q_pct
                })

            is_weak = pct < threshold_percentage and data["responses"] >= minimum_responses

            evidence = {
                "topic_id": t_id,
                "topic_name": data["topic_name"],
                "unit_id": data["unit_id"],
                "unit_name": data["unit_name"],
                "subject_id": data["subject_id"],
                "subject_name": data["subject_name"],
                "response_count": data["responses"],
                "average_marks": avg_m,
                "max_marks": tot_pos,
                "percentage": pct,
                "threshold_percentage": threshold_percentage,
                "minimum_responses_required": minimum_responses,
                "is_weak_topic": is_weak,
                "supporting_questions": sup_questions
            }

            all_topics_evidence.append(evidence)
            if is_weak:
                weak_topics_list.append(evidence)

        weak_topics_list.sort(key=lambda x: x["percentage"])

        return {
            "examination_id": examination_id,
            "total_topics_analyzed": len(all_topics_evidence),
            "weak_topics_count": len(weak_topics_list),
            "threshold_used": threshold_percentage,
            "minimum_responses_used": minimum_responses,
            "weak_topics": weak_topics_list
        }

    def detect_weak_topics_for_student(
        self,
        student_id: str,
        threshold_percentage: float = 50.0,
        minimum_responses: int = 1
    ) -> Dict[str, Any]:
        """Identifies topics where an individual student's performance falls below the threshold."""
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

        if not evaluations:
            return {
                "student_id": student_id,
                "total_topics_analyzed": 0,
                "weak_topics_count": 0,
                "threshold_used": threshold_percentage,
                "minimum_responses_used": minimum_responses,
                "weak_topics": []
            }

        eval_ids = [e.id for e in evaluations]
        items = (
            self.db.query(EvaluationItem)
            .filter(EvaluationItem.evaluation_id.in_(eval_ids))
            .all()
        )

        topic_stats: Dict[str, Dict[str, Any]] = {}

        for item in items:
            q_id = item.question_paper_item.question_id if (hasattr(item, 'question_paper_item') and item.question_paper_item and item.question_paper_item.question_id) else getattr(item, 'question_id', None)
            question = self.db.query(Question).filter(Question.id == q_id).first() if q_id else None
            if not question or not question.topic_id:
                continue

            t_id = question.topic_id
            if t_id not in topic_stats:
                topic = self.db.query(Topic).filter(Topic.id == t_id).first()
                unit = self.db.query(Unit).filter(Unit.id == topic.unit_id).first() if topic and topic.unit_id else None

                topic_stats[t_id] = {
                    "topic_id": t_id,
                    "topic_name": topic.name if topic else f"Topic {t_id[:6]}",
                    "unit_id": topic.unit_id if topic else None,
                    "unit_name": unit.title if unit else None,
                    "subject_id": question.subject_id,
                    "subject_name": None,
                    "obtained": 0.0,
                    "possible": 0.0,
                    "responses": 0,
                    "questions": []
                }

            mark = item.final_marks if item.final_marks is not None else (item.ai_marks if item.ai_marks is not None else 0.0)
            max_m = item.maximum_marks if (hasattr(item, 'maximum_marks') and item.maximum_marks is not None) else getattr(item, 'max_marks', 10.0)

            topic_stats[t_id]["obtained"] += mark
            topic_stats[t_id]["possible"] += max_m
            topic_stats[t_id]["responses"] += 1
            topic_stats[t_id]["questions"].append({
                "question_id": question.id,
                "question_number": f"Q-{question.id[:6]}",
                "question_text": question.question_text,
                "average_marks": mark,
                "max_marks": max_m,
                "percentage": round(float((mark / max_m) * 100), 2) if max_m > 0 else 0.0
            })

        weak_list = []
        for t_id, data in topic_stats.items():
            tot_obt = round(float(data["obtained"]), 2)
            tot_pos = round(float(data["possible"]), 2)
            pct = round(float((tot_obt / tot_pos) * 100), 2) if tot_pos > 0 else 0.0
            avg_m = round(float(tot_obt / data["responses"]), 2) if data["responses"] > 0 else 0.0

            is_weak = pct < threshold_percentage and data["responses"] >= minimum_responses

            evidence = {
                "topic_id": t_id,
                "topic_name": data["topic_name"],
                "unit_id": data["unit_id"],
                "unit_name": data["unit_name"],
                "subject_id": data["subject_id"],
                "subject_name": data["subject_name"],
                "response_count": data["responses"],
                "average_marks": avg_m,
                "max_marks": tot_pos,
                "percentage": pct,
                "threshold_percentage": threshold_percentage,
                "minimum_responses_required": minimum_responses,
                "is_weak_topic": is_weak,
                "supporting_questions": data["questions"]
            }

            if is_weak:
                weak_list.append(evidence)

        weak_list.sort(key=lambda x: x["percentage"])

        return {
            "student_id": student_id,
            "total_topics_analyzed": len(topic_stats),
            "weak_topics_count": len(weak_list),
            "threshold_used": threshold_percentage,
            "minimum_responses_used": minimum_responses,
            "weak_topics": weak_list
        }
