from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

try:
    from app.api.deps import get_db, get_current_user, require_admin_or_faculty
    from app.services.blueprint_service import BlueprintService
    from app.db.models import User, BlueprintStatusEnum
    from app.schemas.blueprint import (
        BlueprintCreate,
        BlueprintUpdate,
        BlueprintResponse,
        BlueprintValidationResult
    )
except ImportError:
    from backend.app.api.deps import get_db, get_current_user, require_admin_or_faculty
    from backend.app.services.blueprint_service import BlueprintService
    from backend.app.db.models import User, BlueprintStatusEnum
    from backend.app.schemas.blueprint import (
        BlueprintCreate,
        BlueprintUpdate,
        BlueprintResponse,
        BlueprintValidationResult
    )

router = APIRouter(tags=["Exam Blueprints"])

@router.post("/blueprints", response_model=None)
def create_blueprint(
    req: BlueprintCreate,
    user: User = Depends(require_admin_or_faculty),
    db: Session = Depends(get_db)
):
    service = BlueprintService(db)
    bp = service.create_blueprint(req, user)
    val_res = service.validate_blueprint_by_id(bp.id)
    return {
        "success": True,
        "data": BlueprintResponse.model_validate(bp),
        "validation": val_res.model_dump()
    }

@router.get("/blueprints", response_model=None)
def list_blueprints(
    subject_id: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = BlueprintService(db)
    bps = service.list_blueprints(subject_id=subject_id, status_filter=status_filter, current_user=user)
    return {
        "success": True,
        "data": [BlueprintResponse.model_validate(bp) for bp in bps]
    }

@router.get("/blueprints/{blueprint_id}", response_model=None)
def get_blueprint(
    blueprint_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = BlueprintService(db)
    bp = service.get_blueprint(blueprint_id)
    val_res = service.validate_blueprint_by_id(blueprint_id)
    return {
        "success": True,
        "data": BlueprintResponse.model_validate(bp),
        "validation": val_res.model_dump()
    }

@router.put("/blueprints/{blueprint_id}", response_model=None)
def update_blueprint(
    blueprint_id: str,
    req: BlueprintUpdate,
    user: User = Depends(require_admin_or_faculty),
    db: Session = Depends(get_db)
):
    service = BlueprintService(db)
    bp = service.update_blueprint(blueprint_id, req, user)
    val_res = service.validate_blueprint_by_id(bp.id)
    return {
        "success": True,
        "data": BlueprintResponse.model_validate(bp),
        "validation": val_res.model_dump()
    }

@router.delete("/blueprints/{blueprint_id}", response_model=None)
def delete_blueprint(
    blueprint_id: str,
    user: User = Depends(require_admin_or_faculty),
    db: Session = Depends(get_db)
):
    service = BlueprintService(db)
    success = service.delete_blueprint(blueprint_id, user)
    return {"success": success, "message": "Blueprint deleted or archived successfully."}

@router.post("/blueprints/{blueprint_id}/validate", response_model=None)
def validate_blueprint(
    blueprint_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = BlueprintService(db)
    val_res = service.validate_blueprint_by_id(blueprint_id)
    return {
        "success": True,
        "data": val_res.model_dump()
    }
