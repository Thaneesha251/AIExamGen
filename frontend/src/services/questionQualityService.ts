import { apiClient } from './api';
import {
  ExamQualityDashboard,
  QuestionQualityItem,
  BlueprintBalance,
  QuestionBankInsights,
  WeakCoverage,
  QuestionQualityReviewRequest,
  QuestionQualityReview
} from '@/types/questionQuality';

export const questionQualityService = {
  getExamQualityDashboard: async (examinationId: string): Promise<ExamQualityDashboard> => {
    const response = await apiClient.get(`/analytics/exams/${examinationId}/quality`);
    return response.data;
  },

  getExamQuestionsQualityList: async (examinationId: string): Promise<QuestionQualityItem[]> => {
    const response = await apiClient.get(`/analytics/exams/${examinationId}/questions`);
    return response.data;
  },

  getSingleQuestionQualityDetail: async (examinationId: string, questionId: string): Promise<any> => {
    const response = await apiClient.get(`/analytics/exams/${examinationId}/questions/${questionId}`);
    return response.data;
  },

  getExamDifficultyBreakdown: async (examinationId: string): Promise<any> => {
    const response = await apiClient.get(`/analytics/exams/${examinationId}/difficulty`);
    return response.data;
  },

  getExamDiscriminationBreakdown: async (examinationId: string): Promise<any> => {
    const response = await apiClient.get(`/analytics/exams/${examinationId}/discrimination`);
    return response.data;
  },

  getExamBlueprintBalance: async (examinationId: string): Promise<BlueprintBalance> => {
    const response = await apiClient.get(`/analytics/exams/${examinationId}/blueprint`);
    return response.data;
  },

  getQuestionBankInsights: async (subjectId: string): Promise<QuestionBankInsights> => {
    const response = await apiClient.get('/analytics/question-bank/insights', {
      params: { subject_id: subjectId }
    });
    return response.data;
  },

  getWeakAssessmentCoverage: async (subjectId: string): Promise<WeakCoverage> => {
    const response = await apiClient.get('/analytics/question-bank/weak-coverage', {
      params: { subject_id: subjectId }
    });
    return response.data;
  },

  recordQuestionQualityReview: async (
    questionId: string,
    data: QuestionQualityReviewRequest
  ): Promise<QuestionQualityReview> => {
    const response = await apiClient.post(`/analytics/questions/${questionId}/review`, data);
    return response.data;
  }
};
