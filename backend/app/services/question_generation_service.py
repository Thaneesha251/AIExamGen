from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException

try:
    from app.repositories.question_repository import QuestionRepository
    from app.repositories.academic_repository import AcademicRepository
    from app.services.academic_service import AcademicService
    from app.db.models import (
        User,
        Question,
        QuestionVersion,
        QuestionGenerationRun,
        AuditLog,
        AuditActionEnum,
        QuestionStatusEnum,
    )
    from app.schemas.question_generation import (
        QuestionGenerationRequest,
    )
    from ai.agents.question_generation_agent import QuestionGenerationAgent
    from ai.agents.question_validation_agent import QuestionValidationAgent
    from ai.services.llm_service import get_llm_provider
except ImportError:
    from backend.app.repositories.question_repository import QuestionRepository
    from backend.app.repositories.academic_repository import AcademicRepository
    from backend.app.services.academic_service import AcademicService
    from backend.app.db.models import (
        User,
        Question,
        QuestionVersion,
        QuestionGenerationRun,
        AuditLog,
        AuditActionEnum,
        QuestionStatusEnum,
    )
    from backend.app.schemas.question_generation import (
        QuestionGenerationRequest,
    )
    from ai.agents.question_generation_agent import QuestionGenerationAgent
    from ai.agents.question_validation_agent import QuestionValidationAgent
    from ai.services.llm_service import get_llm_provider


class QuestionGenerationService:
    def __init__(self, db: Session):
        self.db = db
        self.question_repo = QuestionRepository(db)
        self.academic_repo = AcademicRepository(db)
        self.academic_service = AcademicService(db)
        self.generation_agent = QuestionGenerationAgent(get_llm_provider("mock"))
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
                entity_type="QuestionGenerationRun",
                entity_id=entity_id,
                old_values=old_values,
                new_values=new_values,
            )
            self.db.add(audit)
            self.db.commit()
        except Exception:
            self.db.rollback()

    async def run_generation(self, req: QuestionGenerationRequest, user: User) -> QuestionGenerationRun:
        # 1. Authorize subject access
        self.academic_service.verify_subject_access(user, req.subject_id, is_write_operation=True)

        # 2. Resolve academic hierarchy names
        subject = self.academic_repo.get_subject_by_id(req.subject_id)
        if not subject:
            raise HTTPException(status_code=404, detail="Subject not found")

        unit_name = None
        if req.unit_id:
            unit = self.academic_repo.get_unit_by_id(req.unit_id)
            if unit:
                unit_name = f"Unit {unit.unit_number}: {unit.title}"

        topic_name = None
        if req.topic_id:
            topic = self.academic_repo.get_topic_by_id(req.topic_id)
            if topic:
                topic_name = topic.name

        lo_code = None
        lo_desc = None
        if req.learning_outcome_id:
            lo = self.academic_repo.get_learning_outcome_by_id(req.learning_outcome_id)
            if lo:
                lo_code = lo.code
                lo_desc = lo.description

        # 3. Create QuestionGenerationRun record
        run = QuestionGenerationRun(
            subject_id=req.subject_id,
            unit_id=req.unit_id,
            topic_id=req.topic_id,
            learning_outcome_id=req.learning_outcome_id,
            created_by=user.id,
            provider="mock",
            model="mock-llm-v1",
            prompt_version="question_gen_v1",
            status="RUNNING",
            requested_count=req.count,
            generated_count=0,
            accepted_count=0,
            rejected_count=0
        )
        created_run = self.question_repo.create_generation_run(run)

        try:
            # 4. Invoke QuestionGenerationAgent
            generated_schemas = await self.generation_agent.generate_questions(
                req=req,
                subject_name=subject.name,
                unit_name=unit_name,
                topic_name=topic_name,
                learning_outcome_code=lo_code,
                learning_outcome_desc=lo_desc
            )

            created_run.generated_count = len(generated_schemas)

            # 5. Fetch existing questions pool for duplicate detection
            existing_qs, _ = self.question_repo.search_questions(subject_id=req.subject_id, limit=500)
            existing_pool = [{"id": q.id, "question_text": q.question_text} for q in existing_qs]

            accepted = 0
            rejected = 0

            for gen_schema in generated_schemas:
                val_result = self.validation_agent.validate_question(gen_schema, existing_pool)

                if val_result.is_valid:
                    accepted += 1
                else:
                    rejected += 1

                # Persist generated question in database with UNDER_REVIEW status
                q_model = Question(
                    subject_id=req.subject_id,
                    unit_id=req.unit_id,
                    topic_id=req.topic_id,
                    learning_outcome_id=req.learning_outcome_id,
                    generation_run_id=created_run.id,
                    question_text=gen_schema.question_text,
                    question_type=gen_schema.question_type,
                    marks=gen_schema.marks,
                    difficulty=gen_schema.difficulty,
                    bloom_level=gen_schema.bloom_level,
                    expected_answer=gen_schema.expected_answer,
                    options=gen_schema.options,
                    keywords=gen_schema.keywords,
                    concepts=gen_schema.concepts,
                    source="AI_GENERATED",
                    status=QuestionStatusEnum.UNDER_REVIEW, # Always UNDER_REVIEW for AI generated questions
                    version=1,
                    validation_data=val_result.model_dump(),
                    created_by=user.id
                )
                saved_q = self.question_repo.create(q_model)

                # Add saved question text to pool for subsequent duplicate checks in this run
                existing_pool.append({"id": saved_q.id, "question_text": saved_q.question_text})

                # Create version v1
                v1 = QuestionVersion(
                    question_id=saved_q.id,
                    version_number=1,
                    question_text=saved_q.question_text,
                    marks=saved_q.marks,
                    difficulty=saved_q.difficulty,
                    bloom_level=saved_q.bloom_level,
                    expected_answer=saved_q.expected_answer,
                    options=saved_q.options,
                    keywords=saved_q.keywords,
                    concepts=saved_q.concepts,
                    changed_by=user.id,
                    change_reason="AI question generation run"
                )
                self.question_repo.create_version(v1)

            created_run.accepted_count = accepted
            created_run.rejected_count = rejected
            created_run.status = "COMPLETED"

        except Exception as e:
            created_run.status = "FAILED"
            created_run.error_message = str(e)

        updated_run = self.question_repo.update_generation_run(created_run)

        self._log_audit(
            AuditActionEnum.AI_GENERATION_COMPLETED,
            user_id=user.id,
            entity_id=updated_run.id,
            new_values={
                "status": updated_run.status,
                "generated_count": updated_run.generated_count,
                "accepted_count": updated_run.accepted_count
            }
        )

        return updated_run

    def get_generation_run(self, run_id: str, user: User) -> QuestionGenerationRun:
        run = self.question_repo.get_generation_run(run_id)
        if not run:
            raise HTTPException(status_code=404, detail="Question generation run not found")
        self.academic_service.verify_subject_access(user, run.subject_id, is_write_operation=False)
        return run
