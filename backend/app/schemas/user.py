from typing import Optional, List
from pydantic import BaseModel, EmailStr, ConfigDict, Field
from backend.app.db.models.enums import RoleEnum

class RoleSchema(BaseModel):
    id: str
    name: RoleEnum
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class UserBase(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    registration_number: Optional[str] = None
    employee_id: Optional[str] = None
    department_id: Optional[str] = None
    is_active: bool = True


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=128)
    role: RoleEnum = RoleEnum.STUDENT


class UserUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    registration_number: Optional[str] = None
    employee_id: Optional[str] = None
    department_id: Optional[str] = None
    is_active: Optional[bool] = None


class UserProfileUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)


class UserStatusUpdate(BaseModel):
    is_active: bool


class UserRoleUpdate(BaseModel):
    role: RoleEnum


class UserResponse(UserBase):
    id: str
    role_id: str
    role: Optional[RoleSchema] = None

    model_config = ConfigDict(from_attributes=True)


class UserListResponse(BaseModel):
    total: int
    items: List[UserResponse]
    page: int
    page_size: int
