from typing import Optional
from fastapi import APIRouter, Depends, Request, Query, HTTPException, status
from sqlalchemy.orm import Session

try:
    from app.api.deps import (
        get_db,
        get_current_user,
        require_admin,
        verify_student_resource_access
    )
    from app.services.user_service import UserService
    from app.schemas.user import (
        UserCreate,
        UserUpdate,
        UserProfileUpdate,
        UserStatusUpdate,
        UserRoleUpdate,
        UserResponse,
        UserListResponse
    )
    from app.db.models import User, RoleEnum
except ImportError:
    from backend.app.api.deps import (
        get_db,
        get_current_user,
        require_admin,
        verify_student_resource_access
    )
    from backend.app.services.user_service import UserService
    from backend.app.schemas.user import (
        UserCreate,
        UserUpdate,
        UserProfileUpdate,
        UserStatusUpdate,
        UserRoleUpdate,
        UserResponse,
        UserListResponse
    )
    from backend.app.db.models import User, RoleEnum

router = APIRouter(prefix="/users", tags=["User Management"])


@router.patch("/me")
def update_own_profile(
    profile_data: UserProfileUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = UserService(db)
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    updated = service.update_profile(
        current_user,
        profile_data,
        ip_address=ip_address,
        user_agent=user_agent
    )
    return {
        "success": True,
        "data": UserResponse.model_validate(updated)
    }


@router.get("/students/{student_id}/results")
def get_student_results(
    student_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Protected Student Results Endpoint:
    Enforces student ownership check on backend.
    """
    verify_student_resource_access(student_id, current_user)
    
    user_service = UserService(db)
    target_student = user_service.get_user_by_id(student_id)

    return {
        "success": True,
        "data": {
            "student_id": target_student.id,
            "student_name": target_student.full_name,
            "registration_number": target_student.registration_number,
            "examinations": [],
            "performance_summary": {
                "gpa": 3.8,
                "completed_exams": 0
            }
        }
    }


@router.get("", response_model=None)
def list_users(
    search: Optional[str] = Query(None, description="Search by name, email, reg no, or emp id"),
    role: Optional[RoleEnum] = Query(None, description="Filter by user role"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    service = UserService(db)
    users, total = service.list_users(
        search=search,
        role_name=role,
        is_active=is_active,
        page=page,
        page_size=page_size
    )

    items = [UserResponse.model_validate(u) for u in users]
    return {
        "success": True,
        "data": {
            "total": total,
            "items": items,
            "page": page,
            "page_size": page_size
        }
    }


@router.post("")
def create_user(
    user_data: UserCreate,
    request: Request,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    service = UserService(db)
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    created = service.create_user_by_admin(
        user_data,
        admin_id=current_admin.id,
        ip_address=ip_address,
        user_agent=user_agent
    )
    return {
        "success": True,
        "data": UserResponse.model_validate(created)
    }


@router.get("/{user_id}")
def get_user(
    user_id: str,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    service = UserService(db)
    user = service.get_user_by_id(user_id)
    return {
        "success": True,
        "data": UserResponse.model_validate(user)
    }


@router.patch("/{user_id}")
def update_user(
    user_id: str,
    update_data: UserUpdate,
    request: Request,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    service = UserService(db)
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    updated = service.update_user_by_admin(
        user_id,
        update_data,
        admin_id=current_admin.id,
        ip_address=ip_address,
        user_agent=user_agent
    )
    return {
        "success": True,
        "data": UserResponse.model_validate(updated)
    }


@router.delete("/{user_id}")
def deactivate_user(
    user_id: str,
    request: Request,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    service = UserService(db)
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    service.update_user_status(
        user_id,
        UserStatusUpdate(is_active=False),
        admin_id=current_admin.id,
        ip_address=ip_address,
        user_agent=user_agent
    )
    return {
        "success": True,
        "data": {"message": f"User '{user_id}' deactivated successfully"}
    }


@router.patch("/{user_id}/status")
def update_user_status(
    user_id: str,
    status_data: UserStatusUpdate,
    request: Request,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    service = UserService(db)
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    updated = service.update_user_status(
        user_id,
        status_data,
        admin_id=current_admin.id,
        ip_address=ip_address,
        user_agent=user_agent
    )
    return {
        "success": True,
        "data": UserResponse.model_validate(updated)
    }


@router.patch("/{user_id}/role")
def update_user_role(
    user_id: str,
    role_data: UserRoleUpdate,
    request: Request,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    service = UserService(db)
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    updated = service.update_user_role(
        user_id,
        role_data,
        admin_id=current_admin.id,
        ip_address=ip_address,
        user_agent=user_agent
    )
    return {
        "success": True,
        "data": UserResponse.model_validate(updated)
    }
