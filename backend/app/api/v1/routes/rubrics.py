from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

try:
    from app.api.deps import get_db, get_current_user, require_admin_or_faculty
    from app.services.rubric_service import RubricService
    from app.db.models import User
    from app.schemas.rubric import (
        RubricCreate,
        RubricUpdate,
        RubricResponse,
        RubricValidationResult,
        RubricAssignmentRequest
    )
except ImportError:
    from backend.app.api.deps import get_db, get_current_user, require_admin_or_faculty
    from backend.app.services.rubric_service import RubricService
    from backend.app.db.models import User
    from backend.app.schemas.rubric import (
        RubricCreate,
        RubricUpdate,
        RubricResponse,
        RubricValidationResult,
        RubricAssignmentRequest
    )

router = APIRouter(tags=["Evaluation Rubrics"])

@router.post("/rubrics", response_model=None)
def create_rubric(
    req: RubricCreate,
    user: User = Depends(require_admin_or_faculty),
    db: Session = Depends(get_db)
):
    service = RubricService(db)
    rubric = service.create_rubric(req, user)
    val_res = service.validate_rubric_by_id(rubric.id)
    return {
        "success": True,
        "data": RubricResponse.model_validate(rubric),
        "validation": val_res.model_dump()
    }

@router.get("/rubrics", response_model=None)
def list_rubrics(
    subject_id: Optional[str] = Query(None),
    question_type: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = RubricService(db)
    rubrics = service.list_rubrics(subject_id=subject_id, question_type=question_type, status_filter=status_filter)
    return {
        "success": True,
        "data": [RubricResponse.model_validate(r) for r in rubrics]
    }

@router.get("/rubrics/{rubric_id}", response_model=None)
def get_rubric(
    rubric_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = RubricService(db)
    rubric = service.get_rubric(rubric_id)
    val_res = service.validate_rubric_by_id(rubric_id)
    return {
        "success": True,
        "data": RubricResponse.model_validate(rubric),
        "validation": val_res.model_dump()
    }

@router.put("/rubrics/{rubric_id}", response_model=None)
def update_rubric(
    rubric_id: str,
    req: RubricUpdate,
    user: User = Depends(require_admin_or_faculty),
    db: Session = Depends(get_db)
):
    service = RubricService(db)
    rubric = service.update_rubric(rubric_id, req, user)
    val_res = service.validate_rubric_by_id(rubric.id)
    return {
        "success": True,
        "data": RubricResponse.model_validate(rubric),
        "validation": val_res.model_dump()
    }

@router.delete("/rubrics/{rubric_id}", response_model=None)
def delete_rubric(
    rubric_id: str,
    user: User = Depends(require_admin_or_faculty),
    db: Session = Depends(get_db)
):
    service = RubricService(db)
    success = service.delete_rubric(rubric_id, user)
    return {"success": success, "message": "Rubric deleted successfully."}

@router.post("/rubrics/{rubric_id}/assign", response_model=None)
def assign_rubric(
    rubric_id: str,
    req: RubricAssignmentRequest,
    user: User = Depends(require_admin_or_faculty),
    db: Session = Depends(get_db)
):
    service = RubricService(db)
    rubric = service.assign_rubric(rubric_id, req, user)
    val_res = service.validate_rubric_by_id(rubric.id)
    return {
        "success": True,
        "data": RubricResponse.model_validate(rubric),
        "validation": val_res.model_dump()
    }
