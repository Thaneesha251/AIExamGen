from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field
from backend.app.db.models.enums import QuestionPaperStatusEnum, PaperGenerationMethodEnum
from backend.app.schemas.question import QuestionResponse

class QuestionPaperItemResponse(BaseModel):
    id: str
    question_paper_version_id: str
    question_id: Optional[str] = None
    section: str
    question_number: str
    marks: float
    question_text_snapshot: str
    options_snapshot: Optional[Dict[str, Any]] = None
    question_type_snapshot: Optional[str] = None
    difficulty_snapshot: Optional[str] = None
    bloom_snapshot: Optional[str] = None
    order_index: int
    question: Optional[QuestionResponse] = None
    created_at: Any
    updated_at: Any

    model_config = ConfigDict(from_attributes=True)

class QuestionPaperVersionResponse(BaseModel):
    id: str
    question_paper_id: str
    version_number: int
    generation_method: PaperGenerationMethodEnum
    generated_by: Optional[str] = None
    generation_metadata: Optional[Dict[str, Any]] = None
    items: List[QuestionPaperItemResponse] = []
    created_at: Any
    updated_at: Any

    model_config = ConfigDict(from_attributes=True)

class QuestionPaperResponse(BaseModel):
    id: str
    subject_id: str
    blueprint_id: Optional[str] = None
    title: str
    paper_code: str
    total_marks: float
    duration_minutes: int
    status: QuestionPaperStatusEnum
    created_by: Optional[str] = None
    versions: List[QuestionPaperVersionResponse] = []
    latest_version: Optional[QuestionPaperVersionResponse] = None
    created_at: Any
    updated_at: Any

    model_config = ConfigDict(from_attributes=True)

class QuestionPaperListResponse(BaseModel):
    total: int
    items: List[QuestionPaperResponse]
    page: int
    page_size: int

class PaperGenerationRequest(BaseModel):
    blueprint_id: str
    subject_id: Optional[str] = None
    title: str = Field(..., min_length=1, max_length=255)
    paper_code: Optional[str] = None
    version_label: Optional[str] = "Set A"
    generation_seed: Optional[int] = Field(None, description="Random seed for reproducible paper generation")
    exclude_recent_days: Optional[int] = Field(30, ge=0)

    model_config = ConfigDict(extra="ignore")

class PaperValidationResult(BaseModel):
    is_valid: bool = True
    total_marks: float = 0.0
    question_count: int = 0
    difficulty_distribution: Dict[str, int] = {}
    bloom_distribution: Dict[str, int] = {}
    unit_distribution: Dict[str, int] = {}
    question_type_distribution: Dict[str, int] = {}
    errors: List[str] = []
    warnings: List[str] = []

class QuestionReplacementRequest(BaseModel):
    target_item_id: Optional[str] = None
    new_question_id: Optional[str] = None
    change_reason: Optional[str] = "Faculty question replacement"
    reason: Optional[str] = None

class SectionRegenerateRequest(BaseModel):
    section_name: str
    change_reason: Optional[str] = "Faculty section regeneration"

class PaperRegenerateRequest(BaseModel):
    new_generation_seed: Optional[int] = None
    change_reason: Optional[str] = "Faculty full paper regeneration"

class PaperStatusUpdateRequest(BaseModel):
    status: QuestionPaperStatusEnum
    reason: Optional[str] = None
