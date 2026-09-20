import { apiClient } from './api';
import {
  Evaluation,
  EvaluationItem,
  OverrideEvaluationItemRequest,
  AcceptAIRequest,
  BulkAcceptRequest,
  ApproveEvaluationRequest,
  FinalizeEvaluationRequest,
  ReopenEvaluationRequest,
  FacultyReviewRecord
} from '../types/evaluation';

export const triggerAnswerPaperEvaluation = async (paperId: string): Promise<Evaluation> => {
  const response = await apiClient.post<Evaluation>(`/evaluations/answer-papers/${paperId}/evaluate`);
  return response.data;
};

export const getEvaluationByPaperId = async (paperId: string): Promise<Evaluation> => {
  const response = await apiClient.get<Evaluation>(`/evaluations/answer-papers/${paperId}/active`);
  return response.data;
};

export const getEvaluationById = async (evaluationId: string): Promise<Evaluation> => {
  const response = await apiClient.get<Evaluation>(`/evaluations/${evaluationId}`);
  return response.data;
};

export const acceptItemAIMark = async (
  evaluationId: string,
  itemId: string,
  payload: AcceptAIRequest
): Promise<EvaluationItem> => {
  const response = await apiClient.post<EvaluationItem>(
    `/evaluations/${evaluationId}/items/${itemId}/accept`,
    payload
  );
  return response.data;
};

export const overrideItemMark = async (
  evaluationId: string,
  itemId: string,
  payload: OverrideEvaluationItemRequest
): Promise<EvaluationItem> => {
  const response = await apiClient.post<EvaluationItem>(
    `/evaluations/${evaluationId}/items/${itemId}/override`,
    payload
  );
  return response.data;
};

export const requestItemReevaluation = async (
  evaluationId: string,
  itemId: string,
  reason: string
): Promise<EvaluationItem> => {
  const response = await apiClient.post<EvaluationItem>(
    `/evaluations/${evaluationId}/items/${itemId}/request-reevaluation`,
    { reason }
  );
  return response.data;
};

export const bulkAcceptHighConfidence = async (
  evaluationId: string,
  threshold: number = 0.65
): Promise<{ accepted_count: number; skipped_count: number }> => {
  const response = await apiClient.post<{ accepted_count: number; skipped_count: number }>(
    `/evaluations/${evaluationId}/bulk-accept`,
    { confidence_threshold: threshold }
  );
  return response.data;
};

export const approveEvaluation = async (
  evaluationId: string,
  payload: ApproveEvaluationRequest
): Promise<Evaluation> => {
  const response = await apiClient.post<Evaluation>(
    `/evaluations/${evaluationId}/approve`,
    payload
  );
  return response.data;
};

export const finalizeEvaluation = async (
  evaluationId: string,
  payload: FinalizeEvaluationRequest
): Promise<Evaluation> => {
  const response = await apiClient.post<Evaluation>(
    `/evaluations/${evaluationId}/finalize`,
    payload
  );
  return response.data;
};

export const reopenEvaluation = async (
  evaluationId: string,
  payload: ReopenEvaluationRequest
): Promise<Evaluation> => {
  const response = await apiClient.post<Evaluation>(
    `/evaluations/${evaluationId}/reopen`,
    payload
  );
  return response.data;
};

export const getEvaluationReviews = async (
  evaluationId: string
): Promise<FacultyReviewRecord[]> => {
  const response = await apiClient.get<FacultyReviewRecord[]>(
    `/evaluations/${evaluationId}/reviews`
  );
  return response.data;
};
