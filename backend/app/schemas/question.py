from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field
from backend.app.db.models.enums import QuestionTypeEnum, DifficultyLevelEnum, BloomLevelEnum, QuestionStatusEnum

class MCQOptionsSchema(BaseModel):
    options: List[str] = Field(..., min_length=2)
    correct_option: str
    explanation: Optional[str] = None

class ValidationDataSchema(BaseModel):
    is_valid: bool = True
    alignment_score: float = 1.0
    difficulty_score: float = 1.0
    bloom_alignment_score: float = 1.0
    duplicate_score: float = 0.0
    completeness_score: float = 1.0
    warnings: List[str] = []
    similar_question_id: Optional[str] = None

class QuestionBase(BaseModel):
    subject_id: str
    unit_id: Optional[str] = None
    topic_id: Optional[str] = None
    learning_outcome_id: Optional[str] = None
    question_text: str = Field(..., min_length=1)
    question_type: QuestionTypeEnum
    marks: float = Field(2.0, gt=0)
    difficulty: DifficultyLevelEnum = DifficultyLevelEnum.MEDIUM
    bloom_level: BloomLevelEnum = BloomLevelEnum.UNDERSTAND
    expected_answer: Optional[str] = None
    options: Optional[Dict[str, Any]] = None
    keywords: Optional[List[str]] = None
    concepts: Optional[List[str]] = None
    source: Optional[str] = "MANUAL"
    status: QuestionStatusEnum = QuestionStatusEnum.ACTIVE

class QuestionCreate(QuestionBase):
    pass

class QuestionUpdate(BaseModel):
    subject_id: Optional[str] = None
    unit_id: Optional[str] = None
    topic_id: Optional[str] = None
    learning_outcome_id: Optional[str] = None
    question_text: Optional[str] = Field(None, min_length=1)
    question_type: Optional[QuestionTypeEnum] = None
    marks: Optional[float] = Field(None, gt=0)
    difficulty: Optional[DifficultyLevelEnum] = None
    bloom_level: Optional[BloomLevelEnum] = None
    expected_answer: Optional[str] = None
    options: Optional[Dict[str, Any]] = None
    keywords: Optional[List[str]] = None
    concepts: Optional[List[str]] = None
    status: Optional[QuestionStatusEnum] = None
    change_reason: Optional[str] = "Faculty edit"

class QuestionStatusUpdate(BaseModel):
    status: QuestionStatusEnum
    reason: Optional[str] = None

class QuestionVersionResponse(BaseModel):
    id: str
    question_id: str
    version_number: int
    question_text: str
    marks: float
    difficulty: DifficultyLevelEnum
    bloom_level: BloomLevelEnum
    expected_answer: Optional[str] = None
    keywords: Optional[Any] = None
    concepts: Optional[Any] = None
    changed_by: Optional[str] = None
    change_reason: Optional[str] = None
    created_at: Any

    model_config = ConfigDict(from_attributes=True)

class QuestionResponse(QuestionBase):
    id: str
    generation_run_id: Optional[str] = None
    version: int = 1
    validation_data: Optional[Dict[str, Any]] = None
    created_by: Optional[str] = None
    versions: List[QuestionVersionResponse] = []
    created_at: Any
    updated_at: Any

    model_config = ConfigDict(from_attributes=True)

class QuestionListResponse(BaseModel):
    total: int
    items: List[QuestionResponse]
    page: int
    page_size: int
