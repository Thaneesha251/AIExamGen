import re
import datetime
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, or_
from fastapi import HTTPException, status

try:
    from app.db.models import (
        Examination, AnswerPaper, ExtractedAnswer, Question, QuestionTypeEnum,
        PlagiarismResult, AnswerSimilarity, User, AuditLog, AuditActionEnum
    )
except ImportError:
    from backend.app.db.models import (
        Examination, AnswerPaper, ExtractedAnswer, Question, QuestionTypeEnum,
        PlagiarismResult, AnswerSimilarity, User, AuditLog, AuditActionEnum
    )

from ai.services.embedding_service import LocalEmbeddingService

OBJECTIVE_QUESTION_TYPES = {
    QuestionTypeEnum.MCQ.value if hasattr(QuestionTypeEnum.MCQ, 'value') else "MCQ",
    QuestionTypeEnum.TRUE_FALSE.value if hasattr(QuestionTypeEnum.TRUE_FALSE, 'value') else "TRUE_FALSE",
    QuestionTypeEnum.FILL_BLANK.value if hasattr(QuestionTypeEnum.FILL_BLANK, 'value') else "FILL_BLANK",
}

class SimilarityAnalysisService:
    """Service handling pairwise answer similarity comparison and plagiarism review workflow."""

    def __init__(self, db: Session):
        self.db = db

    def normalize_text(self, text: str) -> str:
        """Normalizes text while retaining meaningful math/punctuation structures."""
        if not text:
            return ""
        # Lowercase
        normalized = text.lower()
        # Collapse multiple spaces and newlines
        normalized = re.sub(r"\s+", " ", normalized).strip()
        return normalized

    def calculate_lexical_similarity(self, text1: str, text2: str) -> float:
        """Combines TF-IDF term frequency cosine similarity and character 3-gram Jaccard similarity."""
        cosine_sim = LocalEmbeddingService.cosine_similarity(text1, text2)
        jaccard_sim = LocalEmbeddingService.jaccard_similarity(text1, text2)
        blend = (0.6 * cosine_sim) + (0.4 * jaccard_sim)
        return round(float(blend), 4)

    def calculate_semantic_similarity(self, text1: str, text2: str) -> float:
        """Calculates semantic representation similarity."""
        cosine_sim = LocalEmbeddingService.cosine_similarity(text1, text2)
        return round(float(cosine_sim), 4)

    def analyze_examination_similarity(
        self,
        examination_id: str,
        user_id: Optional[str] = None,
        lexical_weight: float = 0.5,
        semantic_weight: float = 0.5,
        flag_threshold: float = 0.70,
        minimum_text_length: int = 15
    ) -> Dict[str, Any]:
        """
        Executes pairwise answer similarity comparison across all student answer papers for a given examination.
        Saves AnswerSimilarity records and aggregate PlagiarismResult records.
        """
        examination = self.db.query(Examination).filter(Examination.id == examination_id).first()
        if not examination:
            raise HTTPException(status_code=404, detail="Examination not found")

        # Log start audit event
        if user_id:
            audit_start = AuditLog(
                user_id=user_id,
                action=AuditActionEnum.SIMILARITY_ANALYSIS_STARTED,
                entity_type="EXAMINATION",
                entity_id=examination_id,
                new_values={"lexical_weight": lexical_weight, "semantic_weight": semantic_weight, "flag_threshold": flag_threshold}
            )
            self.db.add(audit_start)
            self.db.commit()


        # Fetch all answer papers for this exam
        answer_papers = self.db.query(AnswerPaper).filter(AnswerPaper.examination_id == examination_id).all()
        if not answer_papers:
            return {
                "examination_id": examination_id,
                "message": "No answer papers found for examination",
                "total_papers": 0,
                "analyzed_pairs": 0,
                "flagged_cases": 0
            }

        paper_map = {p.id: p for p in answer_papers}
        paper_ids = list(paper_map.keys())

        # Fetch all extracted answers for these papers
        extracted_answers = (
            self.db.query(ExtractedAnswer)
            .join(AnswerPaper, ExtractedAnswer.answer_paper_id == AnswerPaper.id)
            .filter(AnswerPaper.examination_id == examination_id)
            .all()
        )

        # Group extracted answers by question_id
        question_answers: Dict[str, List[ExtractedAnswer]] = {}
        for ans in extracted_answers:
            q_id = None
            if hasattr(ans, 'question_paper_item') and ans.question_paper_item and ans.question_paper_item.question_id:
                q_id = ans.question_paper_item.question_id
            else:
                eval_item = self.db.query(EvaluationItem).filter(EvaluationItem.extracted_answer_id == ans.id).first()
                if eval_item and eval_item.question_id:
                    q_id = eval_item.question_id

            if q_id:
                question_answers.setdefault(q_id, []).append(ans)


        total_pairs_analyzed = 0
        total_flagged_pairs = 0
        paper_similarity_scores: Dict[str, List[Dict[str, Any]]] = {p_id: [] for p_id in paper_ids}

        # Analyze pairwise per question
        for q_id, answers in question_answers.items():
            # Get question info
            question = self.db.query(Question).filter(Question.id == q_id).first()
            q_type = str(question.question_type) if question and question.question_type else ""

            # Exclude objective questions
            if q_type in OBJECTIVE_QUESTION_TYPES:
                continue

            # Compare all pairs (ans_i, ans_j)
            n_ans = len(answers)
            for i in range(n_ans):
                for j in range(i + 1, n_ans):
                    ans_a = answers[i]
                    ans_b = answers[j]

                    # Must be from different answer papers (different students)
                    if ans_a.answer_paper_id == ans_b.answer_paper_id:
                        continue

                    # Check text length requirement
                    text_a = self.normalize_text(ans_a.extracted_text or "")
                    text_b = self.normalize_text(ans_b.extracted_text or "")

                    if len(text_a) < minimum_text_length or len(text_b) < minimum_text_length:
                        continue

                    # Deterministic ordering by ID
                    if ans_a.id > ans_b.id:
                        ans_a, ans_b = ans_b, ans_a
                        text_a, text_b = text_b, text_a

                    lexical_score = self.calculate_lexical_similarity(text_a, text_b)
                    semantic_score = self.calculate_semantic_similarity(text_a, text_b)
                    combined_score = round((lexical_weight * lexical_score) + (semantic_weight * semantic_score), 4)

                    is_flagged = combined_score >= flag_threshold
                    total_pairs_analyzed += 1
                    if is_flagged:
                        total_flagged_pairs += 1

                    # Upsert AnswerSimilarity
                    existing_sim = (
                        self.db.query(AnswerSimilarity)
                        .filter(
                            AnswerSimilarity.source_answer_id == ans_a.id,
                            AnswerSimilarity.target_answer_id == ans_b.id
                        )
                        .first()
                    )

                    if not existing_sim:
                        sim_record = AnswerSimilarity(
                            examination_id=examination_id,
                            question_id=q_id,
                            source_answer_id=ans_a.id,
                            target_answer_id=ans_b.id,
                            similarity_score=combined_score,
                            lexical_score=lexical_score,
                            semantic_score=semantic_score,
                            combined_score=combined_score,
                            flagged_for_review=is_flagged,
                            method="COMBINED_LEXICAL_SEMANTIC"
                        )
                        self.db.add(sim_record)
                    else:
                        existing_sim.similarity_score = combined_score
                        existing_sim.lexical_score = lexical_score
                        existing_sim.semantic_score = semantic_score
                        existing_sim.combined_score = combined_score
                        existing_sim.flagged_for_review = is_flagged

                    # Track metrics for both paper_a and paper_b
                    match_info = {
                        "ans_a_id": ans_a.id,
                        "ans_b_id": ans_b.id,
                        "combined_score": combined_score,
                        "lexical_score": lexical_score,
                        "semantic_score": semantic_score,
                        "is_flagged": is_flagged
                    }
                    paper_similarity_scores[ans_a.answer_paper_id].append(match_info)
                    paper_similarity_scores[ans_b.answer_paper_id].append(match_info)

        # Aggregate PlagiarismResult for each answer paper
        for p_id in paper_ids:
            matches = paper_similarity_scores[p_id]
            if not matches:
                continue

            max_score = max((m["combined_score"] for m in matches), default=0.0)
            max_match = max(matches, key=lambda m: m["combined_score"]) if matches else None
            flagged_matches = [m for m in matches if m["is_flagged"]]

            status_str = "FLAGGED" if flagged_matches else "COMPLETED"

            existing_pr = self.db.query(PlagiarismResult).filter(PlagiarismResult.answer_paper_id == p_id).first()

            ans_a = max_match["ans_a_id"] if max_match else None
            ans_b = max_match["ans_b_id"] if max_match else None

            if not existing_pr:
                pr = PlagiarismResult(
                    examination_id=examination_id,
                    answer_paper_id=p_id,
                    answer_a_id=ans_a,
                    answer_b_id=ans_b,
                    similarity_score=max_score,
                    lexical_score=max_match["lexical_score"] if max_match else 0.0,
                    semantic_score=max_match["semantic_score"] if max_match else 0.0,
                    combined_score=max_score,
                    threshold_used=flag_threshold,
                    analysis_version="v1.0",
                    matching_segments={"flagged_count": len(flagged_matches), "total_comparisons": len(matches)},
                    detection_method="COMBINED_LEXICAL_SEMANTIC",
                    status=status_str
                )
                self.db.add(pr)
            else:
                existing_pr.similarity_score = max_score
                existing_pr.lexical_score = max_match["lexical_score"] if max_match else 0.0
                existing_pr.semantic_score = max_match["semantic_score"] if max_match else 0.0
                existing_pr.combined_score = max_score
                existing_pr.threshold_used = flag_threshold
                existing_pr.answer_a_id = ans_a
                existing_pr.answer_b_id = ans_b
                existing_pr.matching_segments = {"flagged_count": len(flagged_matches), "total_comparisons": len(matches)}
                if existing_pr.status not in ("REVIEWED", "DISMISSED"):
                    existing_pr.status = status_str

        self.db.commit()

        # Log completion audit event
        if user_id:
            audit_end = AuditLog(
                user_id=user_id,
                action=AuditActionEnum.SIMILARITY_ANALYSIS_COMPLETED,
                entity_type="EXAMINATION",
                entity_id=examination_id,
                new_values={"total_pairs_analyzed": total_pairs_analyzed, "total_flagged_pairs": total_flagged_pairs}
            )
            self.db.add(audit_end)
            self.db.commit()


        return {
            "examination_id": examination_id,
            "total_papers": len(answer_papers),
            "analyzed_pairs": total_pairs_analyzed,
            "flagged_cases": total_flagged_pairs,
            "flag_threshold": flag_threshold
        }

    def get_examination_similarity_summary(self, examination_id: str) -> Dict[str, Any]:
        """Retrieves overall similarity analysis summary and flagged results for an examination."""
        examination = self.db.query(Examination).filter(Examination.id == examination_id).first()
        if not examination:
            raise HTTPException(status_code=404, detail="Examination not found")

        answer_papers = self.db.query(AnswerPaper).filter(AnswerPaper.examination_id == examination_id).all()
        plag_results = self.db.query(PlagiarismResult).filter(PlagiarismResult.examination_id == examination_id).all()
        similarities = (
            self.db.query(AnswerSimilarity)
            .filter(AnswerSimilarity.examination_id == examination_id)
            .order_by(AnswerSimilarity.similarity_score.desc())
            .all()
        )

        flagged_count = sum(1 for r in plag_results if r.status == "FLAGGED")
        reviewed_count = sum(1 for r in plag_results if r.status == "REVIEWED")
        dismissed_count = sum(1 for r in plag_results if r.status == "DISMISSED")

        return {
            "examination_id": examination_id,
            "examination_title": examination.name if hasattr(examination, 'name') else "Examination",
            "total_answer_papers": len(answer_papers),

            "analyzed_answer_papers": len(plag_results),
            "total_comparable_answers": len(similarities),
            "flagged_cases_count": flagged_count,
            "reviewed_cases_count": reviewed_count,
            "dismissed_cases_count": dismissed_count,
            "flag_threshold_used": plag_results[0].threshold_used if plag_results and plag_results[0].threshold_used else 0.70,
            "high_similarity_threshold": 0.85,
            "analysis_timestamp": plag_results[0].updated_at if plag_results and plag_results[0].updated_at else None,
            "flagged_results": plag_results,
            "top_similarities": similarities[:50]
        }

    def review_plagiarism_case(
        self,
        result_id: str,
        target_status: str,
        notes: str,
        user_id: str
    ) -> PlagiarismResult:
        """Updates plagiarism result status (REVIEWED or DISMISSED) with mandatory faculty notes."""
        if target_status not in ("REVIEWED", "DISMISSED"):
            raise HTTPException(status_code=400, detail="Target status must be REVIEWED or DISMISSED")

        result = self.db.query(PlagiarismResult).filter(PlagiarismResult.id == result_id).first()
        if not result:
            raise HTTPException(status_code=404, detail="Plagiarism result record not found")

        result.status = target_status
        result.reviewed_by = user_id
        result.reviewed_at = datetime.datetime.utcnow().isoformat()
        result.review_notes = notes

        audit_action = AuditActionEnum.PLAGIARISM_CASE_REVIEWED if target_status == "REVIEWED" else AuditActionEnum.PLAGIARISM_CASE_DISMISSED
        audit = AuditLog(
            user_id=user_id,
            action=audit_action,
            entity_type="PLAGIARISM_RESULT",
            entity_id=result_id,
            new_values={"status": target_status, "notes": notes}
        )
        self.db.add(audit)

        self.db.commit()
        self.db.refresh(result)
        return result
