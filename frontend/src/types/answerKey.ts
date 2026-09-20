import { Rubric } from './rubric';

export interface AnswerKeyItem {
  id: string;
  answer_key_id: string;
  question_paper_item_id: string;
  model_answer: string;
  keywords?: string[];
  concepts?: string[];
  acceptable_answers?: string[];
  marking_notes?: string;
  maximum_marks: number;
  rubric_id?: string;
  rubric?: Rubric;
  created_at?: string;
  updated_at?: string;
}

export interface AnswerKey {
  id: string;
  question_paper_version_id: string;
  version_number: number;
  status: 'DRAFT' | 'UNDER_REVIEW' | 'APPROVED' | 'PUBLISHED' | 'ARCHIVED';
  generated_by?: string;
  approved_by?: string;
  items: AnswerKeyItem[];
  created_at?: string;
  updated_at?: string;
}

export interface AnswerKeyValidationResult {
  is_valid: boolean;
  total_items: number;
  total_marks: number;
  target_paper_marks: number;
  errors: string[];
  warnings: string[];
  item_summaries: Array<{
    question_number: string;
    paper_item_id: string;
    answer_key_item_id?: string;
    marks: number;
    has_rubric: boolean;
    status: string;
    error?: string;
  }>;
}

export interface AnswerKeyUpdatePayload {
  status?: string;
  items?: Array<{
    question_paper_item_id: string;
    model_answer: string;
    keywords?: string[];
    concepts?: string[];
    acceptable_answers?: string[];
    marking_notes?: string;
    maximum_marks: number;
    rubric_id?: string;
  }>;
}
