export interface RubricCriterion {
  id?: string;
  rubric_id?: string;
  criterion: string;
  description?: string;
  marks: number;
  min_marks?: number;
  weight?: number;
  partial_credit_rules?: Record<string, any>;
  required?: boolean;
  order_index?: number;
  created_at?: string;
  updated_at?: string;
}

export interface Rubric {
  id: string;
  name: string;
  description?: string;
  subject_id?: string;
  question_type?: string;
  question_id?: string;
  question_paper_item_id?: string;
  total_marks: number;
  status: string;
  version: number;
  created_by?: string;
  criteria: RubricCriterion[];
  created_at?: string;
  updated_at?: string;
}

export interface RubricCreatePayload {
  name: string;
  description?: string;
  subject_id?: string;
  question_type?: string;
  question_id?: string;
  question_paper_item_id?: string;
  total_marks: number;
  status?: string;
  criteria: RubricCriterion[];
}

export interface RubricValidationResult {
  is_valid: boolean;
  total_criterion_marks: number;
  configured_total_marks: number;
  target_item_marks?: number;
  errors: string[];
  warnings: string[];
}
