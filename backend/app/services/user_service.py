from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

try:
    from app.repositories.user_repository import UserRepository
    from app.core.security import get_password_hash
    from app.db.models import User, RoleEnum, AuditLog, AuditActionEnum
    from app.schemas.user import UserCreate, UserUpdate, UserProfileUpdate, UserStatusUpdate, UserRoleUpdate
except ImportError:
    from backend.app.repositories.user_repository import UserRepository
    from backend.app.core.security import get_password_hash
    from backend.app.db.models import User, RoleEnum, AuditLog, AuditActionEnum
    from backend.app.schemas.user import UserCreate, UserUpdate, UserProfileUpdate, UserStatusUpdate, UserRoleUpdate


class UserService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)

    def _log_audit(
        self,
        action: AuditActionEnum,
        admin_id: Optional[str] = None,
        target_user_id: Optional[str] = None,
        old_values: Optional[dict] = None,
        new_values: Optional[dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ):
        try:
            audit = AuditLog(
                user_id=admin_id,
                action=action,
                entity_type="User",
                entity_id=target_user_id,
                old_values=old_values,
                new_values=new_values,
                ip_address=ip_address,
                user_agent=user_agent,
            )
            self.db.add(audit)
            self.db.commit()
        except Exception:
            self.db.rollback()

    def get_user_by_id(self, user_id: str) -> User:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID '{user_id}' not found"
            )
        return user

    def list_users(
        self,
        search: Optional[str] = None,
        role_name: Optional[RoleEnum] = None,
        is_active: Optional[bool] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[User], int]:
        return self.user_repo.search_and_filter(
            search=search,
            role_name=role_name,
            is_active=is_active,
            page=page,
            page_size=page_size
        )

    def create_user_by_admin(
        self,
        user_data: UserCreate,
        admin_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> User:
        if self.user_repo.get_by_email(user_data.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email address is already in use"
            )

        if user_data.registration_number and self.user_repo.get_by_registration_number(user_data.registration_number):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Registration number is already in use"
            )

        if user_data.employee_id and self.user_repo.get_by_employee_id(user_data.employee_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Employee ID is already in use"
            )

        role = self.user_repo.get_role_by_name(user_data.role)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Role '{user_data.role}' not found"
            )

        new_user = User(
            role_id=role.id,
            email=user_data.email,
            password_hash=get_password_hash(user_data.password),
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            registration_number=user_data.registration_number,
            employee_id=user_data.employee_id,
            department_id=user_data.department_id,
            is_active=user_data.is_active
        )

        created_user = self.user_repo.create(new_user)

        self._log_audit(
            action=AuditActionEnum.USER_CREATED,
            admin_id=admin_id,
            target_user_id=created_user.id,
            new_values={
                "email": created_user.email,
                "role": user_data.role.value,
                "first_name": created_user.first_name,
                "last_name": created_user.last_name
            },
            ip_address=ip_address,
            user_agent=user_agent
        )

        return created_user

    def update_user_by_admin(
        self,
        user_id: str,
        update_data: UserUpdate,
        admin_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> User:
        user = self.get_user_by_id(user_id)
        old_values = {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "registration_number": user.registration_number,
            "employee_id": user.employee_id,
            "department_id": user.department_id,
            "is_active": user.is_active
        }

        if update_data.first_name is not None:
            user.first_name = update_data.first_name
        if update_data.last_name is not None:
            user.last_name = update_data.last_name
        if update_data.registration_number is not None:
            if update_data.registration_number != user.registration_number:
                existing = self.user_repo.get_by_registration_number(update_data.registration_number)
                if existing and existing.id != user_id:
                    raise HTTPException(status_code=400, detail="Registration number already in use")
            user.registration_number = update_data.registration_number
        if update_data.employee_id is not None:
            if update_data.employee_id != user.employee_id:
                existing = self.user_repo.get_by_employee_id(update_data.employee_id)
                if existing and existing.id != user_id:
                    raise HTTPException(status_code=400, detail="Employee ID already in use")
            user.employee_id = update_data.employee_id
        if update_data.department_id is not None:
            user.department_id = update_data.department_id
        if update_data.is_active is not None:
            user.is_active = update_data.is_active

        updated_user = self.user_repo.update(user)

        self._log_audit(
            action=AuditActionEnum.USER_UPDATED,
            admin_id=admin_id,
            target_user_id=updated_user.id,
            old_values=old_values,
            new_values={
                "first_name": updated_user.first_name,
                "last_name": updated_user.last_name,
                "is_active": updated_user.is_active
            },
            ip_address=ip_address,
            user_agent=user_agent
        )

        return updated_user

    def update_profile(
        self,
        user: User,
        profile_data: UserProfileUpdate,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> User:
        old_values = {"first_name": user.first_name, "last_name": user.last_name}
        if profile_data.first_name is not None:
            user.first_name = profile_data.first_name
        if profile_data.last_name is not None:
            user.last_name = profile_data.last_name

        updated_user = self.user_repo.update(user)

        self._log_audit(
            action=AuditActionEnum.USER_UPDATED,
            admin_id=user.id,
            target_user_id=user.id,
            old_values=old_values,
            new_values={"first_name": user.first_name, "last_name": user.last_name},
            ip_address=ip_address,
            user_agent=user_agent
        )

        return updated_user

    def update_user_status(
        self,
        user_id: str,
        status_data: UserStatusUpdate,
        admin_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> User:
        user = self.get_user_by_id(user_id)
        old_status = user.is_active
        user.is_active = status_data.is_active

        updated_user = self.user_repo.update(user)

        action = AuditActionEnum.USER_DEACTIVATED if not status_data.is_active else AuditActionEnum.USER_UPDATED
        self._log_audit(
            action=action,
            admin_id=admin_id,
            target_user_id=updated_user.id,
            old_values={"is_active": old_status},
            new_values={"is_active": status_data.is_active},
            ip_address=ip_address,
            user_agent=user_agent
        )

        return updated_user

    def update_user_role(
        self,
        user_id: str,
        role_data: UserRoleUpdate,
        admin_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> User:
        user = self.get_user_by_id(user_id)
        role = self.user_repo.get_role_by_name(role_data.role)
        if not role:
            raise HTTPException(status_code=400, detail=f"Role '{role_data.role}' not found")

        old_role = user.role.name.value if user.role else None
        user.role_id = role.id

        updated_user = self.user_repo.update(user)

        self._log_audit(
            action=AuditActionEnum.ROLE_CHANGED,
            admin_id=admin_id,
            target_user_id=updated_user.id,
            old_values={"role": old_role},
            new_values={"role": role_data.role.value},
            ip_address=ip_address,
            user_agent=user_agent
        )

        return updated_user
