from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

class PaperReviewChecklistResponse(BaseModel):
    paper_id: str
    paper_code: str
    active_version_number: int
    paper_status: str
    is_approvable: bool
    is_publishable: bool
    
    # Checklist flags
    blueprint_valid: bool
    paper_marks_valid: bool
    no_duplicate_questions: bool
    all_questions_approved: bool
    answer_key_exists: bool
    answer_key_marks_valid: bool
    rubrics_valid: bool
    
    errors: List[str] = []
    warnings: List[str] = []

class PaperApprovalRequest(BaseModel):
    comments: Optional[str] = Field(default=None, description="Faculty approval review comments")

class PaperPublishRequest(BaseModel):
    publish_notes: Optional[str] = Field(default=None, description="Publish notes or instructions")
