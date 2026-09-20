from typing import Optional, Any
from pydantic import BaseModel, EmailStr, Field

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)

class UserAuthInfo(BaseModel):
    id: str
    email: str
    first_name: str
    last_name: str
    role: str
    registration_number: Optional[str] = None
    employee_id: Optional[str] = None

class TokenData(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserAuthInfo

class AuthResponse(BaseModel):
    success: bool = True
    data: TokenData

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    registration_number: Optional[str] = None
    department_id: Optional[str] = None
    role: Optional[str] = None # Ignored if ADMIN for public registration

class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=128)
