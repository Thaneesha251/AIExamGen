import { apiClient } from './api';
import {
  AnswerPaper,
  AnswerPaperStatusResponse,
  ExtractedAnswer,
  ExtractedAnswerUpdate,
  AnswerMappingRequest,
  AnswerMergeRequest
} from '../types/answerPaper';

export const uploadAnswerPaper = async (
  examId: string,
  file: File,
  studentId?: string
): Promise<AnswerPaper> => {
  const formData = new FormData();
  formData.append('file', file);
  if (studentId) {
    formData.append('student_id', studentId);
  }

  const response = await apiClient.post<AnswerPaper>(
    `/answer-papers/examinations/${examId}`,
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }
  );
  return response.data;
};

export const getAnswerPaperDetails = async (paperId: string): Promise<AnswerPaper> => {
  const response = await apiClient.get<AnswerPaper>(`/answer-papers/${paperId}`);
  return response.data;
};

export const getAnswerPaperStatus = async (paperId: string): Promise<AnswerPaperStatusResponse> => {
  const response = await apiClient.get<AnswerPaperStatusResponse>(`/answer-papers/${paperId}/status`);
  return response.data;
};

export const listAnswerPapersForExam = async (examId: string): Promise<AnswerPaper[]> => {
  const response = await apiClient.get<AnswerPaper[]>(`/answer-papers/examination/${examId}`);
  return response.data;
};

export const processAnswerPaper = async (paperId: string): Promise<AnswerPaper> => {
  const response = await apiClient.post<AnswerPaper>(`/answer-papers/${paperId}/process`);
  return response.data;
};

export const retrySinglePageOCR = async (paperId: string, pageId: string): Promise<any> => {
  const response = await apiClient.post(`/answer-papers/${paperId}/pages/${pageId}/ocr`);
  return response.data;
};

export const correctOCRText = async (
  paperId: string,
  answerId: string,
  data: ExtractedAnswerUpdate
): Promise<ExtractedAnswer> => {
  const response = await apiClient.put<ExtractedAnswer>(
    `/answer-papers/${paperId}/extracted-answers/${answerId}`,
    data
  );
  return response.data;
};

export const mapAnswerToQuestion = async (
  paperId: string,
  data: AnswerMappingRequest
): Promise<ExtractedAnswer> => {
  const response = await apiClient.post<ExtractedAnswer>(
    `/answer-papers/${paperId}/map-answer`,
    data
  );
  return response.data;
};

export const mergeAnswerSegments = async (
  paperId: string,
  data: AnswerMergeRequest
): Promise<ExtractedAnswer> => {
  const response = await apiClient.post<ExtractedAnswer>(
    `/answer-papers/${paperId}/merge-answers`,
    data
  );
  return response.data;
};

export const completeOCRReview = async (paperId: string): Promise<AnswerPaper> => {
  const response = await apiClient.post<AnswerPaper>(`/answer-papers/${paperId}/complete-review`);
  return response.data;
};

export const getAnswerPaperFileUrl = (paperId: string): string => {
  const token = localStorage.getItem('token');
  const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';
  return `${baseUrl}/answer-papers/${paperId}/file?token=${token}`;
};
