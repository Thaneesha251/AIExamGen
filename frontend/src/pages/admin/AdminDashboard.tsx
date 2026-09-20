import React from 'react';
import { Grid, Card, CardContent, Typography, Box, Button, Stack } from '@mui/material';
import { People, Business, School, Security, ArrowForward } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { PageContainer } from '@/components/layout/PageContainer';
import { useAuth } from '@/context/AuthContext';

export const AdminDashboard: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  const stats = [
    { title: 'System Users', count: '7 Active', desc: '1 Admin, 1 Faculty, 5 Students', icon: <People sx={{ color: '#2563eb', fontSize: 32 }} />, link: '/admin/users' },
    { title: 'Departments', count: '1 CSE', desc: 'Computer Science & Engineering', icon: <Business sx={{ color: '#7c3aed', fontSize: 32 }} /> },
    { title: 'Courses', count: '1 B.E. CSE', desc: '4-Year Degree Program', icon: <School sx={{ color: '#16a34a', fontSize: 32 }} /> },
    { title: 'Security Status', count: 'Active RBAC', desc: 'JWT Token Authentication Enabled', icon: <Security sx={{ color: '#dc2626', fontSize: 32 }} /> },
  ];

  return (
    <PageContainer
      title={`Welcome back, ${user?.first_name || 'Admin'}!`}
      subtitle="System Administrator Workspace — Manage users, departments, courses, and security policies"
    >
      <Grid container spacing={3}>
        {stats.map((stat, idx) => (
          <Grid item xs={12} sm={6} md={3} key={idx}>
            <Card elevation={0} sx={{ border: '1px solid #e2e8f0', borderRadius: 3, p: 1 }}>
              <CardContent>
                <Stack direction="row" justifyContent="space-between" alignItems="flex-start">
                  <Box>
                    <Typography variant="caption" sx={{ color: '#64748b', fontWeight: 600 }}>
                      {stat.title}
                    </Typography>
                    <Typography variant="h5" sx={{ fontWeight: 800, color: '#0f172a', mt: 0.5 }}>
                      {stat.count}
                    </Typography>
                    <Typography variant="caption" sx={{ color: '#94a3b8', display: 'block', mt: 0.5 }}>
                      {stat.desc}
                    </Typography>
                  </Box>
                  <Box sx={{ p: 1, backgroundColor: '#f8fafc', borderRadius: 2 }}>{stat.icon}</Box>
                </Stack>
                {stat.link && (
                  <Button
                    size="small"
                    endIcon={<ArrowForward />}
                    onClick={() => navigate(stat.link!)}
                    sx={{ mt: 2, p: 0, fontWeight: 700 }}
                  >
                    Manage Users
                  </Button>
                )}
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </PageContainer>
  );
};
