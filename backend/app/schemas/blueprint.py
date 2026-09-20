from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field
from backend.app.db.models.enums import BlueprintStatusEnum, QuestionTypeEnum, DifficultyLevelEnum, BloomLevelEnum

class BlueprintRuleBase(BaseModel):
    section: str = Field(..., min_length=1, max_length=50)
    question_count: int = Field(..., ge=1)
    marks_per_question: float = Field(..., gt=0)
    total_marks: float = Field(..., gt=0)
    unit_id: Optional[str] = None
    difficulty: Optional[DifficultyLevelEnum] = None
    bloom_level: Optional[BloomLevelEnum] = None
    question_type: Optional[QuestionTypeEnum] = None
    distribution_json: Optional[Dict[str, Any]] = None # Detailed per-unit, per-bloom, per-difficulty, per-type distributions
    minimum_count: Optional[int] = None
    maximum_count: Optional[int] = None
    order_index: int = Field(0, ge=0)

class BlueprintRuleCreate(BlueprintRuleBase):
    pass

class BlueprintRuleUpdate(BaseModel):
    section: Optional[str] = Field(None, min_length=1, max_length=50)
    question_count: Optional[int] = Field(None, ge=1)
    marks_per_question: Optional[float] = Field(None, gt=0)
    total_marks: Optional[float] = Field(None, gt=0)
    unit_id: Optional[str] = None
    difficulty: Optional[DifficultyLevelEnum] = None
    bloom_level: Optional[BloomLevelEnum] = None
    question_type: Optional[QuestionTypeEnum] = None
    distribution_json: Optional[Dict[str, Any]] = None
    minimum_count: Optional[int] = None
    maximum_count: Optional[int] = None
    order_index: Optional[int] = Field(None, ge=0)

class BlueprintRuleResponse(BlueprintRuleBase):
    id: str
    blueprint_id: str
    created_at: Any
    updated_at: Any

    model_config = ConfigDict(from_attributes=True)

class BlueprintBase(BaseModel):
    subject_id: str
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    total_marks: float = Field(100.0, gt=0)
    duration_minutes: int = Field(180, ge=15)
    status: BlueprintStatusEnum = BlueprintStatusEnum.DRAFT

class BlueprintCreate(BlueprintBase):
    rules: List[BlueprintRuleCreate] = []

class BlueprintUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    total_marks: Optional[float] = Field(None, gt=0)
    duration_minutes: Optional[int] = Field(None, ge=15)
    status: Optional[BlueprintStatusEnum] = None

class BlueprintResponse(BlueprintBase):
    id: str
    created_by: Optional[str] = None
    rules: List[BlueprintRuleResponse] = []
    created_at: Any
    updated_at: Any

    model_config = ConfigDict(from_attributes=True)

class BlueprintValidationResult(BaseModel):
    is_valid: bool = True
    total_marks: float = 0.0
    configured_total_marks: float = 0.0
    total_question_count: int = 0
    errors: List[str] = []
    warnings: List[str] = []
    section_summaries: List[Dict[str, Any]] = []
