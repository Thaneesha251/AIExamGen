from typing import Optional, List, Any
from pydantic import BaseModel, ConfigDict, Field
from backend.app.schemas.question import QuestionResponse

class QuestionBankBase(BaseModel):
    subject_id: str
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None

class QuestionBankCreate(QuestionBankBase):
    pass

class QuestionBankUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None

class QuestionBankItemResponse(BaseModel):
    id: str
    question_bank_id: str
    question_id: str
    added_by: Optional[str] = None
    question: Optional[QuestionResponse] = None
    created_at: Any

    model_config = ConfigDict(from_attributes=True)

class QuestionBankResponse(QuestionBankBase):
    id: str
    created_by: Optional[str] = None
    items: List[QuestionBankItemResponse] = []
    created_at: Any
    updated_at: Any

    model_config = ConfigDict(from_attributes=True)

class AddQuestionsToBankRequest(BaseModel):
    question_ids: List[str] = Field(..., min_length=1)
