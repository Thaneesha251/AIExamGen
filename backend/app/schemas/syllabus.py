from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field
from backend.app.db.models.enums import BloomLevelEnum, SyllabusProcessingStatusEnum

class SourceReference(BaseModel):
    page: Optional[int] = None
    section: Optional[str] = None
    source_text: Optional[str] = None

class SyllabusTopic(BaseModel):
    title: str = Field(..., min_length=1)
    keywords: Optional[str] = None
    source_reference: Optional[SourceReference] = None

class SyllabusUnit(BaseModel):
    unit_number: int = Field(..., ge=1)
    title: str = Field(..., min_length=1)
    description: Optional[str] = None
    weightage: Optional[float] = None
    topics: List[SyllabusTopic] = []
    source_reference: Optional[SourceReference] = None

class SyllabusLearningOutcome(BaseModel):
    code: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    bloom_level: Optional[BloomLevelEnum] = None
    source_reference: Optional[SourceReference] = None

class SyllabusStructure(BaseModel):
    course_title: Optional[str] = None
    course_code: Optional[str] = None
    subject_code: Optional[str] = None
    subject_name: Optional[str] = None
    units: List[SyllabusUnit] = []
    learning_outcomes: List[SyllabusLearningOutcome] = []
    warnings: List[str] = []

class FileAssetInfo(BaseModel):
    id: str
    original_filename: str
    stored_filename: str
    file_size: int
    mime_type: str
    checksum: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class SyllabusDocumentResponse(BaseModel):
    id: str
    subject_id: str
    uploaded_by: str
    file_asset_id: str
    version: int
    is_current: bool
    status: SyllabusProcessingStatusEnum
    processing_error: Optional[str] = None
    extracted_text: Optional[str] = None
    structured_data: Optional[Dict[str, Any]] = None
    file_asset: Optional[FileAssetInfo] = None
    created_at: Any
    updated_at: Any

    model_config = ConfigDict(from_attributes=True)

class SyllabusReviewUpdate(BaseModel):
    structured_data: SyllabusStructure
