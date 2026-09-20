import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { LoginPage } from '@/pages/auth/LoginPage';
import { AdminDashboard } from '@/pages/admin/AdminDashboard';
import { UserManagementPage } from '@/pages/admin/UserManagementPage';
import { FacultyDashboard } from '@/pages/faculty/FacultyDashboard';
import { QuestionBankPage } from '@/pages/faculty/QuestionBankPage';
import { QuestionGenerationPage } from '@/pages/faculty/QuestionGenerationPage';
import { BlueprintBuilderPage } from '@/pages/faculty/BlueprintBuilderPage';
import { PaperListPage } from '@/pages/faculty/PaperListPage';
import { PaperReviewPage } from '@/pages/faculty/PaperReviewPage';
import { AnswerKeyEditorPage } from '@/pages/faculty/AnswerKeyEditorPage';
import { RubricManagementPage } from '@/pages/faculty/RubricManagementPage';
import { FacultyAnswerPaperListPage } from '@/pages/faculty/FacultyAnswerPaperListPage';
import { FacultyOCRReviewPage } from '@/pages/faculty/FacultyOCRReviewPage';
import { FacultyEvaluationViewPage } from '@/pages/faculty/FacultyEvaluationViewPage';
import { SimilarityAnalysisPage } from '@/pages/faculty/SimilarityAnalysisPage';
import { PerformanceAnalyticsPage } from '@/pages/faculty/PerformanceAnalyticsPage';
import { ExamQualityPage } from '@/pages/faculty/ExamQualityPage';
import { StudentDashboard } from '@/pages/student/StudentDashboard';
import { StudentAnswerPaperUploadPage } from '@/pages/student/StudentAnswerPaperUploadPage';
import { ProfilePage } from '@/pages/profile/ProfilePage';
import { ProtectedRoute } from '@/routes/ProtectedRoute';
import { AppLayout } from '@/components/layout/AppLayout';

export const AppRoutes: React.FC = () => {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/login" replace />} />
      <Route path="/login" element={<LoginPage />} />

      {/* Admin Protected Routes */}
      <Route
        path="/admin/dashboard"
        element={
          <ProtectedRoute allowedRoles={['ADMIN']}>
            <AppLayout>
              <AdminDashboard />
            </AppLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/admin/users"
        element={
          <ProtectedRoute allowedRoles={['ADMIN']}>
            <AppLayout>
              <UserManagementPage />
            </AppLayout>
          </ProtectedRoute>
        }
      />

      {/* Faculty Protected Routes */}
      <Route
        path="/faculty/dashboard"
        element={
          <ProtectedRoute allowedRoles={['FACULTY']}>
            <AppLayout>
              <FacultyDashboard />
            </AppLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/faculty/question-bank"
        element={
          <ProtectedRoute allowedRoles={['FACULTY', 'ADMIN']}>
            <AppLayout>
              <QuestionBankPage />
            </AppLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/faculty/question-generation"
        element={
          <ProtectedRoute allowedRoles={['FACULTY', 'ADMIN']}>
            <AppLayout>
              <QuestionGenerationPage />
            </AppLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/faculty/blueprints"
        element={
          <ProtectedRoute allowedRoles={['FACULTY', 'ADMIN']}>
            <AppLayout>
              <BlueprintBuilderPage />
            </AppLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/faculty/question-papers"
        element={
          <ProtectedRoute allowedRoles={['FACULTY', 'ADMIN']}>
            <AppLayout>
              <PaperListPage />
            </AppLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/faculty/question-papers/:paperId/review"
        element={
          <ProtectedRoute allowedRoles={['FACULTY', 'ADMIN']}>
            <AppLayout>
              <PaperReviewPage />
            </AppLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/faculty/question-papers/:paperId/answer-key"
        element={
          <ProtectedRoute allowedRoles={['FACULTY', 'ADMIN']}>
            <AppLayout>
              <AnswerKeyEditorPage />
            </AppLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/faculty/rubrics"
        element={
          <ProtectedRoute allowedRoles={['FACULTY', 'ADMIN']}>
            <AppLayout>
              <RubricManagementPage />
            </AppLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/faculty/answer-papers"
        element={
          <ProtectedRoute allowedRoles={['FACULTY', 'ADMIN']}>
            <AppLayout>
              <FacultyAnswerPaperListPage />
            </AppLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/faculty/answer-papers/:paperId/review"
        element={
          <ProtectedRoute allowedRoles={['FACULTY', 'ADMIN']}>
            <AppLayout>
              <FacultyOCRReviewPage />
            </AppLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/faculty/answer-papers/:paperId/evaluation"
        element={
          <ProtectedRoute allowedRoles={['FACULTY', 'ADMIN']}>
            <AppLayout>
              <FacultyEvaluationViewPage />
            </AppLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/faculty/similarity"
        element={
          <ProtectedRoute allowedRoles={['FACULTY', 'ADMIN']}>
            <AppLayout>
              <SimilarityAnalysisPage />
            </AppLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/faculty/analytics"
        element={
          <ProtectedRoute allowedRoles={['FACULTY', 'ADMIN']}>
            <AppLayout>
              <PerformanceAnalyticsPage />
            </AppLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/faculty/exam-quality"
        element={
          <ProtectedRoute allowedRoles={['FACULTY', 'ADMIN']}>
            <AppLayout>
              <ExamQualityPage />
            </AppLayout>
          </ProtectedRoute>
        }
      />


      {/* Student Protected Routes */}
      <Route
        path="/student/dashboard"
        element={
          <ProtectedRoute allowedRoles={['STUDENT']}>
            <AppLayout>
              <StudentDashboard />
            </AppLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/student/examinations/:examId/answer-paper"
        element={
          <ProtectedRoute allowedRoles={['STUDENT']}>
            <AppLayout>
              <StudentAnswerPaperUploadPage />
            </AppLayout>
          </ProtectedRoute>
        }
      />

      {/* Universal Authenticated Profile Route */}
      <Route
        path="/profile"
        element={
          <ProtectedRoute allowedRoles={['ADMIN', 'FACULTY', 'STUDENT']}>
            <AppLayout>
              <ProfilePage />
            </AppLayout>
          </ProtectedRoute>
        }
      />

      {/* Fallback Catch-all Redirect */}
      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  );
};

