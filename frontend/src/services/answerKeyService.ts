import { apiClient } from './api';
import { AnswerKey, AnswerKeyValidationResult, AnswerKeyUpdatePayload } from '@/types/answerKey';

export const answerKeyService = {
  generateAnswerKey: async (versionId: string): Promise<{ data: AnswerKey; validation: AnswerKeyValidationResult }> => {
    const res = await apiClient.post(`/question-papers/versions/${versionId}/answer-key/generate`);
    return res.data;
  },

  getAnswerKeyForVersion: async (versionId: string): Promise<{ data: AnswerKey; validation: AnswerKeyValidationResult }> => {
    const res = await apiClient.get(`/question-papers/versions/${versionId}/answer-key`);
    return res.data;
  },

  getAnswerKeyById: async (keyId: string): Promise<{ data: AnswerKey; validation: AnswerKeyValidationResult }> => {
    const res = await apiClient.get(`/answer-keys/${keyId}`);
    return res.data;
  },

  updateAnswerKey: async (keyId: string, payload: AnswerKeyUpdatePayload): Promise<{ data: AnswerKey; validation: AnswerKeyValidationResult }> => {
    const res = await apiClient.put(`/answer-keys/${keyId}`, payload);
    return res.data;
  },

  validateAnswerKey: async (keyId: string): Promise<{ data: AnswerKeyValidationResult }> => {
    const res = await apiClient.post(`/answer-keys/${keyId}/validate`);
    return res.data;
  }
};

