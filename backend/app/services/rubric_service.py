from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

try:
    from app.repositories.rubric_repository import RubricRepository
    from app.services.rubric_validation_service import RubricValidationService
    from app.services.academic_service import AcademicService
    from app.db.models import Rubric, RubricCriterion, Question, QuestionPaperItem, AnswerKeyItem, User, AuditLog
    from app.db.models.enums import AuditActionEnum
    from app.schemas.rubric import RubricCreate, RubricUpdate, RubricValidationResult, RubricAssignmentRequest
except ImportError:
    from backend.app.repositories.rubric_repository import RubricRepository
    from backend.app.services.rubric_validation_service import RubricValidationService
    from backend.app.services.academic_service import AcademicService
    from backend.app.db.models import Rubric, RubricCriterion, Question, QuestionPaperItem, AnswerKeyItem, User, AuditLog
    from backend.app.db.models.enums import AuditActionEnum
    from backend.app.schemas.rubric import RubricCreate, RubricUpdate, RubricValidationResult, RubricAssignmentRequest

class RubricService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = RubricRepository(db)
        self.val_service = RubricValidationService(db)
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
                entity_type="Rubric",
                entity_id=entity_id,
                old_values=old_values,
                new_values=new_values,
            )
            self.db.add(audit)
            self.db.commit()
        except Exception:
            self.db.rollback()

    def create_rubric(self, data: RubricCreate, current_user: User) -> Rubric:
        if data.subject_id:
            self.academic_service.verify_subject_access(current_user, data.subject_id, is_write_operation=True)

        criteria_dicts = [c.model_dump() for c in data.criteria]
        rubric_dict = data.model_dump(exclude={"criteria"})
        rubric_dict["created_by"] = current_user.id

        rubric = self.repo.create_rubric(rubric_dict, criteria_dicts)

        self._log_audit(
            action=AuditActionEnum.RUBRIC_CREATED,
            user_id=current_user.id,
            entity_id=rubric.id,
            new_values={"name": rubric.name, "total_marks": rubric.total_marks}
        )

        return rubric

    def get_rubric(self, rubric_id: str) -> Rubric:
        rubric = self.repo.get_rubric_by_id(rubric_id)
        if not rubric:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rubric not found.")
        return rubric

    def list_rubrics(
        self,
        subject_id: Optional[str] = None,
        question_type: Optional[str] = None,
        status_filter: Optional[str] = None
    ) -> List[Rubric]:
        return self.repo.list_rubrics(subject_id=subject_id, question_type=question_type, status_filter=status_filter)

    def update_rubric(self, rubric_id: str, data: RubricUpdate, current_user: User) -> Rubric:
        rubric = self.get_rubric(rubric_id)
        if rubric.subject_id:
            self.academic_service.verify_subject_access(current_user, rubric.subject_id, is_write_operation=True)

        if rubric.status in ["APPROVED", "PUBLISHED"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Published or approved rubrics are immutable. Duplicate or create a new rubric version."
            )

        rubric_dict = data.model_dump(exclude={"criteria"}, exclude_unset=True)
        criteria_dicts = [c.model_dump() for c in data.criteria] if data.criteria is not None else None

        updated_r = self.repo.update_rubric(rubric_id, rubric_dict, criteria_dicts)

        self._log_audit(
            action=AuditActionEnum.RUBRIC_UPDATED,
            user_id=current_user.id,
            entity_id=rubric_id
        )

        return updated_r

    def delete_rubric(self, rubric_id: str, current_user: User) -> bool:
        rubric = self.get_rubric(rubric_id)
        if rubric.subject_id:
            self.academic_service.verify_subject_access(current_user, rubric.subject_id, is_write_operation=True)

        success = self.repo.delete_rubric(rubric_id)
        return success

    def assign_rubric(self, rubric_id: str, data: RubricAssignmentRequest, current_user: User) -> Rubric:
        rubric = self.get_rubric(rubric_id)

        target_marks: Optional[float] = None

        if data.question_id:
            q = self.db.query(Question).filter(Question.id == data.question_id).first()
            if not q:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found.")
            target_marks = q.marks
            rubric.question_id = q.id

        if data.question_paper_item_id:
            pi = self.db.query(QuestionPaperItem).filter(QuestionPaperItem.id == data.question_paper_item_id).first()
            if not pi:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question Paper Item not found.")
            target_marks = pi.marks
            rubric.question_paper_item_id = pi.id

        if data.answer_key_item_id:
            aki = self.db.query(AnswerKeyItem).filter(AnswerKeyItem.id == data.answer_key_item_id).first()
            if not aki:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Answer Key Item not found.")
            target_marks = aki.maximum_marks
            aki.rubric_id = rubric.id

        # Validate rubric compatibility with target_marks
        val_res = self.val_service.validate_rubric(rubric, target_item_marks=target_marks)
        if not val_res.is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": "Cannot assign rubric due to mark mismatch or criteria validation errors.",
                    "errors": val_res.errors
                }
            )

        self.db.commit()
        self.db.refresh(rubric)

        self._log_audit(
            action=AuditActionEnum.RUBRIC_ASSIGNED,
            user_id=current_user.id,
            entity_id=rubric.id
        )

        return rubric

    def validate_rubric_by_id(self, rubric_id: str, target_marks: Optional[float] = None) -> RubricValidationResult:
        rubric = self.get_rubric(rubric_id)
        return self.val_service.validate_rubric(rubric, target_item_marks=target_marks)
