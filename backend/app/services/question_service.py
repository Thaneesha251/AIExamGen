import csv
import io
from typing import Optional, List, Tuple, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

try:
    from app.repositories.question_repository import QuestionRepository
    from app.repositories.academic_repository import AcademicRepository
    from app.services.academic_service import AcademicService
    from app.db.models import (
        User,
        Question,
        QuestionVersion,
        QuestionBank,
        AuditLog,
        AuditActionEnum,
        QuestionStatusEnum,
        QuestionTypeEnum,
        DifficultyLevelEnum,
        BloomLevelEnum,
    )
    from app.schemas.question import (
        QuestionCreate,
        QuestionUpdate,
        QuestionStatusUpdate,
    )
    from app.schemas.question_bank import (
        QuestionBankCreate,
        QuestionBankUpdate,
        AddQuestionsToBankRequest,
    )
    from ai.agents.question_validation_agent import QuestionValidationAgent
    from app.schemas.question_generation import GeneratedQuestionSchema
except ImportError:
    from backend.app.repositories.question_repository import QuestionRepository
    from backend.app.repositories.academic_repository import AcademicRepository
    from backend.app.services.academic_service import AcademicService
    from backend.app.db.models import (
        User,
        Question,
        QuestionVersion,
        QuestionBank,
        AuditLog,
        AuditActionEnum,
        QuestionStatusEnum,
        QuestionTypeEnum,
        DifficultyLevelEnum,
        BloomLevelEnum,
    )
    from backend.app.schemas.question import (
        QuestionCreate,
        QuestionUpdate,
        QuestionStatusUpdate,
    )
    from backend.app.schemas.question_bank import (
        QuestionBankCreate,
        QuestionBankUpdate,
        AddQuestionsToBankRequest,
    )
    from ai.agents.question_validation_agent import QuestionValidationAgent
    from backend.app.schemas.question_generation import GeneratedQuestionSchema


