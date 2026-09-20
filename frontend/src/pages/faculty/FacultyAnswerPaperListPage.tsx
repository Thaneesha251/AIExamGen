import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Table,
  TableHead,
  TableBody,
  TableRow,
  TableCell,
  Button,
  Chip,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  IconButton,
  CircularProgress,
  Alert
} from '@mui/material';
import VisibilityIcon from '@mui/icons-material/Visibility';
import RefreshIcon from '@mui/icons-material/Refresh';
import EditNoteIcon from '@mui/icons-material/EditNote';
import { listAnswerPapersForExam, processAnswerPaper } from '../../services/answerPaperService';
import { academicService } from '../../services/academicService';
import { AnswerPaper } from '../../types/answerPaper';

export const FacultyAnswerPaperListPage: React.FC = () => {
  const navigate = useNavigate();

  const [subjects, setSubjects] = useState<any[]>([]);
  const [selectedSubject, setSelectedSubject] = useState<string>('');
  const [answerPapers, setAnswerPapers] = useState<AnswerPaper[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    loadSubjects();
  }, []);

  const loadSubjects = async () => {
    try {
      const res = await academicService.getSubjects();
      const list = Array.isArray(res) ? res : (res as any).data || [];
      setSubjects(list);
      if (list && list.length > 0) {
        setSelectedSubject(list[0].id);
        fetchPapersForExam(list[0].id);
      }
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to load subjects.');
    }
  };

  const fetchPapersForExam = async (examId: string) => {
    setLoading(true);
    setErrorMsg(null);
    try {
      const papers = await listAnswerPapersForExam(examId);
      setAnswerPapers(papers);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to fetch answer papers.');
    } finally {
      setLoading(false);
    }
  };

  const handleRetryProcessing = async (paperId: string) => {
    try {
      await processAnswerPaper(paperId);
      if (selectedSubject) fetchPapersForExam(selectedSubject);
    } catch (err: any) {
      alert(err.message || 'Failed to retry processing.');
    }
  };

  const getStatusChipColor = (status: string) => {
    switch (status) {
      case 'EVALUATION_PENDING':
      case 'OCR_COMPLETED':
        return 'success';
      case 'PROCESSING':
      case 'UPLOADED':
        return 'warning';
      case 'ERROR':
        return 'error';
      default:
        return 'default';
    }
  };

  return (
    <Box sx={{ p: 4 }}>
      <Typography variant="h4" fontWeight={700} gutterBottom sx={{ color: 'primary.main' }}>
        Student Answer Papers & OCR Review
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
        Inspect student answer paper uploads, page-level OCR results, and answer segmentations. Correct OCR text or map question items before evaluation.
      </Typography>

      {errorMsg && <Alert severity="error" sx={{ mb: 3 }}>{errorMsg}</Alert>}

      <Card sx={{ borderRadius: 3, mb: 4 }}>
        <CardContent sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <FormControl sx={{ minWidth: 300 }}>
            <InputLabel>Select Subject / Examination</InputLabel>
            <Select
              value={selectedSubject}
              label="Select Subject / Examination"
              onChange={(e) => {
                setSelectedSubject(e.target.value);
                fetchPapersForExam(e.target.value);
              }}
            >
              {subjects.map((sub) => (
                <MenuItem key={sub.id} value={sub.id}>
                  {sub.name} ({sub.code})
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={() => selectedSubject && fetchPapersForExam(selectedSubject)}
          >
            Refresh List
          </Button>
        </CardContent>
      </Card>

      <Card sx={{ borderRadius: 3, boxShadow: 2 }}>
        <CardContent sx={{ p: 0 }}>
          {loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
              <CircularProgress />
            </Box>
          ) : (
            <Table>
              <TableHead sx={{ backgroundColor: 'action.hover' }}>
                <TableRow>
                  <TableCell sx={{ fontWeight: 700 }}>Student ID</TableCell>
                  <TableCell sx={{ fontWeight: 700 }}>Submission #</TableCell>
                  <TableCell sx={{ fontWeight: 700 }}>Pages</TableCell>
                  <TableCell sx={{ fontWeight: 700 }}>Segmented Answers</TableCell>
                  <TableCell sx={{ fontWeight: 700 }}>Status</TableCell>
                  <TableCell sx={{ fontWeight: 700 }} align="right">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {answerPapers.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={6} align="center" sx={{ py: 3 }}>
                      No student answer papers found for this examination.
                    </TableCell>
                  </TableRow>
                ) : (
                  answerPapers.map((paper) => (
                    <TableRow key={paper.id} hover>
                      <TableCell>{paper.student_id}</TableCell>
                      <TableCell>#{paper.submission_number}</TableCell>
                      <TableCell>{paper.pages.length} Pages</TableCell>
                      <TableCell>{paper.extracted_answers.length} Answers</TableCell>
                      <TableCell>
                        <Chip
                          label={paper.status}
                          color={getStatusChipColor(paper.status)}
                          size="small"
                          sx={{ fontWeight: 600 }}
                        />
                      </TableCell>
                      <TableCell align="right">
                        <Button
                          variant="contained"
                          size="small"
                          startIcon={<EditNoteIcon />}
                          onClick={() => navigate(`/faculty/answer-papers/${paper.id}/review`)}
                          sx={{ mr: 1 }}
                        >
                          Review OCR
                        </Button>
                        <Button
                          variant="outlined"
                          color="primary"
                          size="small"
                          onClick={() => navigate(`/faculty/answer-papers/${paper.id}/evaluation`)}
                          sx={{ mr: 1 }}
                        >
                          Evaluation
                        </Button>
                        <IconButton
                          size="small"
                          color="secondary"
                          title="Retry OCR Processing"
                          onClick={() => handleRetryProcessing(paper.id)}
                        >
                          <RefreshIcon />
                        </IconButton>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </Box>
  );
};
