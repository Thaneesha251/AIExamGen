import os
import uuid
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, UploadFile, status

try:
    from app.repositories.syllabus_repository import SyllabusRepository
    from app.repositories.academic_repository import AcademicRepository
    from app.services.academic_service import AcademicService
    from app.services.storage.local_storage import LocalStorageService
    from app.db.models import (
        User,
        SyllabusDocument,
        FileAsset,
        FileCategoryEnum,
        SyllabusProcessingStatusEnum,
        Unit,
        Topic,
        LearningOutcome,
        BloomLevelEnum,
        AuditLog,
        AuditActionEnum,
    )
    from app.schemas.syllabus import (
        SyllabusDocumentResponse,
        SyllabusStructure,
        SyllabusReviewUpdate
    )
    from ai.services.document_processing.extractor import DocumentProcessor
    from ai.agents.syllabus_analysis_agent import SyllabusAnalysisAgent
except ImportError:
    from backend.app.repositories.syllabus_repository import SyllabusRepository
    from backend.app.repositories.academic_repository import AcademicRepository
    from backend.app.services.academic_service import AcademicService
    from backend.app.services.storage.local_storage import LocalStorageService
    from backend.app.db.models import (
        User,
        SyllabusDocument,
        FileAsset,
        FileCategoryEnum,
        SyllabusProcessingStatusEnum,
        Unit,
        Topic,
        LearningOutcome,
        BloomLevelEnum,
        AuditLog,
        AuditActionEnum,
    )
    from backend.app.schemas.syllabus import (
        SyllabusDocumentResponse,
        SyllabusStructure,
        SyllabusReviewUpdate
    )
    from ai.services.document_processing.extractor import DocumentProcessor
    from ai.agents.syllabus_analysis_agent import SyllabusAnalysisAgent


