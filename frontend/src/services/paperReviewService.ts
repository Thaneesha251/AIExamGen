import { apiClient } from './api';
import { PaperReviewChecklist, PaperApprovalPayload, PaperPublishPayload } from '@/types/paperReview';

export const paperReviewService = {
  getReviewChecklist: async (paperId: string): Promise<{ data: PaperReviewChecklist }> => {
    const res = await apiClient.get(`/question-papers/${paperId}/review`);
    return res.data;
  },

  approvePaper: async (paperId: string, payload: PaperApprovalPayload): Promise<{ data: any; message: string }> => {
    const res = await apiClient.post(`/question-papers/${paperId}/approve`, payload);
    return res.data;
  },

  publishPaper: async (paperId: string, payload: PaperPublishPayload): Promise<{ data: any; message: string }> => {
    const res = await apiClient.post(`/question-papers/${paperId}/publish`, payload);
    return res.data;
  },

  exportQuestionPaperPdf: async (paperId: string, versionNumber?: number): Promise<Blob> => {
    const res = await apiClient.get(`/question-papers/${paperId}/export/pdf`, {
      params: { version_number: versionNumber },
      responseType: 'blob'
    });
    return res.data;
  },

  exportAnswerKeyPdf: async (paperId: string, versionNumber?: number): Promise<Blob> => {
    const res = await apiClient.get(`/question-papers/${paperId}/answer-key/export/pdf`, {
      params: { version_number: versionNumber },
      responseType: 'blob'
    });
    return res.data;
  }
};

