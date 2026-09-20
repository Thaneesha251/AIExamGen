export interface SimilarityAnalysisRequest {
  lexical_weight?: number;
  semantic_weight?: number;
  flag_threshold?: number;
  minimum_text_length?: number;
}

export interface AnswerSimilarity {
  id: string;
  examination_id?: string;
  question_id?: string;
  question_number?: string;
  question_text?: string;
  source_answer_id: string;
  source_student_id?: string;
  source_student_name?: string;
  source_answer_text?: string;
  target_answer_id: string;
  target_student_id?: string;
  target_student_name?: string;
  target_answer_text?: string;
  similarity_score: number;
  lexical_score?: number;
  semantic_score?: number;
  combined_score?: number;
  flagged_for_review: boolean;
  method: string;
  created_at?: string;
}

export interface PlagiarismResult {
  id: string;
  examination_id: string;
  answer_paper_id: string;
  student_id?: string;
  student_name?: string;
  answer_a_id?: string;
  answer_b_id?: string;
  similarity_score: number;
  lexical_score?: number;
  semantic_score?: number;
  combined_score?: number;
  threshold_used?: number;
  analysis_version?: string;
  matching_segments?: Record<string, any>;
  detection_method: string;
  status: 'FLAGGED' | 'REVIEWED' | 'DISMISSED' | 'COMPLETED';
  reviewed_by?: string;
  reviewed_at?: string;
  review_notes?: string;
  created_at?: string;
}

export interface PlagiarismSummary {
  examination_id: string;
  examination_title?: string;
  total_answer_papers: number;
  analyzed_answer_papers: number;
  total_comparable_answers: number;
  flagged_cases_count: number;
  reviewed_cases_count: number;
  dismissed_cases_count: number;
  flag_threshold_used: number;
  high_similarity_threshold: number;
  analysis_timestamp?: string;
  flagged_results: PlagiarismResult[];
  top_similarities: AnswerSimilarity[];
}

export interface PlagiarismReviewRequest {
  status: 'REVIEWED' | 'DISMISSED';
  review_notes: string;
}
