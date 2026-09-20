from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

try:
    from app.repositories.question_paper_repository import QuestionPaperRepository
    from app.repositories.answer_key_repository import AnswerKeyRepository
    from app.services.question_paper_validation_service import QuestionPaperValidationService
    from app.services.blueprint_validation_service import BlueprintValidationService
    from app.services.answer_key_validation_service import AnswerKeyValidationService
    from app.services.academic_service import AcademicService
    from app.db.models import QuestionPaper, QuestionPaperVersion, AnswerKey, User, AuditLog
    from app.db.models.enums import AuditActionEnum, QuestionPaperStatusEnum, AnswerKeyStatusEnum
    from app.schemas.question_paper_review import (
        PaperReviewChecklistResponse,
        PaperApprovalRequest,
        PaperPublishRequest
    )
except ImportError:
    from backend.app.repositories.question_paper_repository import QuestionPaperRepository
    from backend.app.repositories.answer_key_repository import AnswerKeyRepository
    from backend.app.services.question_paper_validation_service import QuestionPaperValidationService
    from backend.app.services.blueprint_validation_service import BlueprintValidationService
    from backend.app.services.answer_key_validation_service import AnswerKeyValidationService
    from backend.app.services.academic_service import AcademicService
    from backend.app.db.models import QuestionPaper, QuestionPaperVersion, AnswerKey, User, AuditLog
    from backend.app.db.models.enums import AuditActionEnum, QuestionPaperStatusEnum, AnswerKeyStatusEnum
    from backend.app.schemas.question_paper_review import (
        PaperReviewChecklistResponse,
        PaperApprovalRequest,
        PaperPublishRequest
    )

