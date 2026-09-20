from typing import Optional, List, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_

try:
    from app.db.models import User, Role, RoleEnum
except ImportError:
    from backend.app.db.models import User, Role, RoleEnum


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: str) -> Optional[User]:
        return (
            self.db.query(User)
            .options(joinedload(User.role), joinedload(User.department))
            .filter(User.id == user_id)
            .first()
        )

    def get_by_email(self, email: str) -> Optional[User]:
        return (
            self.db.query(User)
            .options(joinedload(User.role), joinedload(User.department))
            .filter(User.email == email)
            .first()
        )

    def get_by_registration_number(self, reg_num: str) -> Optional[User]:
        if not reg_num:
            return None
        return self.db.query(User).filter(User.registration_number == reg_num).first()

    def get_by_employee_id(self, emp_id: str) -> Optional[User]:
        if not emp_id:
            return None
        return self.db.query(User).filter(User.employee_id == emp_id).first()

    def get_role_by_name(self, role_name: RoleEnum) -> Optional[Role]:
        return self.db.query(Role).filter(Role.name == role_name).first()

    def list_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        return (
            self.db.query(User)
            .options(joinedload(User.role), joinedload(User.department))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def search_and_filter(
        self,
        search: Optional[str] = None,
        role_name: Optional[RoleEnum] = None,
        is_active: Optional[bool] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[User], int]:
        query = self.db.query(User).options(joinedload(User.role), joinedload(User.department))

        if role_name:
            query = query.join(User.role).filter(Role.name == role_name)

        if is_active is not None:
            query = query.filter(User.is_active == is_active)

        if search:
            search_pattern = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    User.first_name.ilike(search_pattern),
                    User.last_name.ilike(search_pattern),
                    User.email.ilike(search_pattern),
                    User.registration_number.ilike(search_pattern),
                    User.employee_id.ilike(search_pattern),
                )
            )

        total = query.count()
        offset = (page - 1) * page_size
        users = query.order_by(User.created_at.desc()).offset(offset).limit(page_size).all()
        return users, total

    def create(self, user: User) -> User:
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return self.get_by_id(user.id) or user

    def update(self, user: User) -> User:
        self.db.commit()
        self.db.refresh(user)
        return self.get_by_id(user.id) or user
