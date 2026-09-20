export interface PaperReviewChecklist {
  paper_id: string;
  paper_code: string;
  active_version_number: number;
  paper_status: string;
  is_approvable: boolean;
  is_publishable: boolean;
  
  blueprint_valid: boolean;
  paper_marks_valid: boolean;
  no_duplicate_questions: boolean;
  all_questions_approved: boolean;
  answer_key_exists: boolean;
  answer_key_marks_valid: boolean;
  rubrics_valid: boolean;
  
  errors: string[];
  warnings: string[];
}

export interface PaperApprovalPayload {
  comments?: string;
}

export interface PaperPublishPayload {
  publish_notes?: string;
}
