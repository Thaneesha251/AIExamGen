from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

try:
    from app.api.deps import get_db, get_current_user
    from app.services.auth_service import AuthService
    from app.schemas.auth import (
        LoginRequest,
        RegisterRequest,
        ChangePasswordRequest,
        AuthResponse
    )
    from app.schemas.user import UserResponse
    from app.db.models import User
except ImportError:
    from backend.app.api.deps import get_db, get_current_user
    from backend.app.services.auth_service import AuthService
    from backend.app.schemas.auth import (
        LoginRequest,
        RegisterRequest,
        ChangePasswordRequest,
        AuthResponse
    )
    from backend.app.schemas.user import UserResponse
    from backend.app.db.models import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=AuthResponse)
def login(
    login_data: LoginRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    service = AuthService(db)
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    result = service.authenticate_user(
        login_data,
        ip_address=ip_address,
        user_agent=user_agent
    )
    return {
        "success": True,
        "data": result
    }


@router.post("/register")
def register(
    reg_data: RegisterRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    service = AuthService(db)
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    created_user = service.register_public_user(
        reg_data,
        ip_address=ip_address,
        user_agent=user_agent
    )
    return {
        "success": True,
        "data": UserResponse.model_validate(created_user)
    }


@router.get("/me")
def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    return {
        "success": True,
        "data": UserResponse.model_validate(current_user)
    }


@router.post("/logout")
def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = AuthService(db)
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    service.logout(current_user.id, ip_address=ip_address, user_agent=user_agent)
    return {
        "success": True,
        "data": {"message": "Successfully logged out"}
    }


@router.post("/change-password")
def change_password(
    pass_data: ChangePasswordRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = AuthService(db)
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    service.change_password(
        current_user,
        pass_data,
        ip_address=ip_address,
        user_agent=user_agent
    )
    return {
        "success": True,
        "data": {"message": "Password changed successfully"}
    }
