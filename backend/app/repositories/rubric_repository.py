from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc

try:
    from app.db.models import Rubric, RubricCriterion
except ImportError:
    from backend.app.db.models import Rubric, RubricCriterion

class RubricRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_rubric_by_id(self, rubric_id: str) -> Optional[Rubric]:
        return self.db.query(Rubric).filter(Rubric.id == rubric_id).first()

    def list_rubrics(
        self,
        subject_id: Optional[str] = None,
        question_type: Optional[str] = None,
        status_filter: Optional[str] = None
    ) -> List[Rubric]:
        query = self.db.query(Rubric)
        if subject_id:
            query = query.filter(Rubric.subject_id == subject_id)
        if question_type:
            query = query.filter(Rubric.question_type == question_type)
        if status_filter:
            query = query.filter(Rubric.status == status_filter)
        return query.order_by(desc(Rubric.created_at)).all()

    def create_rubric(
        self,
        rubric_data: Dict[str, Any],
        criteria_data: List[Dict[str, Any]]
    ) -> Rubric:
        rubric = Rubric(**rubric_data)
        self.db.add(rubric)
        self.db.flush()

        for idx, cdata in enumerate(criteria_data):
            cdata_copy = dict(cdata)
            if "order_index" not in cdata_copy or cdata_copy["order_index"] is None:
                cdata_copy["order_index"] = idx
            criterion = RubricCriterion(
                rubric_id=rubric.id,
                criterion=cdata_copy["criterion"],
                description=cdata_copy.get("description"),
                marks=cdata_copy["marks"],
                min_marks=cdata_copy.get("min_marks", 0.0),
                weight=cdata_copy.get("weight", 1.0),
                partial_credit_rules=cdata_copy.get("partial_credit_rules"),
                required=cdata_copy.get("required", True),
                order_index=cdata_copy["order_index"]
            )
            self.db.add(criterion)

        self.db.commit()
        self.db.refresh(rubric)
        return rubric

    def update_rubric(
        self,
        rubric_id: str,
        rubric_data: Dict[str, Any],
        criteria_data: Optional[List[Dict[str, Any]]] = None
    ) -> Optional[Rubric]:
        rubric = self.get_rubric_by_id(rubric_id)
        if not rubric:
            return None

        for k, v in rubric_data.items():
            if hasattr(rubric, k) and v is not None:
                setattr(rubric, k, v)

        if criteria_data is not None:
            # Replace existing criteria
            self.db.query(RubricCriterion).filter(RubricCriterion.rubric_id == rubric_id).delete()
            for idx, cdata in enumerate(criteria_data):
                cdata_copy = dict(cdata)
                criterion = RubricCriterion(
                    rubric_id=rubric.id,
                    criterion=cdata_copy["criterion"],
                    description=cdata_copy.get("description"),
                    marks=cdata_copy["marks"],
                    min_marks=cdata_copy.get("min_marks", 0.0),
                    weight=cdata_copy.get("weight", 1.0),
                    partial_credit_rules=cdata_copy.get("partial_credit_rules"),
                    required=cdata_copy.get("required", True),
                    order_index=cdata_copy.get("order_index", idx)
                )
                self.db.add(criterion)

        self.db.commit()
        self.db.refresh(rubric)
        return rubric

    def delete_rubric(self, rubric_id: str) -> bool:
        rubric = self.get_rubric_by_id(rubric_id)
        if not rubric:
            return False
        self.db.delete(rubric)
        self.db.commit()
        return True
