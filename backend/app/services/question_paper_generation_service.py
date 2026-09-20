import uuid
import random
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

try:
    from app.repositories.question_paper_repository import QuestionPaperRepository
    from app.repositories.blueprint_repository import BlueprintRepository
    from app.services.blueprint_validation_service import BlueprintValidationService
    from app.services.question_selection_service import QuestionSelectionService
    from app.services.question_paper_validation_service import QuestionPaperValidationService
    from app.services.question_eligibility_service import QuestionEligibilityService
    from app.services.academic_service import AcademicService
    from app.db.models import (
        QuestionPaper,
        QuestionPaperVersion,
        QuestionPaperItem,
        Question,
        User,
        AuditLog
    )
    from app.db.models.enums import (
        AuditActionEnum,
        QuestionPaperStatusEnum,
        PaperGenerationMethodEnum,
        QuestionStatusEnum
    )
    from app.schemas.question_paper import (
        PaperGenerationRequest,
        QuestionReplacementRequest,
        SectionRegenerateRequest,
        PaperRegenerateRequest,
        PaperValidationResult
    )
except ImportError:
    from backend.app.repositories.question_paper_repository import QuestionPaperRepository
    from backend.app.repositories.blueprint_repository import BlueprintRepository
    from backend.app.services.blueprint_validation_service import BlueprintValidationService
    from backend.app.services.question_selection_service import QuestionSelectionService
    from backend.app.services.question_paper_validation_service import QuestionPaperValidationService
    from backend.app.services.question_eligibility_service import QuestionEligibilityService
    from backend.app.services.academic_service import AcademicService
    from backend.app.db.models import (
        QuestionPaper,
        QuestionPaperVersion,
        QuestionPaperItem,
        Question,
        User,
        AuditLog
    )
    from backend.app.db.models.enums import (
        AuditActionEnum,
        QuestionPaperStatusEnum,
        PaperGenerationMethodEnum,
        QuestionStatusEnum
    )
    from backend.app.schemas.question_paper import (
        PaperGenerationRequest,
        QuestionReplacementRequest,
        SectionRegenerateRequest,
        PaperRegenerateRequest,
        PaperValidationResult
    )

