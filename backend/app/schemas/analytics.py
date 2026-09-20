from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class DimensionMetric(BaseModel):
    id: str
    name: str
    code: Optional[str] = None
    marks_obtained: float
    max_marks: float
    percentage: float
    response_count: int
    average_marks: float
    highest_marks: Optional[float] = None
    lowest_marks: Optional[float] = None


class ExamAnalyticsOverviewResponse(BaseModel):
    examination_id: str
    examination_title: str
    subject_id: Optional[str] = None
    subject_name: Optional[str] = None
    total_students: int
    finalized_evaluations: int
    average_marks: float
    median_marks: float
    highest_marks: float
    lowest_marks: float
    max_possible_marks: float
    average_percentage: float
    pass_percentage: float
    generated_at: str


class StudentPerformanceResponse(BaseModel):
    student_id: str
    student_name: str
    student_email: Optional[str] = None
    examination_id: str
    examination_title: Optional[str] = None
    total_marks: float
    max_marks: float
    percentage: float
    rank: Optional[int] = None
    evaluation_status: str
    finalized_at: Optional[str] = None
    topic_breakdown: List[DimensionMetric] = []
    unit_breakdown: List[DimensionMetric] = []
    co_breakdown: List[DimensionMetric] = []


class QuestionAnalyticsResponse(BaseModel):
    question_id: str
    question_number: str
    question_text: str
    question_type: str
    bloom_level: Optional[str] = None
    difficulty_level: Optional[str] = None
    max_marks: float
    average_marks: float
    percentage_achieved: float
    total_responses: int
    highest_marks: float
    lowest_marks: float


class UnitAnalyticsResponse(BaseModel):
    unit_id: str
    unit_name: str
    unit_number: Optional[int] = None
    question_count: int
    max_marks: float
    average_marks: float
    percentage: float
    response_count: int


class TopicAnalyticsResponse(BaseModel):
    topic_id: str
    topic_name: str
    unit_id: Optional[str] = None
    unit_name: Optional[str] = None
    question_count: int
    max_marks: float
    average_marks: float
    percentage: float
    response_count: int


class COAnalyticsResponse(BaseModel):
    learning_outcome_id: str
    code: str
    description: str
    question_count: int
    max_marks: float
    average_marks: float
    percentage: float
    response_count: int


class BloomAnalyticsResponse(BaseModel):
    bloom_level: str
    question_count: int
    max_marks: float
    average_marks: float
    percentage: float
    response_count: int


class DifficultyAnalyticsResponse(BaseModel):
    difficulty_level: str
    question_count: int
    max_marks: float
    average_marks: float
    percentage: float
    response_count: int


class SupportingQuestionEvidence(BaseModel):
    question_id: str
    question_number: str
    question_text: str
    average_marks: float
    max_marks: float
    percentage: float


class WeakTopicEvidence(BaseModel):
    topic_id: str
    topic_name: str
    unit_id: Optional[str] = None
    unit_name: Optional[str] = None
    subject_id: Optional[str] = None
    subject_name: Optional[str] = None
    response_count: int
    average_marks: float
    max_marks: float
    percentage: float
    threshold_percentage: float
    minimum_responses_required: int
    is_weak_topic: bool
    supporting_questions: List[SupportingQuestionEvidence] = []


class WeakTopicResponse(BaseModel):
    examination_id: Optional[str] = None
    student_id: Optional[str] = None
    total_topics_analyzed: int
    weak_topics_count: int
    threshold_used: float
    minimum_responses_used: int
    weak_topics: List[WeakTopicEvidence] = []
