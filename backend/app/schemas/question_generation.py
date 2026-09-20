from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field
from backend.app.db.models.enums import QuestionTypeEnum, DifficultyLevelEnum, BloomLevelEnum
from backend.app.schemas.question import QuestionResponse

class QuestionGenerationRequest(BaseModel):
    subject_id: str
    unit_id: Optional[str] = None
    topic_id: Optional[str] = None
    learning_outcome_id: Optional[str] = None
    question_type: QuestionTypeEnum = QuestionTypeEnum.SHORT_ANSWER
    difficulty: DifficultyLevelEnum = DifficultyLevelEnum.MEDIUM
    bloom_level: BloomLevelEnum = BloomLevelEnum.UNDERSTAND
    marks: float = Field(5.0, gt=0)
    count: int = Field(3, ge=1, le=20)
    language: str = "English"

class GeneratedQuestionSchema(BaseModel):
    question_text: str
    question_type: QuestionTypeEnum
    marks: float
    difficulty: DifficultyLevelEnum
    bloom_level: BloomLevelEnum
    expected_answer: Optional[str] = None
    options: Optional[Dict[str, Any]] = None # Options for MCQ
    keywords: List[str] = []
    concepts: List[str] = []

class QuestionValidationResult(BaseModel):
    is_valid: bool = True
    alignment_score: float = 1.0
    difficulty_score: float = 1.0
    bloom_alignment_score: float = 1.0
    duplicate_score: float = 0.0
    completeness_score: float = 1.0
    warnings: List[str] = []
    similar_question_id: Optional[str] = None

class QuestionGenerationRunResponse(BaseModel):
    id: str
    subject_id: str
    unit_id: Optional[str] = None
    topic_id: Optional[str] = None
    learning_outcome_id: Optional[str] = None
    created_by: str
    provider: str
    model: str
    prompt_version: str
    status: str
    requested_count: int
    generated_count: int
    accepted_count: int
    rejected_count: int
    error_message: Optional[str] = None
    questions: List[QuestionResponse] = []
    created_at: Any
    updated_at: Any

    model_config = ConfigDict(from_attributes=True)
