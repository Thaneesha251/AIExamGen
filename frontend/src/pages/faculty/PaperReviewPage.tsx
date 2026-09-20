import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  Chip,
  Button,
  Divider,
  Alert,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField
} from '@mui/material';
import {
  CheckCircle,
  Error as ErrorIcon,
  Warning,
  Approval,
  Publish,
  PictureAsPdf,
  EditNote,
  ArrowBack
} from '@mui/icons-material';
import { useParams, useNavigate } from 'react-router-dom';
import { PaperReviewChecklist } from '@/types/paperReview';
import { paperReviewService } from '@/services/paperReviewService';

export const PaperReviewPage: React.FC = () => {
  const { paperId } = useParams<{ paperId: string }>();
  const navigate = useNavigate();

  const [checklist, setChecklist] = useState<PaperReviewChecklist>({
    paper_id: paperId || 'paper-001',
    paper_code: 'QP-DS-2026-A',
    active_version_number: 1,
    paper_status: 'DRAFT',
    is_approvable: true,
    is_publishable: false,
    blueprint_valid: true,
    paper_marks_valid: true,
    no_duplicate_questions: true,
    all_questions_approved: true,
    answer_key_exists: true,
    answer_key_marks_valid: true,
    rubrics_valid: true,
    errors: [],
    warnings: ['Question #7 has no rubric assigned yet.']
  });

  const [approveOpen, setApproveOpen] = useState(false);
  const [publishOpen, setPublishOpen] = useState(false);
  const [comments, setComments] = useState('');
  const [notes, setNotes] = useState('');
  const [statusMsg, setStatusMsg] = useState('');

  const handleApprove = async () => {
    try {
      if (paperId) {
        await paperReviewService.approvePaper(paperId, { comments });
      }
      setChecklist((prev) => ({ ...prev, paper_status: 'APPROVED', is_publishable: true }));
      setStatusMsg('Question Paper approved successfully!');
      setApproveOpen(false);
    } catch (err: any) {
      console.error(err);
    }
  };

  const handlePublish = async () => {
    try {
      if (paperId) {
        await paperReviewService.publishPaper(paperId, { publish_notes: notes });
      }
      setChecklist((prev) => ({ ...prev, paper_status: 'PUBLISHED' }));
      setStatusMsg('Question Paper published successfully!');
      setPublishOpen(false);
    } catch (err: any) {
      console.error(err);
    }
  };

  const handleExportPaperPdf = async () => {
    try {
      const blob = await paperReviewService.exportQuestionPaperPdf(paperId || 'paper-001');
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `QuestionPaper_${checklist.paper_code}.pdf`;
      a.click();
    } catch (err) {
      console.error(err);
    }
  };

  const handleExportAnswerKeyPdf = async () => {
    try {
      const blob = await paperReviewService.exportAnswerKeyPdf(paperId || 'paper-001');
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `AnswerKey_${checklist.paper_code}.pdf`;
      a.click();
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <Box sx={{ p: 3, maxWidth: 1100, margin: '0 auto' }}>
      <Button startIcon={<ArrowBack />} onClick={() => navigate('/faculty/question-papers')} sx={{ mb: 2 }}>
        Back to Papers
      </Button>

      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 700, color: '#0f172a' }}>
            Faculty Paper Review & Checklist
          </Typography>
          <Typography variant="body2" sx={{ color: '#64748b' }}>
            Verify paper validation constraints, answer key alignment, and rubric criteria before approval and publication.
          </Typography>
        </Box>

        <Chip
          label={checklist.paper_status}
          color={checklist.paper_status === 'APPROVED' ? 'success' : checklist.paper_status === 'PUBLISHED' ? 'primary' : 'warning'}
          sx={{ fontWeight: 800, fontSize: '0.9rem', px: 1 }}
        />
      </Box>

      {statusMsg && (
        <Alert severity="success" sx={{ mb: 3 }} icon={<CheckCircle />}>
          {statusMsg}
        </Alert>
      )}

      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} md={7}>
          <Card sx={{ borderRadius: 3, boxShadow: '0 4px 20px rgba(0,0,0,0.05)', height: '100%' }}>
            <CardContent sx={{ p: 3 }}>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
                Academic & Structural Checklist
              </Typography>
              <Divider sx={{ mb: 2 }} />

              <List>
                <ListItem disablePadding sx={{ py: 0.8 }}>
                  <ListItemIcon>
                    {checklist.blueprint_valid ? <CheckCircle color="success" /> : <ErrorIcon color="error" />}
                  </ListItemIcon>
                  <ListItemText primary="Blueprint Constraints & Marks Allocation" secondary="Per-section question counts and total marks match configured blueprint" />
                </ListItem>

                <ListItem disablePadding sx={{ py: 0.8 }}>
                  <ListItemIcon>
                    {checklist.paper_marks_valid ? <CheckCircle color="success" /> : <ErrorIcon color="error" />}
                  </ListItemIcon>
                  <ListItemText primary="Total Paper Marks Integrity" secondary="Calculated question marks equal target paper total" />
                </ListItem>

                <ListItem disablePadding sx={{ py: 0.8 }}>
                  <ListItemIcon>
                    {checklist.no_duplicate_questions ? <CheckCircle color="success" /> : <ErrorIcon color="error" />}
                  </ListItemIcon>
                  <ListItemText primary="No Duplicate Questions" secondary="Each question item is unique within this paper version" />
                </ListItem>

                <ListItem disablePadding sx={{ py: 0.8 }}>
                  <ListItemIcon>
                    {checklist.all_questions_approved ? <CheckCircle color="success" /> : <ErrorIcon color="error" />}
                  </ListItemIcon>
                  <ListItemText primary="Question Status Eligibility" secondary="All selected questions have APPROVED or ACTIVE status" />
                </ListItem>

                <ListItem disablePadding sx={{ py: 0.8 }}>
                  <ListItemIcon>
                    {checklist.answer_key_exists && checklist.answer_key_marks_valid ? <CheckCircle color="success" /> : <ErrorIcon color="error" />}
                  </ListItemIcon>
                  <ListItemText primary="Answer Key & Model Answers" secondary="Answer key generated with model answers matching item marks" />
                </ListItem>
              </List>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={5}>
          <Card sx={{ borderRadius: 3, boxShadow: '0 4px 20px rgba(0,0,0,0.05)', height: '100%' }}>
            <CardContent sx={{ p: 3, display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
              <Box>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
                  Validation Summary
                </Typography>
                <Divider sx={{ mb: 2 }} />

                {checklist.errors.length > 0 && (
                  <Alert severity="error" icon={<ErrorIcon />} sx={{ mb: 2 }}>
                    <Typography variant="subtitle2" sx={{ fontWeight: 700 }}>Blocking Errors:</Typography>
                    {checklist.errors.map((e, idx) => (
                      <Typography variant="caption" display="block" key={idx}>• {e}</Typography>
                    ))}
                  </Alert>
                )}

                {checklist.warnings.length > 0 && (
                  <Alert severity="warning" icon={<Warning />} sx={{ mb: 2 }}>
                    <Typography variant="subtitle2" sx={{ fontWeight: 700 }}>Warnings:</Typography>
                    {checklist.warnings.map((w, idx) => (
                      <Typography variant="caption" display="block" key={idx}>• {w}</Typography>
                    ))}
                  </Alert>
                )}
              </Box>

              <Box sx={{ mt: 3, display: 'flex', flexDirection: 'column', gap: 1.5 }}>
                <Button
                  variant="outlined"
                  color="secondary"
                  startIcon={<EditNote />}
                  onClick={() => navigate(`/faculty/question-papers/${paperId}/answer-key`)}
                >
                  Manage Answer Key & Rubrics
                </Button>

                <Button
                  variant="outlined"
                  color="success"
                  startIcon={<PictureAsPdf />}
                  onClick={handleExportPaperPdf}
                >
                  Export Question Paper PDF
                </Button>

                <Button
                  variant="outlined"
                  color="info"
                  startIcon={<PictureAsPdf />}
                  onClick={handleExportAnswerKeyPdf}
                >
                  Export Faculty Answer Key PDF
                </Button>

                <Button
                  variant="contained"
                  color="success"
                  startIcon={<Approval />}
                  disabled={!checklist.is_approvable || checklist.paper_status === 'APPROVED' || checklist.paper_status === 'PUBLISHED'}
                  onClick={() => setApproveOpen(true)}
                >
                  Approve Question Paper
                </Button>

                <Button
                  variant="contained"
                  color="primary"
                  startIcon={<Publish />}
                  disabled={checklist.paper_status !== 'APPROVED'}
                  onClick={() => setPublishOpen(true)}
                >
                  Publish Question Paper
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Approve Dialog */}
      <Dialog open={approveOpen} onClose={() => setApproveOpen(false)} fullWidth maxWidth="sm">
        <DialogTitle sx={{ fontWeight: 700 }}>Approve Question Paper</DialogTitle>
        <DialogContent>
          <Typography variant="body2" sx={{ mb: 2 }}>
            Approving this paper verifies that all blueprint rules, questions, model answers, and rubrics have passed faculty review.
          </Typography>
          <TextField
            label="Faculty Approval Comments"
            multiline
            rows={3}
            fullWidth
            value={comments}
            onChange={(e) => setComments(e.target.value)}
            placeholder="Add any review notes or comments..."
          />
        </DialogContent>
        <DialogActions sx={{ p: 2 }}>
          <Button onClick={() => setApproveOpen(false)}>Cancel</Button>
          <Button variant="contained" color="success" onClick={handleApprove}>
            Confirm Approval
          </Button>
        </DialogActions>
      </Dialog>

      {/* Publish Dialog */}
      <Dialog open={publishOpen} onClose={() => setPublishOpen(false)} fullWidth maxWidth="sm">
        <DialogTitle sx={{ fontWeight: 700 }}>Publish Question Paper</DialogTitle>
        <DialogContent>
          <Typography variant="body2" sx={{ mb: 2 }}>
            Publishing freezes this paper version as immutable. Any subsequent modifications will require generating a new version.
          </Typography>
          <TextField
            label="Publishing Notes"
            multiline
            rows={3}
            fullWidth
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="e.g. Official paper for May 2026 examination..."
          />
        </DialogContent>
        <DialogActions sx={{ p: 2 }}>
          <Button onClick={() => setPublishOpen(false)}>Cancel</Button>
          <Button variant="contained" color="primary" onClick={handlePublish}>
            Confirm & Publish
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};
