from typing import Optional
from sqlalchemy import String, Text, Integer, Boolean, ForeignKey, Enum as SQLEnum, Index, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base import Base, TimestampMixin
from backend.app.db.guid import GUID, generate_uuid
from backend.app.db.models.enums import SyllabusProcessingStatusEnum

class SyllabusDocument(Base, TimestampMixin):
    __tablename__ = "syllabus_documents"

    id: Mapped[str] = mapped_column(GUID, primary_key=True, default=generate_uuid)
    subject_id: Mapped[str] = mapped_column(GUID, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True)
    uploaded_by: Mapped[str] = mapped_column(GUID, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    file_asset_id: Mapped[str] = mapped_column(GUID, ForeignKey("file_assets.id", ondelete="CASCADE"), nullable=False)
    
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_current: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    
    status: Mapped[SyllabusProcessingStatusEnum] = mapped_column(
        SQLEnum(SyllabusProcessingStatusEnum),
        default=SyllabusProcessingStatusEnum.UPLOADED,
        nullable=False,
        index=True
    )
    processing_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    extracted_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    structured_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    subject: Mapped["Subject"] = relationship("Subject")
    uploader: Mapped["User"] = relationship("User")
    file_asset: Mapped["FileAsset"] = relationship("FileAsset")
