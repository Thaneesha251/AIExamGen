from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc

try:
    from app.db.models import AnswerKey, AnswerKeyItem
except ImportError:
    from backend.app.db.models import AnswerKey, AnswerKeyItem

class AnswerKeyRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_latest_answer_key(self, question_paper_version_id: str) -> Optional[AnswerKey]:
        return self.db.query(AnswerKey).filter(
            AnswerKey.question_paper_version_id == question_paper_version_id
        ).order_by(desc(AnswerKey.version_number)).first()

    def get_answer_key_by_id(self, key_id: str) -> Optional[AnswerKey]:
        return self.db.query(AnswerKey).filter(AnswerKey.id == key_id).first()

    def get_answer_key_by_version(self, question_paper_version_id: str, version_number: int) -> Optional[AnswerKey]:
        return self.db.query(AnswerKey).filter(
            AnswerKey.question_paper_version_id == question_paper_version_id,
            AnswerKey.version_number == version_number
        ).first()

    def create_answer_key(
        self,
        question_paper_version_id: str,
        version_number: int,
        status: str,
        generated_by: Optional[str],
        items_data: List[Dict[str, Any]]
    ) -> AnswerKey:
        ak = AnswerKey(
            question_paper_version_id=question_paper_version_id,
            version_number=version_number,
            status=status,
            generated_by=generated_by
        )
        self.db.add(ak)
        self.db.flush()

        for idata in items_data:
            item = AnswerKeyItem(
                answer_key_id=ak.id,
                question_paper_item_id=idata["question_paper_item_id"],
                model_answer=idata["model_answer"],
                keywords=idata.get("keywords"),
                concepts=idata.get("concepts"),
                acceptable_answers=idata.get("acceptable_answers"),
                marking_notes=idata.get("marking_notes"),
                maximum_marks=idata["maximum_marks"],
                rubric_id=idata.get("rubric_id")
            )
            self.db.add(item)

        self.db.commit()
        self.db.refresh(ak)
        return ak

    def update_answer_key_item(self, item_id: str, data: Dict[str, Any]) -> Optional[AnswerKeyItem]:
        item = self.db.query(AnswerKeyItem).filter(AnswerKeyItem.id == item_id).first()
        if not item:
            return None
        for k, v in data.items():
            if hasattr(item, k) and v is not None:
                setattr(item, k, v)
        self.db.commit()
        self.db.refresh(item)
        return item
