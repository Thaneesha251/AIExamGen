from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
try:
    from app.db.models import AuditLog, AuditActionEnum
except ImportError:
    from backend.app.db.models import AuditLog, AuditActionEnum

class AuditLogService:
    """Centralized service for creating audit log entries across all business services."""

    def __init__(self, db: Session):
        self.db = db

    def log_action(
        self,
        action: AuditActionEnum,
        user_id: Optional[str] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuditLog:
        try:
            combined_new = dict(new_values or {})
            if details:
                combined_new["details"] = details

            audit = AuditLog(
                user_id=user_id,
                action=action,
                entity_type=entity_type or "System",
                entity_id=entity_id,
                old_values=old_values,
                new_values=combined_new if combined_new else None,
                ip_address=ip_address,
                user_agent=user_agent
            )
            self.db.add(audit)
            self.db.commit()
            return audit
        except Exception:
            self.db.rollback()
            return None
