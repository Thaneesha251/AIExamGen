import uuid
from typing import Optional, List
from sqlalchemy import String, Boolean, ForeignKey, Enum as SQLEnum, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base import Base, TimestampMixin
from backend.app.db.guid import GUID, generate_uuid
from backend.app.db.models.enums import RoleEnum

class Role(Base, TimestampMixin):
    __tablename__ = "roles"

    id: Mapped[str] = mapped_column(GUID, primary_key=True, default=generate_uuid)
    name: Mapped[RoleEnum] = mapped_column(SQLEnum(RoleEnum), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    users: Mapped[List["User"]] = relationship("User", back_populates="role")


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(GUID, primary_key=True, default=generate_uuid)
    role_id: Mapped[str] = mapped_column(GUID, ForeignKey("roles.id", ondelete="RESTRICT"), nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    registration_number: Mapped[Optional[str]] = mapped_column(String(50), unique=True, nullable=True, index=True)
    employee_id: Mapped[Optional[str]] = mapped_column(String(50), unique=True, nullable=True, index=True)
    department_id: Mapped[Optional[str]] = mapped_column(GUID, ForeignKey("departments.id", ondelete="SET NULL"), nullable=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    role: Mapped["Role"] = relationship("Role", back_populates="users")
    department: Mapped[Optional["Department"]] = relationship("Department", back_populates="users")

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()
