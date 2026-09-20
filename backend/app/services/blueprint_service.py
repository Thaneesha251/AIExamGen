from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

try:
    from app.repositories.blueprint_repository import BlueprintRepository
    from app.services.blueprint_validation_service import BlueprintValidationService
    from app.services.academic_service import AcademicService
    from app.db.models import Blueprint, BlueprintRule, User, AuditLog
    from app.db.models.enums import AuditActionEnum, BlueprintStatusEnum
    from app.schemas.blueprint import BlueprintCreate, BlueprintUpdate, BlueprintValidationResult
except ImportError:
    from backend.app.repositories.blueprint_repository import BlueprintRepository
    from backend.app.services.blueprint_validation_service import BlueprintValidationService
    from backend.app.services.academic_service import AcademicService
    from backend.app.db.models import Blueprint, BlueprintRule, User, AuditLog
    from backend.app.db.models.enums import AuditActionEnum, BlueprintStatusEnum
    from backend.app.schemas.blueprint import BlueprintCreate, BlueprintUpdate, BlueprintValidationResult

class BlueprintService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = BlueprintRepository(db)
        self.validation_service = BlueprintValidationService(db)
        self.academic_service = AcademicService(db)

    def _log_audit(
        self,
        action: AuditActionEnum,
        user_id: Optional[str] = None,
        entity_id: Optional[str] = None,
        old_values: Optional[dict] = None,
        new_values: Optional[dict] = None,
    ):
        try:
            audit = AuditLog(
                user_id=user_id,
                action=action,
                entity_type="Blueprint",
                entity_id=entity_id,
                old_values=old_values,
                new_values=new_values,
            )
            self.db.add(audit)
            self.db.commit()
        except Exception:
            self.db.rollback()

    def create_blueprint(self, data: BlueprintCreate, current_user: User) -> Blueprint:
        self.academic_service.verify_subject_access(current_user, data.subject_id, is_write_operation=True)

        rules_dicts = [r.model_dump() for r in data.rules]
        blueprint_data = data.model_dump(exclude={"rules"})

        blueprint = self.repo.create_blueprint(blueprint_data, rules_dicts)

        self._log_audit(
            action=AuditActionEnum.BLUEPRINT_CREATED,
            user_id=current_user.id,
            entity_id=blueprint.id,
            new_values={"name": blueprint.name, "subject_id": blueprint.subject_id}
        )

        return blueprint

    def get_blueprint(self, blueprint_id: str) -> Blueprint:
        bp = self.repo.get_blueprint_by_id(blueprint_id)
        if not bp:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Blueprint '{blueprint_id}' not found.")
        return bp

    def list_blueprints(
        self,
        subject_id: Optional[str] = None,
        status_filter: Optional[str] = None,
        current_user: Optional[User] = None
    ) -> List[Blueprint]:
        if subject_id and current_user:
            self.academic_service.verify_subject_access(current_user, subject_id, is_write_operation=False)
        return self.repo.list_blueprints(subject_id=subject_id, status_filter=status_filter)

    def update_blueprint(self, blueprint_id: str, data: BlueprintUpdate, current_user: User) -> Blueprint:
        bp = self.get_blueprint(blueprint_id)
        self.academic_service.verify_subject_access(current_user, bp.subject_id, is_write_operation=True)

        old_vals = {"name": bp.name, "total_marks": bp.total_marks, "status": bp.status}

        blueprint_data = data.model_dump(exclude={"rules"}, exclude_unset=True)
        rules_dicts = [r.model_dump() for r in data.rules] if data.rules is not None else None

        updated_bp = self.repo.update_blueprint(blueprint_id, blueprint_data, rules_dicts)

        self._log_audit(
            action=AuditActionEnum.BLUEPRINT_UPDATED,
            user_id=current_user.id,
            entity_id=blueprint_id,
            old_values=old_vals,
            new_values={"name": updated_bp.name, "total_marks": updated_bp.total_marks, "status": updated_bp.status}
        )

        return updated_bp

    def delete_blueprint(self, blueprint_id: str, current_user: User) -> bool:
        bp = self.get_blueprint(blueprint_id)
        self.academic_service.verify_subject_access(current_user, bp.subject_id, is_write_operation=True)

        # Check if blueprint is linked to any question papers
        if bp.question_papers:
            # Soft delete (archive) if linked
            bp.status = BlueprintStatusEnum.ARCHIVED
            self.db.commit()
            self._log_audit(
                action=AuditActionEnum.BLUEPRINT_UPDATED,
                user_id=current_user.id,
                entity_id=blueprint_id,
                new_values={"status": BlueprintStatusEnum.ARCHIVED}
            )
            return True

        res = self.repo.delete_blueprint(blueprint_id)
        if res:
            self._log_audit(
                action=AuditActionEnum.BLUEPRINT_DELETED,
                user_id=current_user.id,
                entity_id=blueprint_id
            )
        return res

    def validate_blueprint_by_id(self, blueprint_id: str) -> BlueprintValidationResult:
        bp = self.get_blueprint(blueprint_id)
        res = self.validation_service.validate_blueprint(bp)
        return res
