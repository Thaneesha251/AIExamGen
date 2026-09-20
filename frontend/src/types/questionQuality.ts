export interface QuestionPerformance {
  question_id: string;
  total_responses: number;
  valid_responses: number;
  average_marks: number;
  max_marks: number;
  average_percentage: number;
  minimum_marks: number;
  highest_marks: number;
  full_mark_percentage: number;
  zero_mark_percentage: number;
  partial_mark_percentage: number;
}

export interface DifficultyAnalysis {
  question_id: string;
  difficulty_index: number;
  difficulty_category: 'EASY' | 'MODERATE' | 'DIFFICULT';
}

export interface DiscriminationAnalysis {
  question_id: string;
  discrimination_index: number | null;
  discrimination_category: 'STRONG' | 'ACCEPTABLE' | 'WEAK' | 'NEGATIVE' | 'INSUFFICIENT_SAMPLE';
  upper_group_mean: number | null;
  lower_group_mean: number | null;
  cohort_size: number;
}

export interface SimilarityIntegration {
  flagged_pair_count: number;
  highest_similarity: number;
  average_similarity: number;
  reviewed_cases: number;
  dismissed_cases: number;
}

export interface QuestionQualityItem {
  question_id: string;
  question_number: string;
  question_text: string;
  unit_title: string;
  topic_name: string;
  co_code: string;
  bloom_level: string;
  configured_difficulty: string;
  max_marks: number;
  average_percentage: number;
  difficulty_category: 'EASY' | 'MODERATE' | 'DIFFICULT';
  discrimination_index: number | null;
  discrimination_category: 'STRONG' | 'ACCEPTABLE' | 'WEAK' | 'NEGATIVE' | 'INSUFFICIENT_SAMPLE';
  similarity_flag_count: number;
  quality_status: 'GOOD' | 'REVIEW_DIFFICULTY' | 'REVIEW_DISCRIMINATION' | 'REVIEW_SIMILARITY' | 'REVIEW_MULTIPLE_SIGNALS' | 'INSUFFICIENT_DATA';
  faculty_review_status: 'UNREVIEWED' | 'REVIEWED' | 'KEEP' | 'REVIEW_BEFORE_REUSE';
  faculty_review_note?: string | null;
}

export interface ExamQualityDashboard {
  examination_id: string;
  examination_title: string;
  subject_name?: string | null;
  total_questions: number;
  finalized_responses: number;
  average_exam_score: number;
  average_exam_percentage: number;
  questions_analyzed: number;
  questions_requiring_review: number;
  difficulty_distribution: Record<string, number>;
  discrimination_distribution: Record<string, number>;
  quality_status_summary: Record<string, number>;
  questions: QuestionQualityItem[];
}

export interface BlueprintVarianceItem {
  dimension: string;
  category_name: string;
  target_percentage: number;
  actual_percentage: number;
  variance: number;
  status: 'BALANCED' | 'REVIEW_VARIANCE';
}

export interface BlueprintBalance {
  examination_id: string;
  blueprint_id?: string | null;
  blueprint_name: string;
  total_marks: number;
  overall_status: 'BALANCED' | 'REVIEW_VARIANCE';
  max_variance: number;
  variance_tolerance_used: number;
  breakdown: BlueprintVarianceItem[];
}

export interface QuestionInsightItem {
  question_id: string;
  question_text: string;
  unit_title: string;
  configured_difficulty: string;
  bloom_level: string;
  times_used: number;
  total_responses: number;
  historical_average_percentage?: number | null;
  status_indicator: string;
}

export interface QuestionBankInsights {
  subject_id: string;
  subject_name: string;
  total_questions_in_bank: number;
  questions: QuestionInsightItem[];
}

export interface UnitCoverageItem {
  unit_id: string;
  unit_number: number;
  unit_title: string;
  available_questions: number;
  times_assessed: number;
  coverage_level: 'LOW' | 'MODERATE' | 'HIGH';
}

export interface WeakCoverage {
  subject_id: string;
  units_analyzed: number;
  unit_coverage: UnitCoverageItem[];
}

export interface QuestionQualityReviewRequest {
  examination_id?: string;
  status: 'REVIEWED' | 'KEEP' | 'REVIEW_BEFORE_REUSE';
  note?: string;
}

export interface QuestionQualityReview {
  id: string;
  question_id: string;
  examination_id?: string | null;
  reviewer_id?: string | null;
  status: string;
  note?: string | null;
  reviewed_at?: string | null;
}
