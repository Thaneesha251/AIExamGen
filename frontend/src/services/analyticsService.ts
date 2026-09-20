import { apiClient } from './api';
import {
  ExamAnalyticsOverview,
  StudentPerformance,
  QuestionAnalytics,
  UnitAnalytics,
  TopicAnalytics,
  COAnalytics,
  BloomAnalytics,
  DifficultyAnalytics,
  WeakTopicResponse
} from '@/types/analytics';

export const analyticsService = {
  getExamOverview: async (examinationId: string): Promise<ExamAnalyticsOverview> => {
    const response = await apiClient.get(`/analytics/examinations/${examinationId}`);
    return response.data;
  },

  getStudentPerformanceList: async (examinationId: string): Promise<StudentPerformance[]> => {
    const response = await apiClient.get(`/analytics/examinations/${examinationId}/students`);
    return response.data;
  },

  getQuestionAnalytics: async (examinationId: string): Promise<QuestionAnalytics[]> => {
    const response = await apiClient.get(`/analytics/examinations/${examinationId}/questions`);
    return response.data;
  },

  getUnitAnalytics: async (examinationId: string): Promise<UnitAnalytics[]> => {
    const response = await apiClient.get(`/analytics/examinations/${examinationId}/units`);
    return response.data;
  },

  getTopicAnalytics: async (examinationId: string): Promise<TopicAnalytics[]> => {
    const response = await apiClient.get(`/analytics/examinations/${examinationId}/topics`);
    return response.data;
  },

  getCOAnalytics: async (examinationId: string): Promise<COAnalytics[]> => {
    const response = await apiClient.get(`/analytics/examinations/${examinationId}/learning-outcomes`);
    return response.data;
  },

  getBloomAnalytics: async (examinationId: string): Promise<BloomAnalytics[]> => {
    const response = await apiClient.get(`/analytics/examinations/${examinationId}/bloom`);
    return response.data;
  },

  getDifficultyAnalytics: async (examinationId: string): Promise<DifficultyAnalytics[]> => {
    const response = await apiClient.get(`/analytics/examinations/${examinationId}/difficulty`);
    return response.data;
  },

  getExamWeakTopics: async (
    examinationId: string,
    threshold: number = 50.0,
    minResponses: number = 3
  ): Promise<WeakTopicResponse> => {
    const response = await apiClient.get(`/analytics/examinations/${examinationId}/weak-topics`, {
      params: { threshold, min_responses: minResponses }
    });
    return response.data;
  },

  getSingleStudentPerformance: async (studentId: string): Promise<any> => {
    const response = await apiClient.get(`/analytics/students/${studentId}`);
    return response.data;
  },

  getSingleStudentWeakTopics: async (
    studentId: string,
    threshold: number = 50.0,
    minResponses: number = 1
  ): Promise<WeakTopicResponse> => {
    const response = await apiClient.get(`/analytics/students/${studentId}/weak-topics`, {
      params: { threshold, min_responses: minResponses }
    });
    return response.data;
  }
};
