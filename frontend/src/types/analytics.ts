export interface DimensionMetric {
  id: string;
  name: string;
  code?: string;
  marks_obtained: number;
  max_marks: number;
  percentage: number;
  response_count: number;
  average_marks: number;
  highest_marks?: number;
  lowest_marks?: number;
}

export interface ExamAnalyticsOverview {
  examination_id: string;
  examination_title: string;
  subject_id?: string;
  subject_name?: string;
  total_students: number;
  finalized_evaluations: number;
  average_marks: number;
  median_marks: number;
  highest_marks: number;
  lowest_marks: number;
  max_possible_marks: number;
  average_percentage: number;
  pass_percentage: number;
  generated_at: string;
}

export interface StudentPerformance {
  student_id: string;
  student_name: string;
  student_email?: string;
  examination_id: string;
  examination_title?: string;
  total_marks: number;
  max_marks: number;
  percentage: number;
  rank?: number;
  evaluation_status: string;
  finalized_at?: string;
  topic_breakdown?: DimensionMetric[];
  unit_breakdown?: DimensionMetric[];
  co_breakdown?: DimensionMetric[];
}

export interface QuestionAnalytics {
  question_id: string;
  question_number: string;
  question_text: string;
  question_type: string;
  bloom_level?: string;
  difficulty_level?: string;
  max_marks: number;
  average_marks: number;
  percentage_achieved: number;
  total_responses: number;
  highest_marks: number;
  lowest_marks: number;
}

export interface UnitAnalytics {
  id: string;
  name: string;
  question_count: number;
  max_marks: number;
  average_marks: number;
  percentage: number;
  response_count: number;
}

export interface TopicAnalytics {
  id: string;
  name: string;
  question_count: number;
  max_marks: number;
  average_marks: number;
  percentage: number;
  response_count: number;
}

export interface COAnalytics {
  id: string;
  name: string;
  question_count: number;
  max_marks: number;
  average_marks: number;
  percentage: number;
  response_count: number;
}

export interface BloomAnalytics {
  id: string;
  name: string;
  question_count: number;
  max_marks: number;
  average_marks: number;
  percentage: number;
  response_count: number;
}

export interface DifficultyAnalytics {
  id: string;
  name: string;
  question_count: number;
  max_marks: number;
  average_marks: number;
  percentage: number;
  response_count: number;
}

export interface SupportingQuestionEvidence {
  question_id: string;
  question_number: string;
  question_text: string;
  average_marks: number;
  max_marks: number;
  percentage: number;
}

export interface WeakTopicEvidence {
  topic_id: string;
  topic_name: string;
  unit_id?: string;
  unit_name?: string;
  subject_id?: string;
  subject_name?: string;
  response_count: number;
  average_marks: number;
  max_marks: number;
  percentage: number;
  threshold_percentage: number;
  minimum_responses_required: number;
  is_weak_topic: boolean;
  supporting_questions: SupportingQuestionEvidence[];
}

export interface WeakTopicResponse {
  examination_id?: string;
  student_id?: string;
  total_topics_analyzed: number;
  weak_topics_count: number;
  threshold_used: number;
  minimum_responses_used: number;
  weak_topics: WeakTopicEvidence[];
}
