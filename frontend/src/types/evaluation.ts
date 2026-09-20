export interface RubricCriterionEvaluation {
  criterion_id: string;
  criterion_text: string;
  max_marks: number;
  awarded_marks: number;
  reasoning: string;
}

export interface EvaluationItem {
  id: string;
  evaluation_id: string;
  question_paper_item_id: string;
  extracted_answer_id?: string;
  question_number: string;
  maximum_marks: number;
  ai_marks: number;
  final_marks?: number;
  keyword_score: number;
  concept_score: number;
  semantic_score: number;
  pattern_score: number;
  rubric_score: number;
  ai_score: number;
  confidence: number;
  matched_keywords?: any;
  missing_keywords?: any;
  matched_concepts?: any;
  missing_concepts?: any;
  strengths?: any;
  missing_points?: any;
  evaluation_explanation?: string;
  rubric_evaluations?: RubricCriterionEvaluation[];
  requires_faculty_review: boolean;
  review_reason?: string;
  review_status?: string; // 'PENDING' | 'ACCEPTED' | 'OVERRIDDEN' | 'RE_EVALUATED'
  override_reason?: string;
  faculty_comment?: string;
  reviewed_by?: string;
  reviewed_at?: string;
}

export interface Evaluation {
  id: string;
  examination_id: string;
  answer_paper_id: string;
  student_id: string;
  version: number;
  evaluator_type: 'AI' | 'FACULTY' | 'HYBRID';
  status: 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'UNDER_REVIEW' | 'APPROVED' | 'FINALIZED' | 'REOPENED' | 'REJECTED';
  requires_review: boolean;
  total_ai_marks: number;
  total_final_marks?: number;
  overall_confidence: number;
  started_at?: string;
  completed_at?: string;
  reviewed_at?: string;
  reviewed_by?: string;
  approved_by?: string;
  approved_at?: string;
  finalized_by?: string;
  finalized_at?: string;
  review_notes?: string;
  finalization_notes?: string;
  items: EvaluationItem[];
}

export interface OverrideEvaluationItemRequest {
  final_marks: number;
  reason: string;
  comment?: string;
}

export interface AcceptAIRequest {
  comment?: string;
}

export interface BulkAcceptRequest {
  confidence_threshold?: number;
}

export interface ApproveEvaluationRequest {
  notes?: string;
}

export interface FinalizeEvaluationRequest {
  notes?: string;
}

export interface ReopenEvaluationRequest {
  reason: string;
}

export interface FacultyReviewRecord {
  id: string;
  evaluation_id: string;
  evaluation_item_id?: string;
  faculty_id: string;
  original_ai_marks?: number;
  revised_marks: number;
  comment?: string;
  reason?: string;
  action: string;
  reviewed_at?: string;
}