class QuestionPaperReviewService:
    def __init__(self, db: Session):
        self.db = db
        self.paper_repo = QuestionPaperRepository(db)
        self.ak_repo = AnswerKeyRepository(db)
        self.paper_val_service = QuestionPaperValidationService(db)
        self.blueprint_val_service = BlueprintValidationService(db)
        self.ak_val_service = AnswerKeyValidationService(db)
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
                entity_type="QuestionPaper",
                entity_id=entity_id,
                old_values=old_values,
                new_values=new_values,
            )
            self.db.add(audit)
            self.db.commit()
        except Exception:
            self.db.rollback()

    def get_review_checklist(self, paper_id: str) -> PaperReviewChecklistResponse:
        paper = self.paper_repo.get_paper_by_id(paper_id)
        if not paper:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question Paper not found.")

        latest_ver = self.paper_repo.get_latest_version(paper_id)
        if not latest_ver:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Question Paper has no versions.")

        errors: List[str] = []
        warnings: List[str] = []

        # 1. Blueprint validation
        blueprint_valid = True
        if paper.blueprint:
            bp_res = self.blueprint_val_service.validate_blueprint(paper.blueprint)
            blueprint_valid = bp_res.is_valid
            if not bp_res.is_valid:
                errors.extend([f"[Blueprint] {e}" for e in bp_res.errors])
            warnings.extend([f"[Blueprint] {w}" for w in bp_res.warnings])

        # 2. Paper validation
        paper_res = self.paper_val_service.validate_paper_version(paper, latest_ver)
        paper_marks_valid = abs(paper_res.total_marks - paper.total_marks) <= 0.01
        no_duplicate_questions = not any("Duplicate question" in e for e in paper_res.errors)
        all_questions_approved = not any("unapproved status" in e for e in paper_res.errors)

        if not paper_res.is_valid:
            errors.extend([f"[Paper] {e}" for e in paper_res.errors])
        warnings.extend([f"[Paper] {w}" for w in paper_res.warnings])

        # 3. Answer Key validation
        ak = self.ak_repo.get_latest_answer_key(latest_ver.id)
        answer_key_exists = ak is not None
        answer_key_marks_valid = False
        rubrics_valid = True

        if not answer_key_exists:
            errors.append("[AnswerKey] No answer key has been generated for active paper version.")
        else:
            ak_res = self.ak_val_service.validate_answer_key(ak, latest_ver)
            answer_key_marks_valid = ak_res.is_valid
            if not ak_res.is_valid:
                errors.extend([f"[AnswerKey] {e}" for e in ak_res.errors])
            warnings.extend([f"[AnswerKey] {w}" for w in ak_res.warnings])

        is_approvable = len(errors) == 0
        is_publishable = is_approvable and paper.status in [QuestionPaperStatusEnum.APPROVED, QuestionPaperStatusEnum.UNDER_REVIEW, QuestionPaperStatusEnum.GENERATED]

        return PaperReviewChecklistResponse(
            paper_id=paper.id,
            paper_code=paper.paper_code,
            active_version_number=latest_ver.version_number,
            paper_status=paper.status.value if hasattr(paper.status, 'value') else str(paper.status),
            is_approvable=is_approvable,
            is_publishable=is_publishable,
            blueprint_valid=blueprint_valid,
            paper_marks_valid=paper_marks_valid,
            no_duplicate_questions=no_duplicate_questions,
            all_questions_approved=all_questions_approved,
            answer_key_exists=answer_key_exists,
            answer_key_marks_valid=answer_key_marks_valid,
            rubrics_valid=rubrics_valid,
            errors=errors,
            warnings=warnings
        )

    def approve_paper(self, paper_id: str, req: PaperApprovalRequest, current_user: User) -> QuestionPaper:
        paper = self.paper_repo.get_paper_by_id(paper_id)
        if not paper:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question Paper not found.")

        self.academic_service.verify_subject_access(current_user, paper.subject_id, is_write_operation=True)

        checklist = self.get_review_checklist(paper_id)
        if not checklist.is_approvable:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": "Cannot approve question paper due to blocking validation errors.",
                    "errors": checklist.errors
                }
            )

        old_status = paper.status.value if hasattr(paper.status, 'value') else str(paper.status)
        paper.status = QuestionPaperStatusEnum.APPROVED
        self.db.commit()

        # Update active answer key status as well
        latest_ver = self.paper_repo.get_latest_version(paper_id)
        if latest_ver:
            ak = self.ak_repo.get_latest_answer_key(latest_ver.id)
            if ak:
                ak.status = AnswerKeyStatusEnum.APPROVED.value
                ak.approved_by = current_user.id
                self.db.commit()

        self._log_audit(
            action=AuditActionEnum.QUESTION_PAPER_APPROVED,
            user_id=current_user.id,
            entity_id=paper.id,
            old_values={"status": old_status},
            new_values={"status": QuestionPaperStatusEnum.APPROVED.value, "comments": req.comments}
        )

        self.db.refresh(paper)
        return paper

    def publish_paper(self, paper_id: str, req: PaperPublishRequest, current_user: User) -> QuestionPaper:
        paper = self.paper_repo.get_paper_by_id(paper_id)
        if not paper:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question Paper not found.")

        self.academic_service.verify_subject_access(current_user, paper.subject_id, is_write_operation=True)

        checklist = self.get_review_checklist(paper_id)
        if not checklist.is_approvable:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": "Cannot publish question paper due to blocking validation errors.",
                    "errors": checklist.errors
                }
            )

        old_status = paper.status.value if hasattr(paper.status, 'value') else str(paper.status)
        paper.status = QuestionPaperStatusEnum.PUBLISHED
        self.db.commit()

        latest_ver = self.paper_repo.get_latest_version(paper_id)
        if latest_ver:
            ak = self.ak_repo.get_latest_answer_key(latest_ver.id)
            if ak:
                ak.status = AnswerKeyStatusEnum.PUBLISHED.value
                ak.approved_by = current_user.id
                self.db.commit()

        self._log_audit(
            action=AuditActionEnum.QUESTION_PAPER_PUBLISHED,
            user_id=current_user.id,
            entity_id=paper.id,
            old_values={"status": old_status},
            new_values={"status": QuestionPaperStatusEnum.PUBLISHED.value, "notes": req.publish_notes}
        )

        self.db.refresh(paper)
        return paper
