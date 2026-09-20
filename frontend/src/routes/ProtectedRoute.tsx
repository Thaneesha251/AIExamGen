import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { Box, CircularProgress, Typography } from '@mui/material';
import { useAuth } from '@/context/AuthContext';
import { UserRole } from '@/types/auth';

interface ProtectedRouteProps {
  children: React.ReactNode;
  allowedRoles?: UserRole[];
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children, allowedRoles }) => {
  const { isAuthenticated, isLoading, userRole } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <Box
        sx={{
          minHeight: '100vh',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)',
          color: '#fff',
        }}
      >
        <CircularProgress size={48} sx={{ color: '#60a5fa', mb: 2 }} />
        <Typography variant="body1" sx={{ color: '#94a3b8' }}>
          Verifying security credentials...
        </Typography>
      </Box>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (allowedRoles && allowedRoles.length > 0 && userRole) {
    if (!allowedRoles.includes(userRole as UserRole)) {
      // Redirect unauthorized user to their role-specific dashboard
      if (userRole === 'ADMIN') return <Navigate to="/admin/dashboard" replace />;
      if (userRole === 'FACULTY') return <Navigate to="/faculty/dashboard" replace />;
      if (userRole === 'STUDENT') return <Navigate to="/student/dashboard" replace />;
      return <Navigate to="/login" replace />;
    }
  }

  return <>{children}</>;
};
