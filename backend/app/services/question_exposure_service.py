from typing import Dict, List
from sqlalchemy.orm import Session
from sqlalchemy import func

try:
    from app.db.models import QuestionPaperItem
except ImportError:
    from backend.app.db.models import QuestionPaperItem

class QuestionExposureService:
    def __init__(self, db: Session):
        self.db = db

    def get_exposure_counts(self, question_ids: List[str]) -> Dict[str, int]:
        """
        Returns a mapping of question_id -> count of times it was used across paper items.
        """
        if not question_ids:
            return {}

        results = self.db.query(
            QuestionPaperItem.question_id,
            func.count(QuestionPaperItem.id).label("usage_count")
        ).filter(
            QuestionPaperItem.question_id.in_(question_ids)
        ).group_by(
            QuestionPaperItem.question_id
        ).all()

        counts = {q_id: 0 for q_id in question_ids}
        for q_id, count in results:
            if q_id:
                counts[q_id] = count
        return counts