class QuestionService:
    def __init__(self, db: Session):
        self.db = db
        self.question_repo = QuestionRepository(db)
        self.academic_repo = AcademicRepository(db)
        self.academic_service = AcademicService(db)
        self.validation_agent = QuestionValidationAgent()

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
                entity_type="Question",
                entity_id=entity_id,
                old_values=old_values,
                new_values=new_values,
            )
            self.db.add(audit)
            self.db.commit()
        except Exception:
            self.db.rollback()

    def create_question(self, req: QuestionCreate, user: User) -> Question:
        # 1. Access control check
        self.academic_service.verify_subject_access(user, req.subject_id, is_write_operation=True)

        # 2. Validate MCQ rules
        if req.question_type == QuestionTypeEnum.MCQ:
            if not req.options or not isinstance(req.options, dict):
                raise HTTPException(status_code=400, detail="MCQ questions must include options.")
            opts = req.options.get("options", [])
            correct = req.options.get("correct_option")
            if not opts or len(opts) < 4:
                raise HTTPException(status_code=400, detail="MCQ questions must have at least 4 options.")
            if not correct:
                raise HTTPException(status_code=400, detail="MCQ questions must specify a correct_option.")

        # 3. Validation Agent check
        gen_schema = GeneratedQuestionSchema(
            question_text=req.question_text,
            question_type=req.question_type,
            marks=req.marks,
            difficulty=req.difficulty,
            bloom_level=req.bloom_level,
            expected_answer=req.expected_answer,
            options=req.options,
            keywords=req.keywords or [],
            concepts=req.concepts or []
        )
        
        # Pull existing pool for duplicate check
        existing_qs, _ = self.question_repo.search_questions(subject_id=req.subject_id, limit=500)
        pool = [{"id": q.id, "question_text": q.question_text} for q in existing_qs]
        val_res = self.validation_agent.validate_question(gen_schema, pool)

        # 4. Construct Question entity
        question = Question(
            subject_id=req.subject_id,
            unit_id=req.unit_id,
            topic_id=req.topic_id,
            learning_outcome_id=req.learning_outcome_id,
            question_text=req.question_text,
            question_type=req.question_type,
            marks=req.marks,
            difficulty=req.difficulty,
            bloom_level=req.bloom_level,
            expected_answer=req.expected_answer,
            options=req.options,
            keywords=req.keywords,
            concepts=req.concepts,
            source=req.source or "MANUAL",
            status=req.status or QuestionStatusEnum.ACTIVE,
            version=1,
            validation_data=val_res.model_dump(),
            created_by=user.id
        )

        created_q = self.question_repo.create(question)

        # 5. Create initial QuestionVersion (v1)
        v1 = QuestionVersion(
            question_id=created_q.id,
            version_number=1,
            question_text=created_q.question_text,
            marks=created_q.marks,
            difficulty=created_q.difficulty,
            bloom_level=created_q.bloom_level,
            expected_answer=created_q.expected_answer,
            options=created_q.options,
            keywords=created_q.keywords,
            concepts=created_q.concepts,
            changed_by=user.id,
            change_reason="Initial manual creation"
        )
        self.question_repo.create_version(v1)

        self._log_audit(
            AuditActionEnum.QUESTION_CREATED,
            user_id=user.id,
            entity_id=created_q.id,
            new_values={"question_text": created_q.question_text[:50], "status": created_q.status.value}
        )

        return self.get_question(created_q.id, user)

    def get_question(self, question_id: str, user: User) -> Question:
        q = self.question_repo.get_by_id(question_id)
        if not q:
            raise HTTPException(status_code=404, detail="Question not found")
        self.academic_service.verify_subject_access(user, q.subject_id, is_write_operation=False)
        return q

    def search_questions(
        self,
        user: User,
        subject_id: Optional[str] = None,
        unit_id: Optional[str] = None,
        topic_id: Optional[str] = None,
        learning_outcome_id: Optional[str] = None,
        question_type: Optional[QuestionTypeEnum] = None,
        difficulty: Optional[DifficultyLevelEnum] = None,
        bloom_level: Optional[BloomLevelEnum] = None,
        status: Optional[QuestionStatusEnum] = None,
        source: Optional[str] = None,
        search_query: Optional[str] = None,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[Question], int]:
        if subject_id:
            self.academic_service.verify_subject_access(user, subject_id, is_write_operation=False)
        return self.question_repo.search_questions(
            subject_id=subject_id,
            unit_id=unit_id,
            topic_id=topic_id,
            learning_outcome_id=learning_outcome_id,
            question_type=question_type,
            difficulty=difficulty,
            bloom_level=bloom_level,
            status=status,
            source=source,
            search_query=search_query,
            skip=skip,
            limit=limit
        )

    def update_question(self, question_id: str, req: QuestionUpdate, user: User) -> Question:
        q = self.question_repo.get_by_id(question_id)
        if not q:
            raise HTTPException(status_code=404, detail="Question not found")

        self.academic_service.verify_subject_access(user, q.subject_id, is_write_operation=True)

        old_values = {
            "question_text": q.question_text,
            "marks": q.marks,
            "difficulty": q.difficulty.value,
            "bloom_level": q.bloom_level.value,
            "version": q.version
        }

        content_changed = False

        if req.subject_id and req.subject_id != q.subject_id:
            self.academic_service.verify_subject_access(user, req.subject_id, is_write_operation=True)
            q.subject_id = req.subject_id
        if req.unit_id is not None:
            q.unit_id = req.unit_id
        if req.topic_id is not None:
            q.topic_id = req.topic_id
        if req.learning_outcome_id is not None:
            q.learning_outcome_id = req.learning_outcome_id

        if req.question_text is not None and req.question_text != q.question_text:
            q.question_text = req.question_text
            content_changed = True
        if req.question_type is not None and req.question_type != q.question_type:
            q.question_type = req.question_type
            content_changed = True
        if req.marks is not None and req.marks != q.marks:
            q.marks = req.marks
            content_changed = True
        if req.difficulty is not None and req.difficulty != q.difficulty:
            q.difficulty = req.difficulty
            content_changed = True
        if req.bloom_level is not None and req.bloom_level != q.bloom_level:
            q.bloom_level = req.bloom_level
            content_changed = True
        if req.expected_answer is not None and req.expected_answer != q.expected_answer:
            q.expected_answer = req.expected_answer
            content_changed = True
        if req.options is not None and req.options != q.options:
            q.options = req.options
            content_changed = True
        if req.keywords is not None:
            q.keywords = req.keywords
        if req.concepts is not None:
            q.concepts = req.concepts
        if req.status is not None:
            q.status = req.status

        # If content changed, increment version and create a new QuestionVersion record
        if content_changed:
            q.version += 1
            version_record = QuestionVersion(
                question_id=q.id,
                version_number=q.version,
                question_text=q.question_text,
                marks=q.marks,
                difficulty=q.difficulty,
                bloom_level=q.bloom_level,
                expected_answer=q.expected_answer,
                options=q.options,
                keywords=q.keywords,
                concepts=q.concepts,
                changed_by=user.id,
                change_reason=req.change_reason or "Faculty edit"
            )
            self.question_repo.create_version(version_record)

        # Re-run validation agent
        gen_schema = GeneratedQuestionSchema(
            question_text=q.question_text,
            question_type=q.question_type,
            marks=q.marks,
            difficulty=q.difficulty,
            bloom_level=q.bloom_level,
            expected_answer=q.expected_answer,
            options=q.options,
            keywords=q.keywords or [],
            concepts=q.concepts or []
        )
        existing_qs, _ = self.question_repo.search_questions(subject_id=q.subject_id, limit=500)
        pool = [{"id": ex.id, "question_text": ex.question_text} for ex in existing_qs if ex.id != q.id]
        val_res = self.validation_agent.validate_question(gen_schema, pool)
        q.validation_data = val_res.model_dump()

        updated_q = self.question_repo.update(q)

        self._log_audit(
            AuditActionEnum.QUESTION_UPDATED,
            user_id=user.id,
            entity_id=updated_q.id,
            old_values=old_values,
            new_values={"version": updated_q.version, "status": updated_q.status.value}
        )

        return self.get_question(updated_q.id, user)

    def update_status(self, question_id: str, status_update: QuestionStatusUpdate, user: User) -> Question:
        q = self.question_repo.get_by_id(question_id)
        if not q:
            raise HTTPException(status_code=404, detail="Question not found")

        self.academic_service.verify_subject_access(user, q.subject_id, is_write_operation=True)

        old_status = q.status.value
        q.status = status_update.status
        updated_q = self.question_repo.update(q)

        action = AuditActionEnum.QUESTION_UPDATED
        if status_update.status == QuestionStatusEnum.APPROVED:
            action = AuditActionEnum.QUESTION_APPROVED
        elif status_update.status == QuestionStatusEnum.REJECTED:
            action = AuditActionEnum.QUESTION_REJECTED

        self._log_audit(
            action,
            user_id=user.id,
            entity_id=updated_q.id,
            old_values={"status": old_status},
            new_values={"status": updated_q.status.value, "reason": status_update.reason}
        )

        return self.get_question(updated_q.id, user)

    def import_csv_questions(self, subject_id: str, file_bytes: bytes, user: User) -> Dict[str, Any]:
        self.academic_service.verify_subject_access(user, subject_id, is_write_operation=True)

        text_content = file_bytes.decode("utf-8", errors="replace")
        csv_file = io.StringIO(text_content)
        reader = csv.DictReader(csv_file)

        created_count = 0
        failed_count = 0
        errors: List[str] = []

        for row_idx, row in enumerate(reader, start=1):
            try:
                q_text = row.get("question_text", "").strip()
                if not q_text:
                    failed_count += 1
                    errors.append(f"Row {row_idx}: Missing question_text")
                    continue

                q_type_str = row.get("question_type", "SHORT_ANSWER").strip().upper()
                try:
                    q_type = QuestionTypeEnum(q_type_str)
                except ValueError:
                    q_type = QuestionTypeEnum.SHORT_ANSWER

                diff_str = row.get("difficulty", "MEDIUM").strip().upper()
                try:
                    diff = DifficultyLevelEnum(diff_str)
                except ValueError:
                    diff = DifficultyLevelEnum.MEDIUM

                bloom_str = row.get("bloom_level", "UNDERSTAND").strip().upper()
                try:
                    bloom = BloomLevelEnum(bloom_str)
                except ValueError:
                    bloom = BloomLevelEnum.UNDERSTAND

                try:
                    marks = float(row.get("marks", 5.0))
                except ValueError:
                    marks = 5.0

                exp_ans = row.get("expected_answer", "").strip() or None
                options_dict = None

                if q_type == QuestionTypeEnum.MCQ:
                    opt_a = row.get("option_a", "").strip()
                    opt_b = row.get("option_b", "").strip()
                    opt_c = row.get("option_c", "").strip()
                    opt_d = row.get("option_d", "").strip()
                    correct_opt = row.get("correct_option", opt_a).strip()

                    opts_list = [opt for opt in [opt_a, opt_b, opt_c, opt_d] if opt]
                    if len(opts_list) >= 2:
                        options_dict = {
                            "options": opts_list,
                            "correct_option": correct_opt,
                            "explanation": row.get("explanation", "").strip() or None
                        }

                req = QuestionCreate(
                    subject_id=subject_id,
                    question_text=q_text,
                    question_type=q_type,
                    marks=marks,
                    difficulty=diff,
                    bloom_level=bloom,
                    expected_answer=exp_ans,
                    options=options_dict,
                    source="CSV_IMPORT",
                    status=QuestionStatusEnum.ACTIVE
                )
                self.create_question(req, user)
                created_count += 1

            except Exception as ex:
                failed_count += 1
                errors.append(f"Row {row_idx}: {str(ex)}")

        return {
            "created_count": created_count,
            "failed_count": failed_count,
            "errors": errors
        }

    # --- QUESTION BANK MANAGEMENT ---
    def create_question_bank(self, req: QuestionBankCreate, user: User) -> QuestionBank:
        self.academic_service.verify_subject_access(user, req.subject_id, is_write_operation=True)
        bank = QuestionBank(
            subject_id=req.subject_id,
            name=req.name,
            description=req.description,
            created_by=user.id
        )
        created_bank = self.question_repo.create_bank(bank)
        self._log_audit(
            AuditActionEnum.QUESTION_BANK_CREATED,
            user_id=user.id,
            entity_id=created_bank.id,
            new_values={"name": created_bank.name}
        )
        return created_bank

    def get_question_bank(self, bank_id: str, user: User) -> QuestionBank:
        bank = self.question_repo.get_bank_by_id(bank_id)
        if not bank:
            raise HTTPException(status_code=404, detail="Question bank not found")
        self.academic_service.verify_subject_access(user, bank.subject_id, is_write_operation=False)
        return bank

    def list_question_banks(self, subject_id: str, user: User) -> List[QuestionBank]:
        self.academic_service.verify_subject_access(user, subject_id, is_write_operation=False)
        return self.question_repo.list_banks_by_subject(subject_id)

    def update_question_bank(self, bank_id: str, req: QuestionBankUpdate, user: User) -> QuestionBank:
        bank = self.get_question_bank(bank_id, user)
        self.academic_service.verify_subject_access(user, bank.subject_id, is_write_operation=True)
        
        if req.name is not None:
            bank.name = req.name
        if req.description is not None:
            bank.description = req.description

        updated_bank = self.question_repo.update_bank(bank)
        self._log_audit(
            AuditActionEnum.QUESTION_BANK_UPDATED,
            user_id=user.id,
            entity_id=updated_bank.id,
            new_values={"name": updated_bank.name}
        )
        return updated_bank

    def delete_question_bank(self, bank_id: str, user: User) -> None:
        bank = self.get_question_bank(bank_id, user)
        self.academic_service.verify_subject_access(user, bank.subject_id, is_write_operation=True)
        self.question_repo.delete_bank(bank)

    def add_questions_to_bank(self, bank_id: str, req: AddQuestionsToBankRequest, user: User) -> QuestionBank:
        bank = self.get_question_bank(bank_id, user)
        self.academic_service.verify_subject_access(user, bank.subject_id, is_write_operation=True)

        for q_id in req.question_ids:
            q = self.question_repo.get_by_id(q_id)
            if q and q.subject_id == bank.subject_id:
                self.question_repo.add_question_to_bank(bank.id, q.id, user.id)

        return self.get_question_bank(bank.id, user)

    def remove_question_from_bank(self, bank_id: str, question_id: str, user: User) -> QuestionBank:
        bank = self.get_question_bank(bank_id, user)
        self.academic_service.verify_subject_access(user, bank.subject_id, is_write_operation=True)
        self.question_repo.remove_question_from_bank(bank.id, question_id)
        return self.get_question_bank(bank.id, user)
