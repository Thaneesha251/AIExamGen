from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

try:
    from app.repositories.user_repository import UserRepository
    from app.core.security import verify_password, get_password_hash, create_access_token
    from app.db.models import User, RoleEnum, AuditLog, AuditActionEnum
    from app.schemas.auth import LoginRequest, RegisterRequest, ChangePasswordRequest
except ImportError:
    from backend.app.repositories.user_repository import UserRepository
    from backend.app.core.security import verify_password, get_password_hash, create_access_token
    from backend.app.db.models import User, RoleEnum, AuditLog, AuditActionEnum
    from backend.app.schemas.auth import LoginRequest, RegisterRequest, ChangePasswordRequest


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)

    def _log_audit(
        self,
        action: AuditActionEnum,
        user_id: Optional[str] = None,
        entity_id: Optional[str] = None,
        old_values: Optional[dict] = None,
        new_values: Optional[dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ):
        try:
            audit = AuditLog(
                user_id=user_id,
                action=action,
                entity_type="User",
                entity_id=entity_id or user_id,
                old_values=old_values,
                new_values=new_values,
                ip_address=ip_address,
                user_agent=user_agent,
            )
            self.db.add(audit)
            self.db.commit()
        except Exception:
            self.db.rollback()

    def authenticate_user(
        self,
        login_data: LoginRequest,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        user = self.user_repo.get_by_email(login_data.email)
        
        # Generic error message to prevent user enumeration
        generic_error = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

        if not user:
            self._log_audit(
                action=AuditActionEnum.LOGIN_FAILED,
                new_values={"email": login_data.email, "reason": "User not found"},
                ip_address=ip_address,
                user_agent=user_agent
            )
            raise generic_error

        if not user.is_active:
            self._log_audit(
                action=AuditActionEnum.LOGIN_FAILED,
                user_id=user.id,
                new_values={"email": login_data.email, "reason": "Account inactive"},
                ip_address=ip_address,
                user_agent=user_agent
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is inactive. Please contact system administrator."
            )

        if not verify_password(login_data.password, user.password_hash):
            self._log_audit(
                action=AuditActionEnum.LOGIN_FAILED,
                user_id=user.id,
                new_values={"email": login_data.email, "reason": "Incorrect password"},
                ip_address=ip_address,
                user_agent=user_agent
            )
            raise generic_error

        # Successful Login
        token = create_access_token(
            subject=user.email,
            user_id=user.id,
            role=user.role.name.value if user.role else ""
        )

        self._log_audit(
            action=AuditActionEnum.LOGIN,
            user_id=user.id,
            new_values={"email": user.email, "role": user.role.name.value if user.role else ""},
            ip_address=ip_address,
            user_agent=user_agent
        )

        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": user.role.name.value if user.role else "STUDENT",
                "registration_number": user.registration_number,
                "employee_id": user.employee_id
            }
        }

    def register_public_user(
        self,
        reg_data: RegisterRequest,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> User:
        # Check duplicate email
        if self.user_repo.get_by_email(reg_data.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email address is already registered"
            )

        # Check duplicate registration number if provided
        if reg_data.registration_number and self.user_repo.get_by_registration_number(reg_data.registration_number):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Registration number is already in use"
            )

        # Public registration strictly forces STUDENT role
        student_role = self.user_repo.get_role_by_name(RoleEnum.STUDENT)
        if not student_role:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Default student role not configured in database"
            )

        new_user = User(
            role_id=student_role.id,
            email=reg_data.email,
            password_hash=get_password_hash(reg_data.password),
            first_name=reg_data.first_name,
            last_name=reg_data.last_name,
            registration_number=reg_data.registration_number,
            department_id=reg_data.department_id,
            is_active=True
        )

        created_user = self.user_repo.create(new_user)
        self._log_audit(
            action=AuditActionEnum.USER_CREATED,
            user_id=created_user.id,
            new_values={"email": created_user.email, "role": "STUDENT"},
            ip_address=ip_address,
            user_agent=user_agent
        )
        return created_user

    def change_password(
        self,
        user: User,
        pass_data: ChangePasswordRequest,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        if not verify_password(pass_data.current_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )

        if len(pass_data.new_password) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password must be at least 8 characters long"
            )

        user.password_hash = get_password_hash(pass_data.new_password)
        self.user_repo.update(user)

        self._log_audit(
            action=AuditActionEnum.PASSWORD_CHANGE,
            user_id=user.id,
            new_values={"action": "password_updated"},
            ip_address=ip_address,
            user_agent=user_agent
        )

    def logout(self, user_id: str, ip_address: Optional[str] = None, user_agent: Optional[str] = None):
        self._log_audit(
            action=AuditActionEnum.LOGOUT,
            user_id=user_id,
            new_values={"action": "logged_out"},
            ip_address=ip_address,
            user_agent=user_agent
        )
