from typing import Generator, List, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

try:
    from app.db.session import SessionLocal
    from app.core.security import decode_access_token
    from app.repositories.user_repository import UserRepository
    from app.db.models import User, RoleEnum
except ImportError:
    from backend.app.db.session import SessionLocal
    from backend.app.core.security import decode_access_token
    from backend.app.repositories.user_repository import UserRepository
    from backend.app.db.models import User, RoleEnum


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    db: Session = Depends(get_db),
    token: Optional[str] = Depends(oauth2_scheme)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not token:
        raise credentials_exception

    payload = decode_access_token(token)
    if not payload:
        raise credentials_exception

    user_id: Optional[str] = payload.get("user_id")
    sub: Optional[str] = payload.get("sub")

    if not user_id and not sub:
        raise credentials_exception

    user_repo = UserRepository(db)
    user = None
    if user_id:
        user = user_repo.get_by_id(user_id)
    if not user and sub:
        user = user_repo.get_by_email(sub)

    if not user:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive"
        )

    return user


class RoleChecker:
    def __init__(self, allowed_roles: List[RoleEnum]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        if not current_user.role or current_user.role.name not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operation not permitted for your assigned role"
            )
        return current_user


require_admin = RoleChecker([RoleEnum.ADMIN])
require_faculty = RoleChecker([RoleEnum.FACULTY])
require_student = RoleChecker([RoleEnum.STUDENT])
require_admin_or_faculty = RoleChecker([RoleEnum.ADMIN, RoleEnum.FACULTY])


def verify_student_resource_access(target_student_id: str, current_user: User) -> None:
    """
    Enforce backend security boundary:
    STUDENT role can ONLY access their own resource.
    ADMIN and FACULTY can access student resources where authorized.
    """
    if current_user.role and current_user.role.name == RoleEnum.STUDENT:
        if current_user.id != target_student_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Students can only access their own records"
            )
