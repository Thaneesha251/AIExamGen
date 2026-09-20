"""
Similarity service for detecting duplicate questions within a subject question bank.
Combines Cosine TF-IDF token similarity with character n-gram Jaccard similarity.
"""

from typing import List, Dict, Any, Optional, Tuple
from ai.services.embedding_service import LocalEmbeddingService

class QuestionSimilarityService:
    """Service to evaluate question novelty and find duplicate questions in an existing pool."""

    def __init__(self, duplicate_threshold: float = 0.75):
        self.duplicate_threshold = duplicate_threshold

    def calculate_similarity(self, text1: str, text2: str) -> float:
        """Combines cosine token similarity and character n-gram Jaccard similarity."""
        cosine_sim = LocalEmbeddingService.cosine_similarity(text1, text2)
        jaccard_sim = LocalEmbeddingService.jaccard_similarity(text1, text2)
        
        # Weighted blend: 60% cosine word match, 40% jaccard n-gram match
        combined = (0.6 * cosine_sim) + (0.4 * jaccard_sim)
        return round(float(combined), 4)

    def find_most_similar_question(
        self,
        candidate_text: str,
        existing_questions: List[Dict[str, Any]]
    ) -> Tuple[float, Optional[str], Optional[Dict[str, Any]]]:
        """
        Compares candidate question text against a list of existing questions.
        Returns (max_similarity_score, most_similar_question_id, most_similar_question_dict).
        """
        max_score = 0.0
        most_similar_id = None
        most_similar_q = None

        for q in existing_questions:
            q_text = q.get("question_text", "")
            if not q_text:
                continue
            
            sim = self.calculate_similarity(candidate_text, q_text)
            if sim > max_score:
                max_score = sim
                most_similar_id = q.get("id")
                most_similar_q = q

        return max_score, most_similar_id, most_similar_q
