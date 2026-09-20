import { apiClient } from './api';
import {
  SimilarityAnalysisRequest,
  AnswerSimilarity,
  PlagiarismResult,
  PlagiarismSummary,
  PlagiarismReviewRequest
} from '@/types/similarity';

export const similarityService = {
  analyzeExamination: async (
    examinationId: string,
    params?: SimilarityAnalysisRequest
  ): Promise<any> => {
    const response = await apiClient.post(`/plagiarism/examinations/${examinationId}/analyze`, params || {});
    return response.data;
  },

  getExaminationSummary: async (examinationId: string): Promise<PlagiarismSummary> => {
    const response = await apiClient.get(`/plagiarism/examinations/${examinationId}/summary`);
    return response.data;
  },

  getPaperPlagiarismResult: async (answerPaperId: string): Promise<PlagiarismResult> => {
    const response = await apiClient.get(`/plagiarism/answer-papers/${answerPaperId}`);
    return response.data;
  },

  getPaperSimilarities: async (answerPaperId: string): Promise<AnswerSimilarity[]> => {
    const response = await apiClient.get(`/plagiarism/answer-papers/${answerPaperId}/similarities`);
    return response.data;
  },

  reviewPlagiarismCase: async (
    resultId: string,
    data: PlagiarismReviewRequest
  ): Promise<PlagiarismResult> => {
    const response = await apiClient.post(`/plagiarism/results/${resultId}/review`, data);
    return response.data;
  }
};
