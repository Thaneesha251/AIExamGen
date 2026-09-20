from typing import Optional, List, Tuple, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc

try:
    from app.db.models import Question, QuestionVersion, QuestionBank, QuestionBankItem, QuestionGenerationRun
    from app.db.models.enums import QuestionStatusEnum, QuestionTypeEnum, DifficultyLevelEnum, BloomLevelEnum
except ImportError:
    from backend.app.db.models import Question, QuestionVersion, QuestionBank, QuestionBankItem, QuestionGenerationRun
    from backend.app.db.models.enums import QuestionStatusEnum, QuestionTypeEnum, DifficultyLevelEnum, BloomLevelEnum

class QuestionRepository:
    def __init__(self, db: Session):
        self.db = db

    # --- QUESTION CRUD ---
    def get_by_id(self, question_id: str) -> Optional[Question]:
        return self.db.query(Question).filter(Question.id == question_id).first()

    def create(self, question: Question) -> Question:
        self.db.add(question)
        self.db.commit()
        self.db.refresh(question)
        return question

    def update(self, question: Question) -> Question:
        self.db.commit()
        self.db.refresh(question)
        return question

    def create_version(self, version: QuestionVersion) -> QuestionVersion:
        self.db.add(version)
        self.db.commit()
        self.db.refresh(version)
        return version

    def search_questions(
        self,
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
        query = self.db.query(Question)

        if subject_id:
            query = query.filter(Question.subject_id == subject_id)
        if unit_id:
            query = query.filter(Question.unit_id == unit_id)
        if topic_id:
            query = query.filter(Question.topic_id == topic_id)
        if learning_outcome_id:
            query = query.filter(Question.learning_outcome_id == learning_outcome_id)
        if question_type:
            query = query.filter(Question.question_type == question_type)
        if difficulty:
            query = query.filter(Question.difficulty == difficulty)
        if bloom_level:
            query = query.filter(Question.bloom_level == bloom_level)
        if status:
            query = query.filter(Question.status == status)
        if source:
            query = query.filter(Question.source == source)
        if search_query:
            pattern = f"%{search_query}%"
            query = query.filter(
                or_(
                    Question.question_text.ilike(pattern),
                    Question.expected_answer.ilike(pattern)
                )
            )

        total = query.count()
        items = query.order_by(desc(Question.created_at)).offset(skip).limit(limit).all()
        return items, total

    def list_by_subject(self, subject_id: str, skip: int = 0, limit: int = 100) -> List[Question]:
        return self.db.query(Question).filter(Question.subject_id == subject_id).offset(skip).limit(limit).all()

    def list_by_unit(self, unit_id: str) -> List[Question]:
        return self.db.query(Question).filter(Question.unit_id == unit_id).all()

    # --- GENERATION RUNS ---
    def create_generation_run(self, run: QuestionGenerationRun) -> QuestionGenerationRun:
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return run

    def get_generation_run(self, run_id: str) -> Optional[QuestionGenerationRun]:
        return self.db.query(QuestionGenerationRun).filter(QuestionGenerationRun.id == run_id).first()

    def update_generation_run(self, run: QuestionGenerationRun) -> QuestionGenerationRun:
        self.db.commit()
        self.db.refresh(run)
        return run

    # --- QUESTION BANK ---
    def create_bank(self, bank: QuestionBank) -> QuestionBank:
        self.db.add(bank)
        self.db.commit()
        self.db.refresh(bank)
        return bank

    def get_bank_by_id(self, bank_id: str) -> Optional[QuestionBank]:
        return self.db.query(QuestionBank).filter(QuestionBank.id == bank_id).first()

    def list_banks_by_subject(self, subject_id: str) -> List[QuestionBank]:
        return self.db.query(QuestionBank).filter(QuestionBank.subject_id == subject_id).order_by(desc(QuestionBank.created_at)).all()

    def update_bank(self, bank: QuestionBank) -> QuestionBank:
        self.db.commit()
        self.db.refresh(bank)
        return bank

    def delete_bank(self, bank: QuestionBank) -> None:
        self.db.delete(bank)
        self.db.commit()

    def add_question_to_bank(self, bank_id: str, question_id: str, user_id: str) -> Optional[QuestionBankItem]:
        # Avoid duplicate addition
        existing = self.db.query(QuestionBankItem).filter(
            and_(QuestionBankItem.question_bank_id == bank_id, QuestionBankItem.question_id == question_id)
        ).first()
        if existing:
            return existing

        item = QuestionBankItem(
            question_bank_id=bank_id,
            question_id=question_id,
            added_by=user_id
        )
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def remove_question_from_bank(self, bank_id: str, question_id: str) -> bool:
        item = self.db.query(QuestionBankItem).filter(
            and_(QuestionBankItem.question_bank_id == bank_id, QuestionBankItem.question_id == question_id)
        ).first()
        if item:
            self.db.delete(item)
            self.db.commit()
            return True
        return False
