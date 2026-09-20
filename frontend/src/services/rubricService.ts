import { apiClient } from './api';
import { Rubric, RubricCreatePayload, RubricValidationResult } from '@/types/rubric';

export const rubricService = {
  createRubric: async (payload: RubricCreatePayload): Promise<{ data: Rubric; validation: RubricValidationResult }> => {
    const res = await apiClient.post('/rubrics', payload);
    return res.data;
  },

  listRubrics: async (subjectId?: string, questionType?: string): Promise<{ data: Rubric[] }> => {
    const params: Record<string, string> = {};
    if (subjectId) params.subject_id = subjectId;
    if (questionType) params.question_type = questionType;
    const res = await apiClient.get('/rubrics', { params });
    return res.data;
  },

  getRubric: async (rubricId: string): Promise<{ data: Rubric; validation: RubricValidationResult }> => {
    const res = await apiClient.get(`/rubrics/${rubricId}`);
    return res.data;
  },

  updateRubric: async (rubricId: string, payload: Partial<RubricCreatePayload>): Promise<{ data: Rubric; validation: RubricValidationResult }> => {
    const res = await apiClient.put(`/rubrics/${rubricId}`, payload);
    return res.data;
  },

  deleteRubric: async (rubricId: string): Promise<{ success: boolean }> => {
    const res = await apiClient.delete(`/rubrics/${rubricId}`);
    return res.data;
  },

  assignRubric: async (rubricId: string, payload: { question_id?: string; question_paper_item_id?: string; answer_key_item_id?: string }): Promise<{ data: Rubric; validation: RubricValidationResult }> => {
    const res = await apiClient.post(`/rubrics/${rubricId}/assign`, payload);
    return res.data;
  }
};

