from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field

class SimilarityAnalysisRequest(BaseModel):
    lexical_weight: float = Field(0.5, ge=0.0, le=1.0, description="Weight for lexical similarity score")
    semantic_weight: float = Field(0.5, ge=0.0, le=1.0, description="Weight for semantic similarity score")
    flag_threshold: float = Field(0.70, ge=0.0, le=1.0, description="Threshold above which pairs are flagged for review")
    minimum_text_length: int = Field(15, ge=1, description="Minimum answer text length required for analysis")


class AnswerSimilarityResponse(BaseModel):
    id: str
    examination_id: Optional[str] = None
    question_id: Optional[str] = None
    question_number: Optional[str] = None
    question_text: Optional[str] = None
    source_answer_id: str
    source_student_id: Optional[str] = None
    source_student_name: Optional[str] = None
    source_answer_text: Optional[str] = None
    target_answer_id: str
    target_student_id: Optional[str] = None
    target_student_name: Optional[str] = None
    target_answer_text: Optional[str] = None
    similarity_score: float
    lexical_score: Optional[float] = None
    semantic_score: Optional[float] = None
    combined_score: Optional[float] = None
    flagged_for_review: bool = False
    method: str
    created_at: Optional[Union[datetime, str]] = None
    updated_at: Optional[Union[datetime, str]] = None

    class Config:
        from_attributes = True


class PlagiarismResultResponse(BaseModel):
    id: str
    examination_id: str
    answer_paper_id: str
    student_id: Optional[str] = None
    student_name: Optional[str] = None
    answer_a_id: Optional[str] = None
    answer_b_id: Optional[str] = None
    similarity_score: float
    lexical_score: Optional[float] = None
    semantic_score: Optional[float] = None
    combined_score: Optional[float] = None
    threshold_used: Optional[float] = None
    analysis_version: Optional[str] = None
    matching_segments: Optional[Dict[str, Any]] = None
    detection_method: str
    status: str  # FLAGGED, REVIEWED, DISMISSED
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[str] = None
    review_notes: Optional[str] = None
    created_at: Optional[Union[datetime, str]] = None
    updated_at: Optional[Union[datetime, str]] = None

    class Config:
        from_attributes = True



class PlagiarismSummaryResponse(BaseModel):
    examination_id: str
    examination_title: Optional[str] = None
    total_answer_papers: int
    analyzed_answer_papers: int
    total_comparable_answers: int
    flagged_cases_count: int
    reviewed_cases_count: int
    dismissed_cases_count: int
    flag_threshold_used: float
    high_similarity_threshold: float
    analysis_timestamp: Optional[Union[datetime, str]] = None

    flagged_results: List[PlagiarismResultResponse] = []
    top_similarities: List[AnswerSimilarityResponse] = []


class PlagiarismReviewRequest(BaseModel):
    status: str = Field(..., description="Target review status: REVIEWED or DISMISSED")
    review_notes: str = Field(..., min_length=3, description="Faculty review notes or explanation")
