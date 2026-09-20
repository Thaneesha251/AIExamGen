from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

try:
    from app.api.deps import get_db, get_current_user, require_admin_or_faculty
    from app.services.question_service import QuestionService
    from app.db.models import User
    from app.schemas.question_bank import (
        QuestionBankCreate,
        QuestionBankUpdate,
        QuestionBankResponse,
        AddQuestionsToBankRequest,
    )
except ImportError:
    from backend.app.api.deps import get_db, get_current_user, require_admin_or_faculty
    from backend.app.services.question_service import QuestionService
    from backend.app.db.models import User
    from backend.app.schemas.question_bank import (
        QuestionBankCreate,
        QuestionBankUpdate,
        QuestionBankResponse,
        AddQuestionsToBankRequest,
    )

router = APIRouter(tags=["Question Bank Management"])


@router.post("/question-banks", response_model=None)
def create_question_bank(
    req: QuestionBankCreate,
    user: User = Depends(require_admin_or_faculty),
    db: Session = Depends(get_db)
):
    service = QuestionService(db)
    bank = service.create_question_bank(req, user)
    return {"success": True, "data": QuestionBankResponse.model_validate(bank)}


@router.get("/question-banks/subject/{subject_id}", response_model=None)
def list_question_banks(
    subject_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = QuestionService(db)
    banks = service.list_question_banks(subject_id, user)
    return {"success": True, "data": [QuestionBankResponse.model_validate(b) for b in banks]}


@router.get("/question-banks/{bank_id}", response_model=None)
def get_question_bank(
    bank_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = QuestionService(db)
    bank = service.get_question_bank(bank_id, user)
    return {"success": True, "data": QuestionBankResponse.model_validate(bank)}


@router.put("/question-banks/{bank_id}", response_model=None)
def update_question_bank(
    bank_id: str,
    req: QuestionBankUpdate,
    user: User = Depends(require_admin_or_faculty),
    db: Session = Depends(get_db)
):
    service = QuestionService(db)
    bank = service.update_question_bank(bank_id, req, user)
    return {"success": True, "data": QuestionBankResponse.model_validate(bank)}


@router.delete("/question-banks/{bank_id}", response_model=None)
def delete_question_bank(
    bank_id: str,
    user: User = Depends(require_admin_or_faculty),
    db: Session = Depends(get_db)
):
    service = QuestionService(db)
    service.delete_question_bank(bank_id, user)
    return {"success": True, "message": "Question bank deleted successfully"}


@router.post("/question-banks/{bank_id}/questions", response_model=None)
def add_questions_to_bank(
    bank_id: str,
    req: AddQuestionsToBankRequest,
    user: User = Depends(require_admin_or_faculty),
    db: Session = Depends(get_db)
):
    service = QuestionService(db)
    bank = service.add_questions_to_bank(bank_id, req, user)
    return {"success": True, "data": QuestionBankResponse.model_validate(bank)}


@router.delete("/question-banks/{bank_id}/questions/{question_id}", response_model=None)
def remove_question_from_bank(
    bank_id: str,
    question_id: str,
    user: User = Depends(require_admin_or_faculty),
    db: Session = Depends(get_db)
):
    service = QuestionService(db)
    bank = service.remove_question_from_bank(bank_id, question_id, user)
    return {"success": True, "data": QuestionBankResponse.model_validate(bank)}
