from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc

try:
    from app.db.models import Blueprint, BlueprintRule
    from app.db.models.enums import BlueprintStatusEnum
except ImportError:
    from backend.app.db.models import Blueprint, BlueprintRule
    from backend.app.db.models.enums import BlueprintStatusEnum

class BlueprintRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, blueprint_id: str) -> Optional[Blueprint]:
        return self.db.query(Blueprint).filter(Blueprint.id == blueprint_id).first()

    def list_by_subject(
        self,
        subject_id: str,
        status: Optional[BlueprintStatusEnum] = None,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[Blueprint], int]:
        query = self.db.query(Blueprint).filter(Blueprint.subject_id == subject_id)
        if status:
            query = query.filter(Blueprint.status == status)
        total = query.count()
        items = query.order_by(desc(Blueprint.created_at)).offset(skip).limit(limit).all()
        return items, total

    def list_all(
        self,
        status: Optional[BlueprintStatusEnum] = None,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[Blueprint], int]:
        query = self.db.query(Blueprint)
        if status:
            query = query.filter(Blueprint.status == status)
        total = query.count()
        items = query.order_by(desc(Blueprint.created_at)).offset(skip).limit(limit).all()
        return items, total

    def create(self, blueprint: Blueprint) -> Blueprint:
        self.db.add(blueprint)
        self.db.commit()
        self.db.refresh(blueprint)
        return blueprint

    def update(self, blueprint: Blueprint) -> Blueprint:
        self.db.commit()
        self.db.refresh(blueprint)
        return blueprint

    def delete(self, blueprint: Blueprint) -> None:
        self.db.delete(blueprint)
        self.db.commit()

    # --- SERVICE CONVENIENCE METHODS ---
    def get_blueprint_by_id(self, blueprint_id: str) -> Optional[Blueprint]:
        return self.get_by_id(blueprint_id)

    def create_blueprint(self, blueprint_data: dict, rules_dicts: Optional[List[dict]] = None) -> Blueprint:
        blueprint = Blueprint(**blueprint_data)
        self.db.add(blueprint)
        self.db.flush()
        if rules_dicts:
            for rd in rules_dicts:
                rule = BlueprintRule(blueprint_id=blueprint.id, **rd)
                self.db.add(rule)
        self.db.commit()
        self.db.refresh(blueprint)
        return blueprint

    def list_blueprints(self, subject_id: Optional[str] = None, status_filter: Optional[str] = None) -> List[Blueprint]:
        query = self.db.query(Blueprint)
        if subject_id:
            query = query.filter(Blueprint.subject_id == subject_id)
        if status_filter:
            query = query.filter(Blueprint.status == status_filter)
        return query.order_by(desc(Blueprint.created_at)).all()

    def update_blueprint(self, blueprint_id: str, blueprint_data: dict, rules_dicts: Optional[List[dict]] = None) -> Blueprint:
        bp = self.get_by_id(blueprint_id)
        if not bp:
            return None
        for k, v in blueprint_data.items():
            setattr(bp, k, v)
        if rules_dicts is not None:
            self.db.query(BlueprintRule).filter(BlueprintRule.blueprint_id == blueprint_id).delete()
            for rd in rules_dicts:
                rule = BlueprintRule(blueprint_id=blueprint_id, **rd)
                self.db.add(rule)
        self.db.commit()
        self.db.refresh(bp)
        return bp

    def delete_blueprint(self, blueprint_id: str) -> bool:
        bp = self.get_by_id(blueprint_id)
        if bp:
            self.db.delete(bp)
            self.db.commit()
            return True
        return False

    # --- RULE OPERATIONS ---
    def get_rule_by_id(self, rule_id: str) -> Optional[BlueprintRule]:
        return self.db.query(BlueprintRule).filter(BlueprintRule.id == rule_id).first()

    def create_rule(self, rule: BlueprintRule) -> BlueprintRule:
        self.db.add(rule)
        self.db.commit()
        self.db.refresh(rule)
        return rule

    def update_rule(self, rule: BlueprintRule) -> BlueprintRule:
        self.db.commit()
        self.db.refresh(rule)
        return rule

    def delete_rule(self, rule: BlueprintRule) -> None:
        self.db.delete(rule)
        self.db.commit()
