from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

class RubricCriterionBase(BaseModel):
    criterion: str = Field(..., description="Criterion name, e.g. Concept Understanding")
    description: Optional[str] = Field(default=None, description="Detailed marking criteria description")
    marks: float = Field(..., ge=0, description="Maximum marks for this criterion")
    min_marks: float = Field(default=0.0, ge=0, description="Minimum marks for this criterion")
    weight: float = Field(default=1.0, gt=0, description="Criterion weighting factor")
    partial_credit_rules: Optional[Dict[str, Any]] = Field(default=None, description="Partial credit breakdown rules")
    required: bool = Field(default=True, description="Whether this criterion is mandatory")
    order_index: int = Field(default=0, ge=0, description="Sorting order index")

class RubricCriterionCreate(RubricCriterionBase):
    pass

class RubricCriterionUpdate(BaseModel):
    criterion: Optional[str] = None
    description: Optional[str] = None
    marks: Optional[float] = None
    min_marks: Optional[float] = None
    weight: Optional[float] = None
    partial_credit_rules: Optional[Dict[str, Any]] = None
    required: Optional[bool] = None
    order_index: Optional[int] = None

class RubricCriterionResponse(RubricCriterionBase):
    id: str
    rubric_id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class RubricCreate(BaseModel):
    name: str = Field(..., description="Rubric name")
    description: Optional[str] = Field(default=None)
    subject_id: Optional[str] = Field(default=None)
    question_type: Optional[str] = Field(default=None)
    question_id: Optional[str] = Field(default=None)
    question_paper_item_id: Optional[str] = Field(default=None)
    total_marks: float = Field(..., gt=0)
    status: str = Field(default="DRAFT")
    criteria: List[RubricCriterionCreate] = []

class RubricUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    subject_id: Optional[str] = None
    question_type: Optional[str] = None
    question_id: Optional[str] = None
    question_paper_item_id: Optional[str] = None
    total_marks: Optional[float] = None
    status: Optional[str] = None
    criteria: Optional[List[RubricCriterionCreate]] = None

class RubricResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    subject_id: Optional[str] = None
    question_type: Optional[str] = None
    question_id: Optional[str] = None
    question_paper_item_id: Optional[str] = None
    total_marks: float
    status: str
    version: int
    created_by: Optional[str] = None
    criteria: List[RubricCriterionResponse] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class RubricValidationResult(BaseModel):
    is_valid: bool
    total_criterion_marks: float
    configured_total_marks: float
    target_item_marks: Optional[float] = None
    errors: List[str] = []
    warnings: List[str] = []

class RubricAssignmentRequest(BaseModel):
    question_id: Optional[str] = None
    question_paper_item_id: Optional[str] = None
    answer_key_item_id: Optional[str] = None
