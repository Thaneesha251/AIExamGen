from pydantic import BaseModel, Field
from typing import Optional, List
from backend.app.db.models.enums import AnswerPaperStatusEnum, ExtractionMethodEnum

class AnswerPageResponse(BaseModel):
    id: str
    answer_paper_id: str
    page_number: int
    file_asset_id: Optional[str] = None
    ocr_text: Optional[str] = None
    ocr_confidence: Optional[float] = None
    ocr_provider: Optional[str] = None
    processing_time: Optional[float] = None
    error_message: Optional[str] = None
    processing_status: str

    class Config:
        from_attributes = True


class ExtractedAnswerResponse(BaseModel):
    id: str
    answer_paper_id: str
    question_paper_item_id: Optional[str] = None
    answer_page_id: Optional[str] = None
    question_number: str
    extracted_text: str
    extraction_confidence: Optional[float] = None
    ocr_confidence: Optional[float] = None
    segmentation_confidence: Optional[float] = None
    page_start: Optional[int] = None
    page_end: Optional[int] = None
    extraction_method: ExtractionMethodEnum
    manually_corrected: bool
    status: str

    class Config:
        from_attributes = True


class AnswerPaperResponse(BaseModel):
    id: str
    examination_id: str
    student_id: str
    file_asset_id: Optional[str] = None
    submission_number: int
    status: AnswerPaperStatusEnum
    uploaded_at: Optional[str] = None
    processed_at: Optional[str] = None
    pages: List[AnswerPageResponse] = []
    extracted_answers: List[ExtractedAnswerResponse] = []

    class Config:
        from_attributes = True


class AnswerPaperStatusResponse(BaseModel):
    answer_paper_id: str
    status: str
    total_pages: int
    processed_pages: int
    ocr_completed_pages: int
    segmented_answers: int
    failed_pages: int
    progress_percent: int
    uploaded_at: Optional[str] = None
    processed_at: Optional[str] = None


class ExtractedAnswerUpdate(BaseModel):
    extracted_text: str = Field(..., min_length=1, description="Corrected OCR answer text")


class AnswerMappingRequest(BaseModel):
    extracted_answer_id: str
    question_paper_item_id: str


class AnswerMergeRequest(BaseModel):
    source_answer_ids: List[str] = Field(..., min_items=2)
    target_question_paper_item_id: Optional[str] = None
    target_question_number: str
