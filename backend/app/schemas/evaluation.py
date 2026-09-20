from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from backend.app.db.models.enums import EvaluatorTypeEnum, EvaluationStatusEnum

class EvaluationItemResponse(BaseModel):
    id: str
    evaluation_id: str
    question_paper_item_id: str
    extracted_answer_id: Optional[str] = None
    maximum_marks: float
    keyword_score: Optional[float] = None
    concept_score: Optional[float] = None
    semantic_score: Optional[float] = None
    pattern_score: Optional[float] = None
    rubric_score: Optional[float] = None
    ai_score: Optional[float] = None
    ai_marks: Optional[float] = None
    final_marks: Optional[float] = None
    confidence: Optional[float] = None
    matched_keywords: Optional[Dict[str, Any]] = None
    missing_keywords: Optional[Dict[str, Any]] = None
    matched_concepts: Optional[Dict[str, Any]] = None
    missing_concepts: Optional[Dict[str, Any]] = None
    strengths: Optional[Dict[str, Any]] = None
    missing_points: Optional[Dict[str, Any]] = None
    criterion_scores: Optional[Dict[str, Any]] = None
    requires_faculty_review: bool
    review_reason: Optional[str] = None
    prompt_version: Optional[str] = None
    evaluation_explanation: Optional[str] = None
    review_status: Optional[str] = "PENDING"
    override_reason: Optional[str] = None
    faculty_comment: Optional[str] = None
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[str] = None

    class Config:
        from_attributes = True


class EvaluationResponse(BaseModel):
    id: str
    examination_id: str
    answer_paper_id: str
    student_id: str
    version: int
    evaluator_type: EvaluatorTypeEnum
    status: EvaluationStatusEnum
    requires_review: bool
    total_ai_marks: Optional[float] = None
    total_final_marks: Optional[float] = None
    overall_confidence: Optional[float] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    reviewed_at: Optional[str] = None
    reviewed_by: Optional[str] = None
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None
    finalized_by: Optional[str] = None
    finalized_at: Optional[str] = None
    review_notes: Optional[str] = None
    finalization_notes: Optional[str] = None
    items: List[EvaluationItemResponse] = []

    class Config:
        from_attributes = True


class EvaluationSummaryResponse(BaseModel):
    evaluation_id: str
    answer_paper_id: str
    student_id: str
    version: int
    status: str
    total_ai_marks: Optional[float] = None
    total_final_marks: Optional[float] = None
    overall_confidence: Optional[float] = None
    requires_review: bool
    total_items: int
    reviewed_items: int


class ReevaluateItemRequest(BaseModel):
    reason: Optional[str] = Field(None, description="Faculty reason for item re-evaluation")


class AcceptAIRequest(BaseModel):
    comment: Optional[str] = Field(None, description="Optional faculty comment when accepting AI mark")


class OverrideMarksRequest(BaseModel):
    final_marks: float = Field(..., description="Revised final marks awarded by faculty")
    reason: str = Field(..., min_length=10, description="Mandatory reason for mark override (min 10 chars)")
    comment: Optional[str] = Field(None, description="Optional additional faculty comment")


class RequestReevaluationRequest(BaseModel):
    reason: str = Field(..., min_length=5, description="Reason for requesting AI re-evaluation")


class BulkAcceptRequest(BaseModel):
    confidence_threshold: float = Field(0.65, ge=0.0, le=1.0, description="Minimum confidence threshold for bulk acceptance")


class ApproveEvaluationRequest(BaseModel):
    notes: Optional[str] = Field(None, description="Optional approval notes")


class FinalizeEvaluationRequest(BaseModel):
    notes: Optional[str] = Field(None, description="Optional finalization notes")


class ReopenEvaluationRequest(BaseModel):
    reason: str = Field(..., min_length=10, description="Mandatory administrative reason for reopening finalized evaluation")


class FacultyReviewResponse(BaseModel):
    id: str
    evaluation_id: str
    evaluation_item_id: Optional[str] = None
    faculty_id: str
    original_ai_marks: Optional[float] = None
    revised_marks: float
    comment: Optional[str] = None
    reason: Optional[str] = None
    action: str
    reviewed_at: Optional[str] = None

    class Config:
        from_attributes = True
