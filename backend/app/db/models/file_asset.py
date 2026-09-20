from typing import Optional
from sqlalchemy import String, Integer, ForeignKey, Enum as SQLEnum, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base import Base, TimestampMixin
from backend.app.db.guid import GUID, generate_uuid
from backend.app.db.models.enums import FileCategoryEnum

class FileAsset(Base, TimestampMixin):
    __tablename__ = "file_assets"

    id: Mapped[str] = mapped_column(GUID, primary_key=True, default=generate_uuid)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(512), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False, default="application/pdf")
    file_size: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    checksum: Mapped[Optional[str]] = mapped_column(String(64), nullable=True) # SHA-256 hash for integrity
    file_category: Mapped[FileCategoryEnum] = mapped_column(SQLEnum(FileCategoryEnum), nullable=False, default=FileCategoryEnum.OTHER, index=True)
    uploaded_by: Mapped[Optional[str]] = mapped_column(GUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    uploader: Mapped[Optional["User"]] = relationship("User")
