from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

class AnswerKeyItemBase(BaseModel):
    model_answer: str = Field(..., description="Complete model answer text")
    keywords: Optional[List[str]] = Field(default=None, description="Expected keywords")
    concepts: Optional[List[str]] = Field(default=None, description="Key academic concepts")
    acceptable_answers: Optional[List[str]] = Field(default=None, description="Alternative acceptable answers")
    marking_notes: Optional[str] = Field(default=None, description="Faculty guidance for evaluation")
    maximum_marks: float = Field(..., gt=0, description="Marks allocated for this item")
    rubric_id: Optional[str] = Field(default=None, description="Linked rubric ID if assigned")

class AnswerKeyItemCreate(AnswerKeyItemBase):
    question_paper_item_id: str

class AnswerKeyItemUpdate(BaseModel):
    model_answer: Optional[str] = None
    keywords: Optional[List[str]] = None
    concepts: Optional[List[str]] = None
    acceptable_answers: Optional[List[str]] = None
    marking_notes: Optional[str] = None
    maximum_marks: Optional[float] = None
    rubric_id: Optional[str] = None

class AnswerKeyItemResponse(AnswerKeyItemBase):
    id: str
    answer_key_id: str
    question_paper_item_id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class AnswerKeyCreate(BaseModel):
    question_paper_version_id: str
    items: Optional[List[AnswerKeyItemCreate]] = None

class AnswerKeyUpdate(BaseModel):
    status: Optional[str] = None
    items: Optional[List[AnswerKeyItemCreate]] = None

class AnswerKeyResponse(BaseModel):
    id: str
    question_paper_version_id: str
    version_number: int
    status: str
    generated_by: Optional[str] = None
    approved_by: Optional[str] = None
    items: List[AnswerKeyItemResponse] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class AnswerKeyValidationResult(BaseModel):
    is_valid: bool
    total_items: int
    total_marks: float
    target_paper_marks: float
    errors: List[str] = []
    warnings: List[str] = []
    item_summaries: List[Dict[str, Any]] = []

class AIDraftAnswerKeyRequest(BaseModel):
    overwrite_existing: bool = False
    custom_instructions: Optional[str] = None
