import { apiClient } from './api';
import {
  Question,
  QuestionListResponse,
  QuestionCreateRequest,
  QuestionUpdateRequest,
  QuestionStatus,
  QuestionGenerationRequest,
  QuestionGenerationRun,
  QuestionBank,
  QuestionBankCreateRequest,
} from '../types/question';

export interface QuestionQueryParams {
  subject_id?: string;
  unit_id?: string;
  topic_id?: string;
  learning_outcome_id?: string;
  question_type?: string;
  difficulty?: string;
  bloom_level?: string;
  status?: string;
  source?: string;
  search?: string;
  page?: number;
  page_size?: number;
}

export const questionService = {
  // Question CRUD & Search
  searchQuestions: async (params: QuestionQueryParams): Promise<QuestionListResponse> => {
    const res = await apiClient.get('/questions', { params });
    return res.data.data;
  },

  getQuestionById: async (id: string): Promise<Question> => {
    const res = await apiClient.get(`/questions/${id}`);
    return res.data.data;
  },

  createQuestion: async (data: QuestionCreateRequest): Promise<Question> => {
    const res = await apiClient.post('/questions', data);
    return res.data.data;
  },

  updateQuestion: async (id: string, data: QuestionUpdateRequest): Promise<Question> => {
    const res = await apiClient.put(`/questions/${id}`, data);
    return res.data.data;
  },

  updateQuestionStatus: async (id: string, status: QuestionStatus, reason?: string): Promise<Question> => {
    const res = await apiClient.patch(`/questions/${id}/status`, { status, reason });
    return res.data.data;
  },

  importCsvQuestions: async (subjectId: string, file: File): Promise<{ created_count: number; failed_count: number; errors: string[] }> => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await apiClient.post(`/subjects/${subjectId}/questions/import-csv`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return res.data.data;
  },

  // AI Question Generation Runs
  generateQuestions: async (data: QuestionGenerationRequest): Promise<QuestionGenerationRun> => {
    const res = await apiClient.post('/questions/generate', data);
    return res.data.data;
  },

  getGenerationRun: async (runId: string): Promise<QuestionGenerationRun> => {
    const res = await apiClient.get(`/questions/generation-runs/${runId}`);
    return res.data.data;
  },

  // Question Banks
  listQuestionBanks: async (subjectId: string): Promise<QuestionBank[]> => {
    const res = await apiClient.get(`/question-banks/subject/${subjectId}`);
    return res.data.data;
  },

  getQuestionBankById: async (bankId: string): Promise<QuestionBank> => {
    const res = await apiClient.get(`/question-banks/${bankId}`);
    return res.data.data;
  },

  createQuestionBank: async (data: QuestionBankCreateRequest): Promise<QuestionBank> => {
    const res = await apiClient.post('/question-banks', data);
    return res.data.data;
  },

  updateQuestionBank: async (bankId: string, data: { name?: string; description?: string }): Promise<QuestionBank> => {
    const res = await apiClient.put(`/question-banks/${bankId}`, data);
    return res.data.data;
  },

  deleteQuestionBank: async (bankId: string): Promise<void> => {
    await apiClient.delete(`/question-banks/${bankId}`);
  },

  addQuestionsToBank: async (bankId: string, questionIds: string[]): Promise<QuestionBank> => {
    const res = await apiClient.post(`/question-banks/${bankId}/questions`, { question_ids: questionIds });
    return res.data.data;
  },

  removeQuestionFromBank: async (bankId: string, questionId: string): Promise<QuestionBank> => {
    const res = await apiClient.delete(`/question-banks/${bankId}/questions/${questionId}`);
    return res.data.data;
  },
};