class QuestionPaperGenerationService:
    def __init__(self, db: Session):
        self.db = db
        self.paper_repo = QuestionPaperRepository(db)
        self.blueprint_repo = BlueprintRepository(db)
        self.blueprint_val_service = BlueprintValidationService(db)
        self.selection_service = QuestionSelectionService(db)
        self.paper_val_service = QuestionPaperValidationService(db)
        self.eligibility_service = QuestionEligibilityService(db)
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

    def generate_paper(self, request: PaperGenerationRequest, current_user: User) -> QuestionPaper:
        blueprint = self.blueprint_repo.get_blueprint_by_id(request.blueprint_id)
        if not blueprint:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Blueprint '{request.blueprint_id}' not found."
            )

        self.academic_service.verify_subject_access(current_user, blueprint.subject_id, is_write_operation=True)

        # 1. Validate Blueprint Pool Availability
        val_res = self.blueprint_val_service.validate_blueprint(blueprint)
        if not val_res.is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": "Blueprint validation failed due to structural issues or question bank pool shortages.",
                    "errors": val_res.errors,
                    "section_summaries": val_res.section_summaries
                }
            )

        # 2. Select Questions Deterministically
        try:
            selected_items = self.selection_service.select_questions_for_blueprint(
                blueprint=blueprint,
                seed=request.generation_seed
            )
        except ValueError as ve:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))

        # 3. Create QuestionPaper record
        paper_code = request.paper_code or f"QP-{uuid.uuid4().hex[:8].upper()}"
        existing_paper = self.paper_repo.get_paper_by_code(paper_code)
        if existing_paper:
            paper_code = f"QP-{uuid.uuid4().hex[:8].upper()}"

        paper_data = {
            "subject_id": blueprint.subject_id,
            "blueprint_id": request.blueprint_id,
            "title": request.title,
            "paper_code": paper_code,
            "total_marks": blueprint.total_marks,
            "duration_minutes": getattr(request, "duration_minutes", None) or getattr(blueprint, "duration_minutes", 180),
            "status": QuestionPaperStatusEnum.GENERATED,
            "created_by": current_user.id
        }
        paper_obj = QuestionPaper(**paper_data)
        paper = self.paper_repo.create_paper(paper_obj)

        # 4. Create Version 1 with items snapshots
        items_data = []
        for item in selected_items:
            q: Question = item["question"]
            items_data.append({
                "question_id": q.id,
                "section": item["section"],
                "question_number": item["question_number"],
                "marks": item["marks"],
                "question_text_snapshot": q.question_text,
                "options_snapshot": q.options,
                "question_type_snapshot": q.question_type.value if hasattr(q.question_type, 'value') else str(q.question_type),
                "difficulty_snapshot": q.difficulty.value if hasattr(q.difficulty, 'value') else str(q.difficulty),
                "bloom_snapshot": q.bloom_level.value if hasattr(q.bloom_level, 'value') else str(q.bloom_level),
                "order_index": item["order_index"]
            })

        version_metadata = {
            "generation_seed": request.generation_seed,
            "blueprint_id": request.blueprint_id,
            "initial_generation": True
        }

        self.paper_repo.create_paper_version(
            question_paper_id=paper.id,
            version_number=1,
            generation_method=PaperGenerationMethodEnum.AI_GENERATED,
            generated_by=current_user.id,
            items_data=items_data,
            generation_metadata=version_metadata
        )

        self.db.refresh(paper)

        self._log_audit(
            action=AuditActionEnum.PAPER_GENERATION_COMPLETED,
            user_id=current_user.id,
            entity_id=paper.id,
            new_values={"paper_code": paper.paper_code, "total_marks": paper.total_marks, "seed": request.generation_seed}
        )

        return paper

    def get_paper(self, paper_id: str) -> QuestionPaper:
        paper = self.paper_repo.get_paper_by_id(paper_id)
        if not paper:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Question Paper '{paper_id}' not found.")
        return paper

    def list_papers(self, subject_id: Optional[str] = None, current_user: Optional[User] = None) -> List[QuestionPaper]:
        if subject_id and current_user:
            self.academic_service.verify_subject_access(current_user, subject_id, is_write_operation=False)
        return self.paper_repo.list_papers(subject_id=subject_id)

    def replace_question_in_paper(
        self,
        paper_id: str,
        request: QuestionReplacementRequest,
        current_user: User
    ) -> QuestionPaper:
        paper = self.get_paper(paper_id)
        self.academic_service.verify_subject_access(current_user, paper.subject_id, is_write_operation=True)

        latest_ver = self.paper_repo.get_latest_version(paper_id)
        if not latest_ver:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No active version found for question paper.")

        # Find target item
        target_item: Optional[QuestionPaperItem] = None
        target_q_num = getattr(request, "target_question_number", None)
        for item in latest_ver.items:
            if request.target_item_id and item.id == request.target_item_id:
                target_item = item
                break
            if target_q_num and item.question_number == target_q_num:
                target_item = item
                break

        if not target_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target question item to replace was not found in active paper version."
            )

        # Get current question IDs in paper to avoid duplicates
        existing_qids = [i.question_id for i in latest_ver.items if i.question_id]

        replacement_q: Optional[Question] = None
        replacement_id = getattr(request, "new_question_id", None) or getattr(request, "replacement_question_id", None)
        if replacement_id:
            candidate = self.db.query(Question).filter(Question.id == replacement_id).first()
            if not candidate or candidate.status not in [QuestionStatusEnum.APPROVED, QuestionStatusEnum.ACTIVE]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Requested replacement question is not approved or does not exist."
                )
            if candidate.marks != target_item.marks:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Replacement question marks ({candidate.marks}) do not match target item marks ({target_item.marks})."
                )
            replacement_q = candidate
        else:
            # Auto-find candidate matching section rule or target item properties
            candidates = self.eligibility_service.get_base_eligible_query(paper.subject_id).filter(
                Question.marks == target_item.marks,
                ~Question.id.in_(existing_qids)
            ).all()

            if not candidates:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No eligible replacement questions available in Question Bank with matching marks."
                )

            # Pick least exposed candidate
            rng = random.Random()
            replacement_q = rng.choice(candidates)

        # Build items for new version (vN+1)
        new_version_number = latest_ver.version_number + 1
        new_items_data = []

        for item in latest_ver.items:
            if item.id == target_item.id:
                # Replace with replacement_q
                q = replacement_q
                new_items_data.append({
                    "question_id": q.id,
                    "section": item.section,
                    "question_number": item.question_number,
                    "marks": item.marks,
                    "question_text_snapshot": q.question_text,
                    "options_snapshot": q.options,
                    "question_type_snapshot": q.question_type.value if hasattr(q.question_type, 'value') else str(q.question_type),
                    "difficulty_snapshot": q.difficulty.value if hasattr(q.difficulty, 'value') else str(q.difficulty),
                    "bloom_snapshot": q.bloom_level.value if hasattr(q.bloom_level, 'value') else str(q.bloom_level),
                    "order_index": item.order_index
                })
            else:
                # Copy existing item snapshot
                new_items_data.append({
                    "question_id": item.question_id,
                    "section": item.section,
                    "question_number": item.question_number,
                    "marks": item.marks,
                    "question_text_snapshot": item.question_text_snapshot,
                    "options_snapshot": item.options_snapshot,
                    "question_type_snapshot": item.question_type_snapshot,
                    "difficulty_snapshot": item.difficulty_snapshot,
                    "bloom_snapshot": item.bloom_snapshot,
                    "order_index": item.order_index
                })

        new_ver_metadata = {
            "replaced_item_id": target_item.id,
            "old_question_id": target_item.question_id,
            "new_question_id": replacement_q.id,
            "reason": request.reason or "Faculty single question replacement"
        }

        self.paper_repo.create_paper_version(
            question_paper_id=paper.id,
            version_number=new_version_number,
            generation_method=PaperGenerationMethodEnum.HYBRID,
            generated_by=current_user.id,
            items_data=new_items_data,
            generation_metadata=new_ver_metadata
        )

        self._log_audit(
            action=AuditActionEnum.PAPER_QUESTION_REPLACED,
            user_id=current_user.id,
            entity_id=paper.id,
            new_values={"version_number": new_version_number, "replaced_q": replacement_q.id}
        )

        self.db.refresh(paper)
        return paper

    def regenerate_section(
        self,
        paper_id: str,
        request: SectionRegenerateRequest,
        current_user: User
    ) -> QuestionPaper:
        paper = self.get_paper(paper_id)
        self.academic_service.verify_subject_access(current_user, paper.subject_id, is_write_operation=True)

        if not paper.blueprint:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Paper has no blueprint linked for section regeneration.")

        latest_ver = self.paper_repo.get_latest_version(paper_id)
        if not latest_ver:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No active version found.")

        # Find blueprint rule for section
        target_rule = None
        for rule in paper.blueprint.rules:
            if rule.section == request.section_name:
                target_rule = rule
                break

        if not target_rule:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Section '{request.section_name}' not found in blueprint rules.")

        # Exclude questions used in other sections of the paper
        other_section_qids = [
            i.question_id for i in latest_ver.items
            if i.section != request.section_name and i.question_id
        ]

        seed = request.generation_seed or random.randint(1000, 99999)
        rng = random.Random(seed)

        # Select new questions for this rule
        selected_for_rule = self.selection_service._select_generic_for_rule(
            subject_id=paper.subject_id,
            rule=target_rule,
            count=target_rule.question_count,
            exclude_ids=other_section_qids,
            rng=rng
        )

        if len(selected_for_rule) < target_rule.question_count:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient questions to regenerate section '{request.section_name}'."
            )

        new_version_number = latest_ver.version_number + 1
        new_items_data = []
        sec_q_idx = 0

        for item in latest_ver.items:
            if item.section == request.section_name:
                q = selected_for_rule[sec_q_idx]
                sec_q_idx += 1
                new_items_data.append({
                    "question_id": q.id,
                    "section": item.section,
                    "question_number": item.question_number,
                    "marks": item.marks,
                    "question_text_snapshot": q.question_text,
                    "options_snapshot": q.options,
                    "question_type_snapshot": q.question_type.value if hasattr(q.question_type, 'value') else str(q.question_type),
                    "difficulty_snapshot": q.difficulty.value if hasattr(q.difficulty, 'value') else str(q.difficulty),
                    "bloom_snapshot": q.bloom_level.value if hasattr(q.bloom_level, 'value') else str(q.bloom_level),
                    "order_index": item.order_index
                })
            else:
                new_items_data.append({
                    "question_id": item.question_id,
                    "section": item.section,
                    "question_number": item.question_number,
                    "marks": item.marks,
                    "question_text_snapshot": item.question_text_snapshot,
                    "options_snapshot": item.options_snapshot,
                    "question_type_snapshot": item.question_type_snapshot,
                    "difficulty_snapshot": item.difficulty_snapshot,
                    "bloom_snapshot": item.bloom_snapshot,
                    "order_index": item.order_index
                })

        new_ver_metadata = {
            "regenerated_section": request.section_name,
            "seed": seed
        }

        self.paper_repo.create_paper_version(
            question_paper_id=paper.id,
            version_number=new_version_number,
            generation_method=PaperGenerationMethodEnum.HYBRID,
            generated_by=current_user.id,
            items_data=new_items_data,
            generation_metadata=new_ver_metadata
        )

        self._log_audit(
            action=AuditActionEnum.PAPER_SECTION_REGENERATED,
            user_id=current_user.id,
            entity_id=paper.id,
            new_values={"section": request.section_name, "version_number": new_version_number}
        )

        self.db.refresh(paper)
        return paper

    def regenerate_full_paper(
        self,
        paper_id: str,
        request: PaperRegenerateRequest,
        current_user: User
    ) -> QuestionPaper:
        paper = self.get_paper(paper_id)
        self.academic_service.verify_subject_access(current_user, paper.subject_id, is_write_operation=True)

        if not paper.blueprint:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Paper has no blueprint linked for full regeneration.")

        latest_ver = self.paper_repo.get_latest_version(paper_id)
        current_ver_num = latest_ver.version_number if latest_ver else 0

        seed = request.generation_seed or random.randint(1000, 99999)
        selected_items = self.selection_service.select_questions_for_blueprint(
            blueprint=paper.blueprint,
            seed=seed
        )

        new_items_data = []
        for item in selected_items:
            q: Question = item["question"]
            new_items_data.append({
                "question_id": q.id,
                "section": item["section"],
                "question_number": item["question_number"],
                "marks": item["marks"],
                "question_text_snapshot": q.question_text,
                "options_snapshot": q.options,
                "question_type_snapshot": q.question_type.value if hasattr(q.question_type, 'value') else str(q.question_type),
                "difficulty_snapshot": q.difficulty.value if hasattr(q.difficulty, 'value') else str(q.difficulty),
                "bloom_snapshot": q.bloom_level.value if hasattr(q.bloom_level, 'value') else str(q.bloom_level),
                "order_index": item["order_index"]
            })

        new_version_number = current_ver_num + 1
        new_ver_metadata = {
            "full_regeneration": True,
            "seed": seed
        }

        self.paper_repo.create_paper_version(
            question_paper_id=paper.id,
            version_number=new_version_number,
            generation_method=PaperGenerationMethodEnum.AI_GENERATED,
            generated_by=current_user.id,
            items_data=new_items_data,
            generation_metadata=new_ver_metadata
        )

        self._log_audit(
            action=AuditActionEnum.PAPER_REGENERATED,
            user_id=current_user.id,
            entity_id=paper.id,
            new_values={"version_number": new_version_number, "seed": seed}
        )

        self.db.refresh(paper)
        return paper

    def validate_paper_by_id(
        self,
        paper_id: str,
        version_number: Optional[int] = None
    ) -> PaperValidationResult:
        paper = self.get_paper(paper_id)
        if version_number:
            ver = self.paper_repo.get_version_by_number(paper_id, version_number)
        else:
            ver = self.paper_repo.get_latest_version(paper_id)

        if not ver:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question Paper Version not found.")

        return self.paper_val_service.validate_paper_version(paper, ver)
