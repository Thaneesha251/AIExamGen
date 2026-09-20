import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Chip,
  Button,
  IconButton,
  Tooltip,
  CircularProgress
} from '@mui/material';
import { Add, Visibility, EditNote, PictureAsPdf, CheckCircle, RateReview } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { QuestionPaper } from '@/types/questionPaper';
import { paperReviewService } from '@/services/paperReviewService';

export const PaperListPage: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);

  // Demonstration state
  const papers: QuestionPaper[] = [
    {
      id: 'paper-001',
      subject_id: 'sub-001',
      title: 'Data Structures End-Semester Examination',
      paper_code: 'QP-DS-2026-A',
      total_marks: 100,
      duration_minutes: 180,
      status: 'APPROVED' as any,
      created_at: new Date().toISOString()
    },
    {
      id: 'paper-002',
      subject_id: 'sub-001',
      title: 'Algorithms Mid-Semester Paper',
      paper_code: 'QP-ALG-2026-B',
      total_marks: 50,
      duration_minutes: 90,
      status: 'DRAFT' as any,
      created_at: new Date().toISOString()
    }
  ];

  const handleExportPdf = async (paperId: string, title: string) => {
    try {
      const blob = await paperReviewService.exportQuestionPaperPdf(paperId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${title.replace(/\s+/g, '_')}_Paper.pdf`;
      a.click();
    } catch (err) {
      console.error('Export PDF error', err);
    }
  };

  const getStatusChip = (statusStr: string) => {
    switch (statusStr) {
      case 'APPROVED':
        return <Chip label="APPROVED" color="success" size="small" sx={{ fontWeight: 700 }} />;
      case 'PUBLISHED':
        return <Chip label="PUBLISHED" color="primary" size="small" sx={{ fontWeight: 700 }} />;
      case 'UNDER_REVIEW':
        return <Chip label="UNDER REVIEW" color="warning" size="small" sx={{ fontWeight: 700 }} />;
      default:
        return <Chip label="DRAFT" color="default" size="small" sx={{ fontWeight: 700 }} />;
    }
  };

  return (
    <Box sx={{ p: 3, maxWidth: 1200, margin: '0 auto' }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 700, color: '#0f172a' }}>
            Question Papers
          </Typography>
          <Typography variant="body2" sx={{ color: '#64748b' }}>
            Manage generated question papers, faculty review checklists, answer keys, and print-ready PDF exports.
          </Typography>
        </Box>

        <Button
          variant="contained"
          startIcon={<Add />}
          onClick={() => navigate('/faculty/question-generation')}
          sx={{ borderRadius: 2.5, px: 3, py: 1 }}
        >
          Generate New Paper
        </Button>
      </Box>

      <Card sx={{ borderRadius: 3, boxShadow: '0 4px 20px rgba(0,0,0,0.05)' }}>
        <CardContent sx={{ p: 0 }}>
          <Table>
            <TableHead sx={{ bgcolor: '#f8fafc' }}>
              <TableRow>
                <TableCell sx={{ fontWeight: 700 }}>Paper Code</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Title</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Total Marks</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Duration</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Status</TableCell>
                <TableCell align="right" sx={{ fontWeight: 700 }}>Actions</TableCell>
              </TableRow>
            </TableHead>

            <TableBody>
              {papers.map((p) => (
                <TableRow key={p.id} hover>
                  <TableCell sx={{ fontFamily: 'monospace', fontWeight: 700 }}>{p.paper_code}</TableCell>
                  <TableCell sx={{ fontWeight: 600 }}>{p.title}</TableCell>
                  <TableCell>{p.total_marks} Marks</TableCell>
                  <TableCell>{p.duration_minutes} Mins</TableCell>
                  <TableCell>{getStatusChip(p.status as any)}</TableCell>
                  <TableCell align="right">
                    <Tooltip title="Faculty Review & Approval">
                      <IconButton color="primary" onClick={() => navigate(`/faculty/question-papers/${p.id}/review`)}>
                        <RateReview />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Answer Key Editor">
                      <IconButton color="secondary" onClick={() => navigate(`/faculty/question-papers/${p.id}/answer-key`)}>
                        <EditNote />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Export Question Paper PDF">
                      <IconButton color="success" onClick={() => handleExportPdf(p.id, p.title)}>
                        <PictureAsPdf />
                      </IconButton>
                    </Tooltip>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </Box>
  );
};
