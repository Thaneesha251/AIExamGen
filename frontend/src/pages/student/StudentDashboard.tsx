import React from 'react';
import { Grid, Card, CardContent, Typography, Box, Stack } from '@mui/material';
import { School, AssignmentTurnedIn, Analytics, AccountCircle } from '@mui/icons-material';
import { PageContainer } from '@/components/layout/PageContainer';
import { useAuth } from '@/context/AuthContext';

export const StudentDashboard: React.FC = () => {
  const { user } = useAuth();

  const cards = [
    { title: 'Student Profile', value: user?.registration_number || 'Registered', desc: `${user?.first_name} ${user?.last_name}`, icon: <AccountCircle sx={{ color: '#2563eb', fontSize: 32 }} /> },
    { title: 'Enrolled Course', value: 'B.E. CSE', desc: 'Semester 3', icon: <School sx={{ color: '#7c3aed', fontSize: 32 }} /> },
    { title: 'Assigned Exams', value: 'CS301 DSA', desc: 'End Semester Examination', icon: <AssignmentTurnedIn sx={{ color: '#16a34a', fontSize: 32 }} /> },
    { title: 'Performance Analytics', value: 'Active', desc: 'Unit & Bloom level feedback ready', icon: <Analytics sx={{ color: '#fbbf24', fontSize: 32 }} /> },
  ];

  return (
    <PageContainer
      title={`Welcome back, ${user?.first_name || 'Student'}!`}
      subtitle="Student Workspace — View assigned examinations, evaluated answer keys, and performance breakdown"
    >
      <Grid container spacing={3}>
        {cards.map((card, idx) => (
          <Grid item xs={12} sm={6} md={3} key={idx}>
            <Card elevation={0} sx={{ border: '1px solid #e2e8f0', borderRadius: 3, p: 1 }}>
              <CardContent>
                <Stack direction="row" justifyContent="space-between" alignItems="flex-start">
                  <Box>
                    <Typography variant="caption" sx={{ color: '#64748b', fontWeight: 600 }}>
                      {card.title}
                    </Typography>
                    <Typography variant="h6" sx={{ fontWeight: 800, color: '#0f172a', mt: 0.5 }}>
                      {card.value}
                    </Typography>
                    <Typography variant="caption" sx={{ color: '#94a3b8', display: 'block', mt: 0.5 }}>
                      {card.desc}
                    </Typography>
                  </Box>
                  <Box sx={{ p: 1, backgroundColor: '#f8fafc', borderRadius: 2 }}>{card.icon}</Box>
                </Stack>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </PageContainer>
  );
};
