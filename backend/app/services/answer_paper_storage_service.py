import os
import hashlib
import io
from typing import Tuple, List, Optional
from pathlib import Path
from sqlalchemy.orm import Session
from fastapi import UploadFile, HTTPException, status

try:
    from app.db.models import AnswerPaper, AnswerPage, FileAsset, Examination, ExaminationStudent, AnswerPaperStatusEnum, FileCategoryEnum
except ImportError:
    from backend.app.db.models import AnswerPaper, AnswerPage, FileAsset, Examination, ExaminationStudent, AnswerPaperStatusEnum, FileCategoryEnum

from backend.app.services.storage.local_storage import LocalStorageService

ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/x-png"
}

class AnswerPaperStorageService:
    """Service handling file upload validation, SHA-256 calculation, secure storage, and AnswerPaper/Page creation."""

    def __init__(self, db: Session, storage_service: Optional[LocalStorageService] = None):
        self.db = db
        self.storage_service = storage_service or LocalStorageService(base_dir="storage/uploads")

    def get_max_file_size_bytes(self) -> int:
        max_mb = int(os.getenv("MAX_ANSWER_PAPER_SIZE_MB", "25"))
        return max_mb * 1024 * 1024

    def validate_file(self, filename: str, content_type: str, file_bytes: bytes) -> str:
        """Validates extension, MIME type, file size, empty content, and basic corruption."""
        if not file_bytes or len(file_bytes) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty (0 bytes)."
            )

        max_bytes = self.get_max_file_size_bytes()
        if len(file_bytes) > max_bytes:
            max_mb = max_bytes // (1024 * 1024)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File size exceeds maximum allowed limit of {max_mb}MB."
            )

        ext = Path(filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file extension '{ext}'. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
            )

        # Content/MIME type check (basic header validation)
        if content_type.lower() not in ALLOWED_MIME_TYPES and not content_type.startswith("image/"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported MIME content type '{content_type}'."
            )

        # Simple file magic header check to detect corruption
        if ext == ".pdf" and not file_bytes.startswith(b"%PDF"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Corrupted or invalid PDF file header."
            )
        elif ext in [".jpg", ".jpeg"] and not (file_bytes.startswith(b"\xff\xd8") or b"JFIF" in file_bytes[:30] or b"Exif" in file_bytes[:30]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Corrupted or invalid JPEG image header."
            )
        elif ext == ".png" and not file_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Corrupted or invalid PNG image header."
            )

        return ext

    def compute_sha256(self, file_bytes: bytes) -> str:
        """Calculates SHA-256 hash of file content."""
        return hashlib.sha256(file_bytes).hexdigest()

    async def create_answer_paper_from_upload(
        self,
        examination_id: str,
        student_id: str,
        file: UploadFile,
        uploaded_by_user_id: str
    ) -> AnswerPaper:
        """Processes an uploaded file, creates FileAsset, AnswerPaper, and AnswerPages."""
        # 1. Check examination and student eligibility
        exam = self.db.query(Examination).filter(Examination.id == examination_id).first()
        if not exam:
            raise HTTPException(status_code=404, detail="Examination not found.")

        # Check if student is enrolled or present
        exam_student = self.db.query(ExaminationStudent).filter(
            ExaminationStudent.examination_id == examination_id,
            ExaminationStudent.student_id == student_id
        ).first()

        if not exam_student:
            # Auto-register student into examination if allowed or required
            exam_student = ExaminationStudent(
                examination_id=examination_id,
                student_id=student_id
            )
            self.db.add(exam_student)
            self.db.flush()

        # Read file bytes
        file_bytes = await file.read()
        ext = self.validate_file(file.filename or "paper.pdf", file.content_type or "application/pdf", file_bytes)
        checksum = self.compute_sha256(file_bytes)

        # Check existing submission count for student/exam
        existing_count = self.db.query(AnswerPaper).filter(
            AnswerPaper.examination_id == examination_id,
            AnswerPaper.student_id == student_id
        ).count()
        sub_number = existing_count + 1

        # Store file securely
        import uuid
        stored_filename = f"answer_paper_{examination_id[:8]}_{student_id[:8]}_sub{sub_number}_{uuid.uuid4().hex[:8]}{ext}"
        destination_path = f"answer-papers/{stored_filename}"

        stored_rel_path = await self.storage_service.save_file(
            file_data=io.BytesIO(file_bytes),
            destination_path=destination_path,
            content_type=file.content_type
        )

        # Create FileAsset
        file_asset = FileAsset(
            original_filename=file.filename or "answer_paper" + ext,
            stored_filename=stored_filename,
            storage_path=stored_rel_path,
            mime_type=file.content_type or "application/pdf",
            file_size=len(file_bytes),
            checksum=checksum,
            file_category=FileCategoryEnum.ANSWER_PAPER,
            uploaded_by=uploaded_by_user_id
        )
        self.db.add(file_asset)
        self.db.flush()

        # Create AnswerPaper record
        answer_paper = AnswerPaper(
            examination_id=examination_id,
            student_id=student_id,
            file_asset_id=file_asset.id,
            submission_number=sub_number,
            status=AnswerPaperStatusEnum.UPLOADED
        )
        self.db.add(answer_paper)
        self.db.flush()

        # Determine page count & create AnswerPages
        page_count = self._extract_pages_and_create_records(answer_paper, file_bytes, ext, uploaded_by_user_id)

        self.db.commit()
        self.db.refresh(answer_paper)
        return answer_paper

    def _extract_pages_and_create_records(self, answer_paper: AnswerPaper, file_bytes: bytes, ext: str, uploaded_by_user_id: str) -> int:
        """Extracts individual pages and creates AnswerPage records."""
        if ext == ".pdf":
            try:
                import pypdf
                pdf_reader = pypdf.PdfReader(io.BytesIO(file_bytes))
                num_pages = len(pdf_reader.pages)
            except Exception:
                try:
                    import PyPDF2
                    pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
                    num_pages = len(pdf_reader.pages)
                except Exception:
                    # Fallback page estimate if pdf parser fails
                    num_pages = 1
            num_pages = max(1, num_pages)
        else:
            num_pages = 1

        for p_num in range(1, num_pages + 1):
            page = AnswerPage(
                answer_paper_id=answer_paper.id,
                page_number=p_num,
                processing_status="PENDING"
            )
            self.db.add(page)

        self.db.flush()
        return num_pages
