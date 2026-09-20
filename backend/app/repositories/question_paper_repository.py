from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_, and_

try:
    from app.db.models import QuestionPaper, QuestionPaperVersion, QuestionPaperItem
    from app.db.models.enums import QuestionPaperStatusEnum
except ImportError:
    from backend.app.db.models import QuestionPaper, QuestionPaperVersion, QuestionPaperItem
    from backend.app.db.models.enums import QuestionPaperStatusEnum

class QuestionPaperRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, paper_id: str) -> Optional[QuestionPaper]:
        return self.db.query(QuestionPaper).filter(QuestionPaper.id == paper_id).first()

    def get_paper_by_id(self, paper_id: str) -> Optional[QuestionPaper]:
        return self.get_by_id(paper_id)

    def get_by_code(self, paper_code: str) -> Optional[QuestionPaper]:
        return self.db.query(QuestionPaper).filter(QuestionPaper.paper_code == paper_code).first()

    def get_paper_by_code(self, paper_code: str) -> Optional[QuestionPaper]:
        return self.get_by_code(paper_code)

    def list_papers(
        self,
        subject_id: Optional[str] = None,
        blueprint_id: Optional[str] = None,
        status: Optional[QuestionPaperStatusEnum] = None,
        created_by: Optional[str] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[QuestionPaper], int]:
        query = self.db.query(QuestionPaper)

        if subject_id:
            query = query.filter(QuestionPaper.subject_id == subject_id)
        if blueprint_id:
            query = query.filter(QuestionPaper.blueprint_id == blueprint_id)
        if status:
            query = query.filter(QuestionPaper.status == status)
        if created_by:
            query = query.filter(QuestionPaper.created_by == created_by)
        if search:
            pattern = f"%{search}%"
            query = query.filter(
                or_(
                    QuestionPaper.title.ilike(pattern),
                    QuestionPaper.paper_code.ilike(pattern)
                )
            )

        total = query.count()
        items = query.order_by(desc(QuestionPaper.created_at)).offset(skip).limit(limit).all()
        return items, total

    def create_paper(self, paper: QuestionPaper) -> QuestionPaper:
        self.db.add(paper)
        self.db.commit()
        self.db.refresh(paper)
        return paper

    def update_paper(self, paper: QuestionPaper) -> QuestionPaper:
        self.db.commit()
        self.db.refresh(paper)
        return paper

    def delete_paper(self, paper: QuestionPaper) -> None:
        self.db.delete(paper)
        self.db.commit()

    # --- VERSION & ITEM OPERATIONS ---
    def create_paper_version(
        self,
        question_paper_id: str,
        version_number: int,
        generation_method: PaperGenerationMethodEnum,
        generated_by: Optional[str],
        items_data: List[dict],
        generation_metadata: Optional[dict] = None
    ) -> QuestionPaperVersion:
        version = QuestionPaperVersion(
            question_paper_id=question_paper_id,
            version_number=version_number,
            generation_method=generation_method,
            generated_by=generated_by,
            generation_metadata=generation_metadata
        )
        self.db.add(version)
        self.db.flush()

        for idata in items_data:
            item = QuestionPaperItem(
                question_paper_version_id=version.id,
                **idata
            )
            self.db.add(item)
        self.db.commit()
        self.db.refresh(version)
        return version

    def create_version(self, version: QuestionPaperVersion) -> QuestionPaperVersion:
        self.db.add(version)
        self.db.commit()
        self.db.refresh(version)
        return version

    def get_version(self, version_id: str) -> Optional[QuestionPaperVersion]:
        return self.db.query(QuestionPaperVersion).filter(QuestionPaperVersion.id == version_id).first()

    def get_latest_version(self, paper_id: str) -> Optional[QuestionPaperVersion]:
        return self.db.query(QuestionPaperVersion).filter(
            QuestionPaperVersion.question_paper_id == paper_id
        ).order_by(desc(QuestionPaperVersion.version_number)).first()

    def get_next_version_number(self, question_paper_id: str) -> int:
        latest = self.db.query(QuestionPaperVersion).filter(
            QuestionPaperVersion.question_paper_id == question_paper_id
        ).order_by(desc(QuestionPaperVersion.version_number)).first()
        return (latest.version_number + 1) if latest else 1

    def create_item(self, item: QuestionPaperItem) -> QuestionPaperItem:
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def get_item_by_id(self, item_id: str) -> Optional[QuestionPaperItem]:
        return self.db.query(QuestionPaperItem).filter(QuestionPaperItem.id == item_id).first()
