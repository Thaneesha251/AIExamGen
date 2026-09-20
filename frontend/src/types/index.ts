export type UserRole = 'ADMIN' | 'FACULTY' | 'STUDENT';

export interface UserProfile {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  department_id?: string;
  is_active: boolean;
}

export interface HealthResponse {
  success: boolean;
  status: string;
  service: string;
  environment: string;
  database: string;
  ai_provider: string;
  ocr_provider: string;
}

export * from './user';
export * from './auth';
export * from './academic';
export * from './question';
export * from './questionPaper';
export * from './answerKey';
export * from './rubric';
export * from './paperReview';