class SyllabusService:
    def __init__(self, db: Session):
        self.db = db
        self.syllabus_repo = SyllabusRepository(db)
        self.academic_repo = AcademicRepository(db)
        self.academic_service = AcademicService(db)
        self.storage_service = LocalStorageService(base_dir="storage/uploads")
        self.document_processor = DocumentProcessor()
        self.analysis_agent = SyllabusAnalysisAgent()

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
                entity_type="SyllabusDocument",
                entity_id=entity_id,
                old_values=old_values,
                new_values=new_values,
            )
            self.db.add(audit)
            self.db.commit()
        except Exception:
            self.db.rollback()

    async def upload_syllabus(self, subject_id: str, file: UploadFile, user: User) -> SyllabusDocument:
        # 1. Authorize faculty subject access
        self.academic_service.verify_subject_access(user, subject_id, is_write_operation=True)

        original_filename = file.filename or "syllabus.pdf"
        ext = os.path.splitext(original_filename)[1].lower()
        if ext not in {".pdf", ".docx", ".txt"}:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file format '{ext}'. Allowed formats: .pdf, .docx, .txt"
            )

        file_bytes = await file.read()
        if len(file_bytes) == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")

        checksum = DocumentProcessor.calculate_checksum(file_bytes)

        # 2. Store file via storage service
        next_version = self.syllabus_repo.get_next_version(subject_id)
        stored_filename = f"subj_{subject_id}_v{next_version}_{uuid.uuid4().hex[:8]}{ext}"
        destination_path = f"syllabi/{subject_id}/{stored_filename}"

        # Write bytes using LocalStorageService
        import io
        saved_rel_path = await self.storage_service.save_file(
            io.BytesIO(file_bytes),
            destination_path,
            content_type=file.content_type
        )

        # 3. Create FileAsset record
        file_asset = FileAsset(
            original_filename=original_filename,
            stored_filename=stored_filename,
            storage_path=saved_rel_path,
            mime_type=file.content_type or "application/octet-stream",
            file_size=len(file_bytes),
            checksum=checksum,
            file_category=FileCategoryEnum.SYLLABUS,
            uploaded_by=user.id
        )
        self.db.add(file_asset)
        self.db.commit()
        self.db.refresh(file_asset)

        # 4. Create SyllabusDocument record
        syllabus_doc = SyllabusDocument(
            subject_id=subject_id,
            uploaded_by=user.id,
            file_asset_id=file_asset.id,
            version=next_version,
            is_current=True,
            status=SyllabusProcessingStatusEnum.UPLOADED
        )
        created_doc = self.syllabus_repo.create(syllabus_doc)
        self.syllabus_repo.set_current_version(created_doc.id, subject_id)

        self._log_audit(
            AuditActionEnum.SYLLABUS_UPLOADED,
            user_id=user.id,
            entity_id=created_doc.id,
            new_values={"filename": original_filename, "version": next_version}
        )

        # Automatically process document upon upload
        return await self.process_syllabus(created_doc.id, user)

    async def process_syllabus(self, doc_id: str, user: User) -> SyllabusDocument:
        doc = self.syllabus_repo.get_by_id(doc_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Syllabus document not found")

        self.academic_service.verify_subject_access(user, doc.subject_id, is_write_operation=True)

        doc.status = SyllabusProcessingStatusEnum.PROCESSING
        self.syllabus_repo.update(doc)

        try:
            # Full absolute disk path
            abs_file_path = os.path.join(self.storage_service.base_dir, doc.file_asset.storage_path)

            # Extract text
            extraction_res = self.document_processor.extract_text(abs_file_path, doc.file_asset.original_filename)
            doc.extracted_text = extraction_res.text

            # Parse structure using AI agent
            structure = self.analysis_agent.analyze_syllabus(
                extraction_res.text,
                document_name=doc.file_asset.original_filename
            )

            # Combine extractor warnings with parser warnings
            all_warnings = list(set(extraction_res.warnings + structure.warnings))
            structure.warnings = all_warnings

            doc.structured_data = structure.model_dump()
            doc.status = SyllabusProcessingStatusEnum.REVIEW_REQUIRED
            doc.processing_error = None

        except Exception as e:
            doc.status = SyllabusProcessingStatusEnum.FAILED
            doc.processing_error = str(e)

        updated_doc = self.syllabus_repo.update(doc)
        self._log_audit(
            AuditActionEnum.SYLLABUS_PROCESSED,
            user_id=user.id,
            entity_id=updated_doc.id,
            new_values={"status": updated_doc.status.value}
        )
        return updated_doc

    def update_syllabus_review(self, doc_id: str, review_data: SyllabusReviewUpdate, user: User) -> SyllabusDocument:
        doc = self.syllabus_repo.get_by_id(doc_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Syllabus document not found")

        self.academic_service.verify_subject_access(user, doc.subject_id, is_write_operation=True)

        doc.structured_data = review_data.structured_data.model_dump()
        doc.status = SyllabusProcessingStatusEnum.REVIEW_REQUIRED
        updated_doc = self.syllabus_repo.update(doc)

        self._log_audit(
            AuditActionEnum.SYLLABUS_UPDATED,
            user_id=user.id,
            entity_id=updated_doc.id,
            new_values={"action": "review_edited"}
        )
        return updated_doc

    def approve_syllabus(self, doc_id: str, user: User) -> SyllabusDocument:
        doc = self.syllabus_repo.get_by_id(doc_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Syllabus document not found")

        self.academic_service.verify_subject_access(user, doc.subject_id, is_write_operation=True)

        if not doc.structured_data:
            raise HTTPException(status_code=400, detail="Cannot approve document without structured syllabus data.")

        # Persist Units, Topics, and Learning Outcomes into Academic DB Tables
        structured = SyllabusStructure.model_validate(doc.structured_data)

        # 1. Synchronize Units & Topics
        for u_item in structured.units:
            # Check existing unit
            existing_units = self.academic_repo.list_units_by_subject(doc.subject_id)
            target_unit = next((u for u in existing_units if u.unit_number == u_item.unit_number), None)

            if not target_unit:
                target_unit = Unit(
                    subject_id=doc.subject_id,
                    unit_number=u_item.unit_number,
                    title=u_item.title,
                    description=u_item.description,
                    weightage=u_item.weightage or 20.0
                )
                target_unit = self.academic_repo.create_unit(target_unit)
            else:
                target_unit.title = u_item.title
                if u_item.description:
                    target_unit.description = u_item.description
                target_unit = self.academic_repo.update_unit(target_unit)

            # Topics
            existing_topics = self.academic_repo.list_topics_by_unit(target_unit.id)
            for t_item in u_item.topics:
                target_topic = next((t for t in existing_topics if t.name.lower() == t_item.title.lower()), None)
                if not target_topic:
                    target_topic = Topic(
                        unit_id=target_unit.id,
                        name=t_item.title,
                        keywords=t_item.keywords,
                        description=f"Extracted topic from Unit {u_item.unit_number}"
                    )
                    self.academic_repo.create_topic(target_topic)

        # 2. Synchronize Learning Outcomes
        existing_cos = self.academic_repo.list_learning_outcomes(doc.subject_id)
        for lo_item in structured.learning_outcomes:
            target_co = next((co for co in existing_cos if co.code.upper() == lo_item.code.upper()), None)
            bloom_val = lo_item.bloom_level or BloomLevelEnum.UNDERSTAND
            if not target_co:
                target_co = LearningOutcome(
                    subject_id=doc.subject_id,
                    code=lo_item.code.upper(),
                    description=lo_item.description,
                    bloom_level=bloom_val
                )
                self.academic_repo.create_learning_outcome(target_co)
            else:
                target_co.description = lo_item.description
                target_co.bloom_level = bloom_val
                self.academic_repo.update_learning_outcome(target_co)

        doc.status = SyllabusProcessingStatusEnum.APPROVED
        updated_doc = self.syllabus_repo.update(doc)

        self._log_audit(
            AuditActionEnum.SYLLABUS_APPROVED,
            user_id=user.id,
            entity_id=updated_doc.id,
            new_values={"status": "APPROVED", "persisted_units": len(structured.units)}
        )
        return updated_doc

    def get_current_syllabus(self, subject_id: str, user: User) -> Optional[SyllabusDocument]:
        self.academic_service.verify_subject_access(user, subject_id, is_write_operation=False)
        return self.syllabus_repo.get_current_by_subject(subject_id)

    def list_syllabus_history(self, subject_id: str, user: User) -> List[SyllabusDocument]:
        self.academic_service.verify_subject_access(user, subject_id, is_write_operation=False)
        return self.syllabus_repo.list_by_subject(subject_id)

    def get_syllabus_by_id(self, doc_id: str, user: User) -> SyllabusDocument:
        doc = self.syllabus_repo.get_by_id(doc_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Syllabus document not found")
        self.academic_service.verify_subject_access(user, doc.subject_id, is_write_operation=False)
        return doc
