from typing import Optional, List
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

try:
    from app.db.models import SyllabusDocument, FileAsset, SyllabusProcessingStatusEnum
except ImportError:
    from backend.app.db.models import SyllabusDocument, FileAsset, SyllabusProcessingStatusEnum


class SyllabusRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, doc_id: str) -> Optional[SyllabusDocument]:
        return (
            self.db.query(SyllabusDocument)
            .options(
                joinedload(SyllabusDocument.file_asset),
                joinedload(SyllabusDocument.uploader),
                joinedload(SyllabusDocument.subject)
            )
            .filter(SyllabusDocument.id == doc_id)
            .first()
        )

    def get_current_by_subject(self, subject_id: str) -> Optional[SyllabusDocument]:
        return (
            self.db.query(SyllabusDocument)
            .options(joinedload(SyllabusDocument.file_asset))
            .filter(SyllabusDocument.subject_id == subject_id, SyllabusDocument.is_current == True)
            .order_by(SyllabusDocument.version.desc())
            .first()
        )

    def list_by_subject(self, subject_id: str) -> List[SyllabusDocument]:
        return (
            self.db.query(SyllabusDocument)
            .options(joinedload(SyllabusDocument.file_asset))
            .filter(SyllabusDocument.subject_id == subject_id)
            .order_by(SyllabusDocument.version.desc())
            .all()
        )

    def get_next_version(self, subject_id: str) -> int:
        max_ver = (
            self.db.query(func.max(SyllabusDocument.version))
            .filter(SyllabusDocument.subject_id == subject_id)
            .scalar()
        )
        return (max_ver or 0) + 1

    def create(self, doc: SyllabusDocument) -> SyllabusDocument:
        self.db.add(doc)
        self.db.commit()
        self.db.refresh(doc)
        return self.get_by_id(doc.id) or doc

    def update(self, doc: SyllabusDocument) -> SyllabusDocument:
        self.db.commit()
        self.db.refresh(doc)
        return self.get_by_id(doc.id) or doc

    def set_current_version(self, doc_id: str, subject_id: str):
        # Reset all other documents for subject to is_current=False
        self.db.query(SyllabusDocument).filter(
            SyllabusDocument.subject_id == subject_id
        ).update({"is_current": False})

        # Set target document as is_current=True
        target = self.db.query(SyllabusDocument).filter(SyllabusDocument.id == doc_id).first()
        if target:
            target.is_current = True
            self.db.commit()
            self.db.refresh(target)
