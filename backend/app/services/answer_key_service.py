from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

try:
    from app.repositories.answer_key_repository import AnswerKeyRepository
    from app.repositories.question_paper_repository import QuestionPaperRepository
    from app.services.answer_key_validation_service import AnswerKeyValidationService
    from app.services.academic_service import AcademicService
    from app.db.models import AnswerKey, AnswerKeyItem, QuestionPaperVersion, Question, User, AuditLog
    from app.db.models.enums import AuditActionEnum, AnswerKeyStatusEnum
    from app.schemas.answer_key import AnswerKeyCreate, AnswerKeyUpdate, AnswerKeyValidationResult, AIDraftAnswerKeyRequest
    from ai.services.llm_service import BaseLLMProvider, MockLLMProvider
except ImportError:
    from backend.app.repositories.answer_key_repository import AnswerKeyRepository
    from backend.app.repositories.question_paper_repository import QuestionPaperRepository
    from backend.app.services.answer_key_validation_service import AnswerKeyValidationService
    from backend.app.services.academic_service import AcademicService
    from backend.app.db.models import AnswerKey, AnswerKeyItem, QuestionPaperVersion, Question, User, AuditLog
    from backend.app.db.models.enums import AuditActionEnum, AnswerKeyStatusEnum
    from backend.app.schemas.answer_key import AnswerKeyCreate, AnswerKeyUpdate, AnswerKeyValidationResult, AIDraftAnswerKeyRequest
    from ai.services.llm_service import BaseLLMProvider, MockLLMProvider

