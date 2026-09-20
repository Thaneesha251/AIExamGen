export type AnswerPaperStatus = 
  | 'UPLOADED'
  | 'PROCESSING'
  | 'OCR_COMPLETED'
  | 'EVALUATION_PENDING'
  | 'EVALUATED'
  | 'UNDER_REVIEW'
  | 'FINALIZED'
  | 'ERROR';

export type ExtractionMethod = 'OCR' | 'MANUAL' | 'HYBRID';

export interface AnswerPage {
  id: string;
  answer_paper_id: string;
  page_number: number;
  file_asset_id?: string;
  ocr_text?: string;
  ocr_confidence?: number;
  ocr_provider?: string;
  processing_time?: number;
  error_message?: string;
  processing_status: string;
}

export interface ExtractedAnswer {
  id: string;
  answer_paper_id: string;
  question_paper_item_id?: string;
  answer_page_id?: string;
  question_number: string;
  extracted_text: string;
  extraction_confidence?: number;
  ocr_confidence?: number;
  segmentation_confidence?: number;
  page_start?: number;
  page_end?: number;
  extraction_method: ExtractionMethod;
  manually_corrected: boolean;
  status: string;
}

export interface AnswerPaper {
  id: string;
  examination_id: string;
  student_id: string;
  file_asset_id?: string;
  submission_number: number;
  status: AnswerPaperStatus;
  uploaded_at?: string;
  processed_at?: string;
  pages: AnswerPage[];
  extracted_answers: ExtractedAnswer[];
}

export interface AnswerPaperStatusResponse {
  answer_paper_id: string;
  status: AnswerPaperStatus;
  total_pages: number;
  processed_pages: number;
  ocr_completed_pages: number;
  segmented_answers: number;
  failed_pages: number;
  progress_percent: number;
  uploaded_at?: string;
  processed_at?: string;
}

export interface ExtractedAnswerUpdate {
  extracted_text: string;
}

export interface AnswerMappingRequest {
  extracted_answer_id: string;
  question_paper_item_id: string;
}

export interface AnswerMergeRequest {
  source_answer_ids: string[];
  target_question_paper_item_id?: string;
  target_question_number: string;
}
