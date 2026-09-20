import React from 'react';
import { Grid, Card, CardContent, Typography, Box, Stack } from '@mui/material';
import { MenuBook, Quiz, AssignmentTurnedIn, Grade } from '@mui/icons-material';
import { PageContainer } from '@/components/layout/PageContainer';
import { useAuth } from '@/context/AuthContext';

export const FacultyDashboard: React.FC = () => {
  const { user } = useAuth();

  const cards = [
    { title: 'Assigned Subjects', value: 'CS301', desc: 'Data Structures & Algorithms', icon: <MenuBook sx={{ color: '#2563eb', fontSize: 32 }} /> },
    { title: 'Question Bank', value: '20+ Questions', desc: 'Covering 5 Units & 15 Topics', icon: <Quiz sx={{ color: '#7c3aed', fontSize: 32 }} /> },
    { title: 'Exam Blueprint', value: '1 Active', desc: '100-Mark End Semester Pattern', icon: <AssignmentTurnedIn sx={{ color: '#16a34a', fontSize: 32 }} /> },
    { title: 'Evaluations', value: 'Ready', desc: 'OCR & Semantic Scoring Ready', icon: <Grade sx={{ color: '#fbbf24', fontSize: 32 }} /> },
  ];

  return (
    <PageContainer
      title={`Welcome back, ${user?.first_name || 'Faculty Member'}!`}
      subtitle="Faculty Workspace — Manage subject syllabi, question banks, exam blueprints, and answer paper evaluation"
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