class AnswerKeyService:
    def __init__(self, db: Session, llm_provider: Optional[BaseLLMProvider] = None):
        self.db = db
        self.ak_repo = AnswerKeyRepository(db)
        self.paper_repo = QuestionPaperRepository(db)
        self.val_service = AnswerKeyValidationService(db)
        self.academic_service = AcademicService(db)
        self.llm_provider = llm_provider or MockLLMProvider()

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
                entity_type="AnswerKey",
                entity_id=entity_id,
                old_values=old_values,
                new_values=new_values,
            )
            self.db.add(audit)
            self.db.commit()
        except Exception:
            self.db.rollback()

    def generate_initial_answer_key(
        self,
        question_paper_version_id: str,
        current_user: User
    ) -> AnswerKey:
        ver = self.db.query(QuestionPaperVersion).filter(QuestionPaperVersion.id == question_paper_version_id).first()
        if not ver:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question Paper Version not found.")

        paper = ver.question_paper
        self.academic_service.verify_subject_access(current_user, paper.subject_id, is_write_operation=True)

        existing_ak = self.ak_repo.get_latest_answer_key(question_paper_version_id)
        version_number = (existing_ak.version_number + 1) if existing_ak else 1

        items_data = []
        for pitem in ver.items:
            # Attempt to pull original question if available
            q = pitem.question
            model_ans = ""
            keywords = []
            concepts = []
            acceptable = []
            marking_notes = ""

            if q:
                model_ans = q.expected_answer or ""
                keywords = q.keywords if isinstance(q.keywords, list) else []
                concepts = q.concepts if isinstance(q.concepts, list) else []
                if q.options and isinstance(q.options, dict):
                    correct_opt = q.options.get("correct_option")
                    if correct_opt:
                        acceptable.append(str(correct_opt))
                        if not model_ans:
                            model_ans = f"Correct Option: {correct_opt}"
            else:
                model_ans = f"Model Answer for Question {pitem.question_number}"

            if not model_ans:
                model_ans = f"Solution and detailed explanation for Question {pitem.question_number} ({pitem.marks} marks)."

            marking_notes = f"Award up to {pitem.marks} marks based on completeness, accuracy, and clear presentation."

            items_data.append({
                "question_paper_item_id": pitem.id,
                "model_answer": model_ans,
                "keywords": keywords,
                "concepts": concepts,
                "acceptable_answers": acceptable,
                "marking_notes": marking_notes,
                "maximum_marks": pitem.marks,
                "rubric_id": None
            })

        ak = self.ak_repo.create_answer_key(
            question_paper_version_id=question_paper_version_id,
            version_number=version_number,
            status=AnswerKeyStatusEnum.DRAFT.value,
            generated_by=current_user.id,
            items_data=items_data
        )

        self._log_audit(
            action=AuditActionEnum.ANSWER_KEY_CREATED,
            user_id=current_user.id,
            entity_id=ak.id,
            new_values={"paper_version_id": question_paper_version_id, "version_number": version_number}
        )

        return ak

    def get_answer_key_by_id(self, key_id: str) -> AnswerKey:
        ak = self.ak_repo.get_answer_key_by_id(key_id)
        if not ak:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Answer Key not found.")
        return ak

    def get_latest_answer_key(self, question_paper_version_id: str) -> AnswerKey:
        ak = self.ak_repo.get_latest_answer_key(question_paper_version_id)
        if not ak:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Answer Key not found for this paper version.")
        return ak

    def update_answer_key(
        self,
        key_id: str,
        data: AnswerKeyUpdate,
        current_user: User
    ) -> AnswerKey:
        ak = self.get_answer_key_by_id(key_id)
        paper = ak.question_paper_version.question_paper
        self.academic_service.verify_subject_access(current_user, paper.subject_id, is_write_operation=True)

        if ak.status in [AnswerKeyStatusEnum.APPROVED.value, AnswerKeyStatusEnum.PUBLISHED.value]:
            # Immutable published/approved version: create a new version (vN+1)
            new_ver_num = ak.version_number + 1
            new_items_data = []

            # Merge items
            updated_items_map = {}
            if data.items:
                for item_in in data.items:
                    updated_items_map[item_in.question_paper_item_id] = item_in.model_dump()

            for existing_item in ak.items:
                if existing_item.question_paper_item_id in updated_items_map:
                    idata = updated_items_map[existing_item.question_paper_item_id]
                else:
                    idata = {
                        "question_paper_item_id": existing_item.question_paper_item_id,
                        "model_answer": existing_item.model_answer,
                        "keywords": existing_item.keywords,
                        "concepts": existing_item.concepts,
                        "acceptable_answers": existing_item.acceptable_answers,
                        "marking_notes": existing_item.marking_notes,
                        "maximum_marks": existing_item.maximum_marks,
                        "rubric_id": existing_item.rubric_id
                    }
                new_items_data.append(idata)

            new_ak = self.ak_repo.create_answer_key(
                question_paper_version_id=ak.question_paper_version_id,
                version_number=new_ver_num,
                status=AnswerKeyStatusEnum.DRAFT.value,
                generated_by=current_user.id,
                items_data=new_items_data
            )

            self._log_audit(
                action=AuditActionEnum.ANSWER_KEY_VERSION_CREATED,
                user_id=current_user.id,
                entity_id=new_ak.id,
                new_values={"version_number": new_ver_num, "from_version": ak.version_number}
            )

            return new_ak

        # Draft update in-place
        if data.status:
            ak.status = data.status

        if data.items:
            for item_in in data.items:
                # Find matching existing item
                match_item = next((i for i in ak.items if i.question_paper_item_id == item_in.question_paper_item_id), None)
                if match_item:
                    self.ak_repo.update_answer_key_item(match_item.id, item_in.model_dump(exclude_unset=True))

        self.db.commit()
        self.db.refresh(ak)

        self._log_audit(
            action=AuditActionEnum.ANSWER_KEY_UPDATED,
            user_id=current_user.id,
            entity_id=ak.id
        )

        return ak

    def validate_answer_key_by_id(self, key_id: str) -> AnswerKeyValidationResult:
        ak = self.get_answer_key_by_id(key_id)
        ver = ak.question_paper_version
        return self.val_service.validate_answer_key(ak, ver)
