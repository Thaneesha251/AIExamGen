export type QuestionType =
  | 'MCQ'
  | 'TRUE_FALSE'
  | 'FILL_BLANK'
  | 'SHORT_ANSWER'
  | 'DESCRIPTIVE'
  | 'PROBLEM_SOLVING'
  | 'NUMERICAL'
  | 'PROGRAMMING'
  | 'CASE_STUDY';

export type DifficultyLevel = 'EASY' | 'MEDIUM' | 'HARD';

export type BloomLevel =
  | 'REMEMBER'
  | 'UNDERSTAND'
  | 'APPLY'
  | 'ANALYZE'
  | 'EVALUATE'
  | 'CREATE';

export type QuestionStatus =
  | 'DRAFT'
  | 'AI_GENERATED'
  | 'UNDER_REVIEW'
  | 'APPROVED'
  | 'ACTIVE'
  | 'REJECTED'
  | 'ARCHIVED';

export interface MCQOptions {
  options: string[];
  correct_option: string;
  explanation?: string;
}

export interface ValidationData {
  is_valid: boolean;
  alignment_score: number;
  difficulty_score: number;
  bloom_alignment_score: number;
  duplicate_score: number;
  completeness_score: number;
  warnings: string[];
  similar_question_id?: string;
}

export interface QuestionVersion {
  id: string;
  question_id: string;
  version_number: number;
  question_text: string;
  marks: number;
  difficulty: DifficultyLevel;
  bloom_level: BloomLevel;
  expected_answer?: string;
  options?: MCQOptions;
  keywords?: string[];
  concepts?: string[];
  changed_by?: string;
  change_reason?: string;
  created_at: string;
}

export interface Question {
  id: string;
  subject_id: string;
  unit_id?: string;
  topic_id?: string;
  learning_outcome_id?: string;
  generation_run_id?: string;
  question_text: string;
  question_type: QuestionType;
  marks: number;
  difficulty: DifficultyLevel;
  bloom_level: BloomLevel;
  expected_answer?: string;
  options?: MCQOptions;
  keywords?: string[];
  concepts?: string[];
  source?: string;
  status: QuestionStatus;
  version: number;
  validation_data?: ValidationData;
  created_by?: string;
  versions?: QuestionVersion[];
  created_at: string;
  updated_at: string;
}

export interface QuestionListResponse {
  total: number;
  items: Question[];
  page: number;
  page_size: number;
}

export interface QuestionCreateRequest {
  subject_id: string;
  unit_id?: string;
  topic_id?: string;
  learning_outcome_id?: string;
  question_text: string;
  question_type: QuestionType;
  marks: number;
  difficulty: DifficultyLevel;
  bloom_level: BloomLevel;
  expected_answer?: string;
  options?: MCQOptions;
  keywords?: string[];
  concepts?: string[];
  status?: QuestionStatus;
  source?: string;
}

export interface QuestionUpdateRequest {
  subject_id?: string;
  unit_id?: string;
  topic_id?: string;
  learning_outcome_id?: string;
  question_text?: string;
  question_type?: QuestionType;
  marks?: number;
  difficulty?: DifficultyLevel;
  bloom_level?: BloomLevel;
  expected_answer?: string;
  options?: MCQOptions;
  keywords?: string[];
  concepts?: string[];
  status?: QuestionStatus;
  change_reason?: string;
}

export interface QuestionGenerationRequest {
  subject_id: string;
  unit_id?: string;
  topic_id?: string;
  learning_outcome_id?: string;
  question_type: QuestionType;
  difficulty: DifficultyLevel;
  bloom_level: BloomLevel;
  marks: number;
  count: number;
  language?: string;
}

export interface QuestionGenerationRun {
  id: string;
  subject_id: string;
  unit_id?: string;
  topic_id?: string;
  learning_outcome_id?: string;
  created_by: string;
  provider: string;
  model: string;
  prompt_version: string;
  status: string;
  requested_count: number;
  generated_count: number;
  accepted_count: number;
  rejected_count: number;
  error_message?: string;
  questions?: Question[];
  created_at: string;
  updated_at: string;
}

export interface QuestionBankItem {
  id: string;
  question_bank_id: string;
  question_id: string;
  added_by?: string;
  question?: Question;
  created_at: string;
}

export interface QuestionBank {
  id: string;
  subject_id: string;
  name: string;
  description?: string;
  created_by?: string;
  items?: QuestionBankItem[];
  created_at: string;
  updated_at: string;
}

export interface QuestionBankCreateRequest {
  subject_id: string;
  name: string;
  description?: string;
}
