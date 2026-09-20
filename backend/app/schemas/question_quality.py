from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class QuestionPerformanceResponse(BaseModel):
    question_id: str
    total_responses: int
    valid_responses: int
    average_marks: float
    max_marks: float
    average_percentage: float
    minimum_marks: float
    highest_marks: float
    full_mark_percentage: float
    zero_mark_percentage: float
    partial_mark_percentage: float

class DifficultyAnalysisResponse(BaseModel):
    question_id: str
    difficulty_index: float
    difficulty_category: str  # EASY, MODERATE, DIFFICULT

class DiscriminationAnalysisResponse(BaseModel):
    question_id: str
    discrimination_index: Optional[float] = None
    discrimination_category: str  # STRONG, ACCEPTABLE, WEAK, NEGATIVE, INSUFFICIENT_SAMPLE
    upper_group_mean: Optional[float] = None
    lower_group_mean: Optional[float] = None
    cohort_size: int

class SimilarityIntegrationResponse(BaseModel):
    flagged_pair_count: int
    highest_similarity: float
    average_similarity: float
    reviewed_cases: int
    dismissed_cases: int

class QuestionQualityItemResponse(BaseModel):
    question_id: str
    question_number: str
    question_text: str
    unit_title: str
    topic_name: str
    co_code: str
    bloom_level: str
    configured_difficulty: str
    max_marks: float
    average_percentage: float
    difficulty_category: str
    discrimination_index: Optional[float] = None
    discrimination_category: str
    similarity_flag_count: int
    quality_status: str  # GOOD, REVIEW_DIFFICULTY, REVIEW_DISCRIMINATION, REVIEW_SIMILARITY, REVIEW_MULTIPLE_SIGNALS, INSUFFICIENT_DATA
    faculty_review_status: str  # UNREVIEWED, REVIEWED, KEEP, REVIEW_BEFORE_REUSE
    faculty_review_note: Optional[str] = None

class ExamQualityDashboardResponse(BaseModel):
    examination_id: str
    examination_title: str
    subject_name: Optional[str] = None
    total_questions: int
    finalized_responses: int
    average_exam_score: float
    average_exam_percentage: float
    questions_analyzed: int
    questions_requiring_review: int
    difficulty_distribution: Dict[str, int]
    discrimination_distribution: Dict[str, int]
    quality_status_summary: Dict[str, int]
    questions: List[QuestionQualityItemResponse]

class BlueprintVarianceItem(BaseModel):
    dimension: str
    category_name: str
    target_percentage: float
    actual_percentage: float
    variance: float
    status: str  # BALANCED, REVIEW_VARIANCE

class BlueprintBalanceResponse(BaseModel):
    examination_id: str
    blueprint_id: Optional[str] = None
    blueprint_name: str
    total_marks: float
    overall_status: str  # BALANCED, REVIEW_VARIANCE
    max_variance: float
    variance_tolerance_used: float
    breakdown: List[BlueprintVarianceItem]

class QuestionInsightItem(BaseModel):
    question_id: str
    question_text: str
    unit_title: str
    configured_difficulty: str
    bloom_level: str
    times_used: int
    total_responses: int
    historical_average_percentage: Optional[float] = None
    status_indicator: str

class QuestionBankInsightsResponse(BaseModel):
    subject_id: str
    subject_name: str
    total_questions_in_bank: int
    questions: List[QuestionInsightItem]

class UnitCoverageItem(BaseModel):
    unit_id: str
    unit_number: int
    unit_title: str
    available_questions: int
    times_assessed: int
    coverage_level: str  # LOW, MODERATE, HIGH

class WeakCoverageResponse(BaseModel):
    subject_id: str
    units_analyzed: int
    unit_coverage: List[UnitCoverageItem]

class QuestionQualityReviewRequest(BaseModel):
    examination_id: Optional[str] = None
    status: str = Field(default="REVIEWED")  # REVIEWED, KEEP, REVIEW_BEFORE_REUSE
    note: Optional[str] = None

class QuestionQualityReviewResponse(BaseModel):
    id: str
    question_id: str
    examination_id: Optional[str] = None
    reviewer_id: Optional[str] = None
    status: str
    note: Optional[str] = None
    reviewed_at: Optional[str] = None
