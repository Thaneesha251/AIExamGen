export interface QuestionPaperItem {
  id: string;
  question_paper_version_id: string;
  question_id?: string;
  section: string;
  question_number: string;
  marks: number;
  question_text_snapshot: string;
  options_snapshot?: Record<string, any>;
  question_type_snapshot?: string;
  difficulty_snapshot?: string;
  bloom_snapshot?: string;
  order_index: number;
}

export interface QuestionPaperVersion {
  id: string;
  question_paper_id: string;
  version_number: number;
  generation_method: string;
  generated_by?: string;
  generation_metadata?: Record<string, any>;
  items: QuestionPaperItem[];
  created_at?: string;
}

export interface QuestionPaper {
  id: string;
  subject_id: string;
  blueprint_id?: string;
  title: string;
  paper_code: string;
  total_marks: number;
  duration_minutes: number;
  status: 'DRAFT' | 'GENERATED' | 'UNDER_REVIEW' | 'APPROVED' | 'PUBLISHED' | 'ARCHIVED';
  created_by?: string;
  versions?: QuestionPaperVersion[];
  created_at?: string;
  updated_at?: string;
}

export interface PaperGenerationPayload {
  subject_id: string;
  blueprint_id: string;
  title: string;
  paper_code?: string;
  duration_minutes?: number;
  generation_seed?: number;
}
