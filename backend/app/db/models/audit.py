from typing import Optional
from sqlalchemy import String, ForeignKey, Enum as SQLEnum, Index, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base import Base, TimestampMixin
from backend.app.db.guid import GUID, generate_uuid
from backend.app.db.models.enums import AuditActionEnum

class AuditLog(Base, TimestampMixin):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(GUID, primary_key=True, default=generate_uuid)
    user_id: Mapped[Optional[str]] = mapped_column(GUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action: Mapped[AuditActionEnum] = mapped_column(SQLEnum(AuditActionEnum), nullable=False, index=True)

    entity_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True) # e.g. "QuestionPaper", "Evaluation"
    entity_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)

    old_values: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True) # JSON snapshot of old state
    new_values: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True) # JSON snapshot of new state

    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    user: Mapped[Optional["User"]] = relationship("User")
