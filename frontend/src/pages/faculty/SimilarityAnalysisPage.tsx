import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Typography,
  Paper,
  Grid,
  Button,
  TextField,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  CircularProgress,
  Divider,
  Card,
  CardContent,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  Compare,
  CheckCircle,
  Cancel,
  Warning,
  Refresh,
  Visibility,
  Security,
  Analytics
} from '@mui/icons-material';
import { similarityService } from '@/services/similarityService';
import { PlagiarismSummary, PlagiarismResult, AnswerSimilarity } from '@/types/similarity';

export const SimilarityAnalysisPage: React.FC = () => {
  const [examId, setExamId] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [analyzing, setAnalyzing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [summary, setSummary] = useState<PlagiarismSummary | null>(null);

  // Review Dialog State
  const [selectedResult, setSelectedResult] = useState<PlagiarismResult | null>(null);
  const [reviewModalOpen, setReviewModalOpen] = useState<boolean>(false);
  const [reviewAction, setReviewAction] = useState<'REVIEWED' | 'DISMISSED'>('REVIEWED');
  const [reviewNotes, setReviewNotes] = useState<string>('');
  const [submittingReview, setSubmittingReview] = useState<boolean>(false);

  // Evidence Inspection State
  const [inspectModalOpen, setInspectModalOpen] = useState<boolean>(false);

  const fetchSummary = async (targetExamId: string) => {
    if (!targetExamId.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const data = await similarityService.getExaminationSummary(targetExamId);
      setSummary(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch similarity analysis summary');
    } finally {
      setLoading(false);
    }
  };

  const handleRunAnalysis = async () => {
    if (!examId.trim()) {
      setError('Please enter a valid Examination ID');
      return;
    }
    setAnalyzing(true);
    setError(null);
    try {
      await similarityService.analyzeExamination(examId, {
        lexical_weight: 0.5,
        semantic_weight: 0.5,
        flag_threshold: 0.70
      });
      await fetchSummary(examId);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to execute similarity analysis');
    } finally {
      setAnalyzing(false);
    }
  };

  const handleOpenReview = (result: PlagiarismResult, action: 'REVIEWED' | 'DISMISSED') => {
    setSelectedResult(result);
    setReviewAction(action);
    setReviewNotes('');
    setReviewModalOpen(true);
  };

  const handleSubmitReview = async () => {
    if (!selectedResult || reviewNotes.trim().length < 3) {
      setError('Please provide detailed faculty review notes (at least 3 characters)');
      return;
    }
    setSubmittingReview(true);
    try {
      await similarityService.reviewPlagiarismCase(selectedResult.id, {
        status: reviewAction,
        review_notes: reviewNotes
      });
      setReviewModalOpen(false);
      if (examId) await fetchSummary(examId);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to update review status');
    } finally {
      setSubmittingReview(false);
    }
  };

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 6 }}>
      {/* Header Banner */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 800, color: '#1e293b', mb: 1, display: 'flex', alignItems: 'center', gap: 1.5 }}>
          <Compare color="primary" fontSize="large" /> Answer Similarity & Plagiarism Review
        </Typography>
        <Typography variant="body1" sx={{ color: '#64748b' }}>
          Analyze student answer papers for lexical and semantic text overlap to identify suspicious similarities requiring academic review.
        </Typography>
      </Box>

      {/* Mandatory Non-Cheating Policy Alert */}
      <Alert severity="warning" icon={<Security fontSize="inherit" />} sx={{ mb: 4, borderRadius: 2 }}>
        <Typography variant="subtitle2" sx={{ fontWeight: 700 }}>
          Faculty Review Flagging Policy
        </Typography>
        Similarity detection produces analytical indicators and evidence flags for faculty evaluation. Similarity results do <strong>NEVER</strong> automatically declare a student guilty of plagiarism or cheating. Faculty remains solely responsible for the final academic determination.
      </Alert>

      {/* Examination Selector & Action */}
      <Paper sx={{ p: 3, mb: 4, borderRadius: 3, border: '1px solid #e2e8f0' }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Examination ID"
              placeholder="Enter Examination UUID..."
              value={examId}
              onChange={(e) => setExamId(e.target.value)}
              variant="outlined"
              size="medium"
            />
          </Grid>
          <Grid item xs={12} md={3}>
            <Button
              fullWidth
              variant="contained"
              color="primary"
              size="large"
              startIcon={analyzing ? <CircularProgress size={20} color="inherit" /> : <Analytics />}
              onClick={handleRunAnalysis}
              disabled={analyzing || !examId.trim()}
              sx={{ py: 1.5, borderRadius: 2, fontWeight: 700 }}
            >
              {analyzing ? 'Analyzing...' : 'Run Similarity Analysis'}
            </Button>
          </Grid>
          <Grid item xs={12} md={3}>
            <Button
              fullWidth
              variant="outlined"
              size="large"
              startIcon={<Refresh />}
              onClick={() => fetchSummary(examId)}
              disabled={loading || !examId.trim()}
              sx={{ py: 1.5, borderRadius: 2 }}
            >
              Fetch Summary
            </Button>
          </Grid>
        </Grid>

        {error && (
          <Alert severity="error" sx={{ mt: 2 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}
      </Paper>

      {/* Summary Metrics Cards */}
      {summary && (
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ borderRadius: 3, bgcolor: '#f8fafc', border: '1px solid #e2e8f0' }}>
              <CardContent>
                <Typography variant="caption" sx={{ color: '#64748b', fontWeight: 700 }}>
                  TOTAL ANSWER PAPERS
                </Typography>
                <Typography variant="h3" sx={{ fontWeight: 800, color: '#1e293b', mt: 1 }}>
                  {summary.total_answer_papers}
                </Typography>
                <Typography variant="caption" sx={{ color: '#94a3b8' }}>
                  {summary.analyzed_answer_papers} analyzed
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ borderRadius: 3, bgcolor: '#fef2f2', border: '1px solid #fecaca' }}>
              <CardContent>
                <Typography variant="caption" sx={{ color: '#991b1b', fontWeight: 700 }}>
                  FLAGGED FOR REVIEW
                </Typography>
                <Typography variant="h3" sx={{ fontWeight: 800, color: '#dc2626', mt: 1 }}>
                  {summary.flagged_cases_count}
                </Typography>
                <Typography variant="caption" sx={{ color: '#ef4444' }}>
                  Threshold: &ge; {(summary.flag_threshold_used * 100).toFixed(0)}%
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ borderRadius: 3, bgcolor: '#f0fdf4', border: '1px solid #bbf7d0' }}>
              <CardContent>
                <Typography variant="caption" sx={{ color: '#166534', fontWeight: 700 }}>
                  REVIEWED CASES
                </Typography>
                <Typography variant="h3" sx={{ fontWeight: 800, color: '#16a34a', mt: 1 }}>
                  {summary.reviewed_cases_count}
                </Typography>
                <Typography variant="caption" sx={{ color: '#22c55e' }}>
                  Faculty decision confirmed
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ borderRadius: 3, bgcolor: '#f8fafc', border: '1px solid #cbd5e1' }}>
              <CardContent>
                <Typography variant="caption" sx={{ color: '#475569', fontWeight: 700 }}>
                  DISMISSED CASES
                </Typography>
                <Typography variant="h3" sx={{ fontWeight: 800, color: '#64748b', mt: 1 }}>
                  {summary.dismissed_cases_count}
                </Typography>
                <Typography variant="caption" sx={{ color: '#94a3b8' }}>
                  Cleared false positives
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Flagged Cases Results Table */}
      {summary && (
        <Paper sx={{ p: 3, borderRadius: 3, border: '1px solid #e2e8f0' }}>
          <Typography variant="h6" sx={{ fontWeight: 700, mb: 2 }}>
            Similarity Analysis Results ({summary.flagged_results.length})
          </Typography>

          {summary.flagged_results.length === 0 ? (
            <Box sx={{ py: 6, textCenter: 'center', textAlign: 'center' }}>
              <CheckCircle color="success" sx={{ fontSize: 48, mb: 1 }} />
              <Typography variant="h6" sx={{ color: '#475569' }}>
                No High Similarity Cases Detected
              </Typography>
              <Typography variant="body2" sx={{ color: '#94a3b8' }}>
                All student answer papers for this examination fell below the review threshold.
              </Typography>
            </Box>
          ) : (
            <TableContainer>
              <Table>
                <TableHead sx={{ bgcolor: '#f8fafc' }}>
                  <TableRow>
                    <TableCell sx={{ fontWeight: 700 }}>Answer Paper ID</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Similarity Score</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Lexical Score</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Semantic Score</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Detection Method</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Status</TableCell>
                    <TableCell sx={{ fontWeight: 700, textAlign: 'right' }}>Faculty Action</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {summary.flagged_results.map((item) => (
                    <TableRow key={item.id} hover>
                      <TableCell sx={{ fontFamily: 'monospace', fontWeight: 600 }}>
                        {item.answer_paper_id.slice(0, 8)}...
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={`${(item.similarity_score * 100).toFixed(1)}%`}
                          color={item.similarity_score >= 0.85 ? 'error' : 'warning'}
                          sx={{ fontWeight: 700 }}
                        />
                      </TableCell>
                      <TableCell>{(item.lexical_score ? item.lexical_score * 100 : 0).toFixed(1)}%</TableCell>
                      <TableCell>{(item.semantic_score ? item.semantic_score * 100 : 0).toFixed(1)}%</TableCell>
                      <TableCell>
                        <Chip label={item.detection_method} size="small" variant="outlined" />
                      </TableCell>
                      <TableCell>
                        {item.status === 'FLAGGED' && <Chip label="FLAGGED FOR REVIEW" color="error" size="small" />}
                        {item.status === 'REVIEWED' && <Chip label="REVIEWED" color="success" size="small" />}
                        {item.status === 'DISMISSED' && <Chip label="DISMISSED" color="default" size="small" />}
                      </TableCell>
                      <TableCell align="right">
                        <Box sx={{ display: 'flex', gap: 1, justifyContent: 'flex-end' }}>
                          <Button
                            size="small"
                            variant="outlined"
                            color="success"
                            onClick={() => handleOpenReview(item, 'REVIEWED')}
                          >
                            Review
                          </Button>
                          <Button
                            size="small"
                            variant="outlined"
                            color="inherit"
                            onClick={() => handleOpenReview(item, 'DISMISSED')}
                          >
                            Dismiss
                          </Button>
                        </Box>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </Paper>
      )}

      {/* Review Dialog */}
      <Dialog open={reviewModalOpen} onClose={() => setReviewModalOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle sx={{ fontWeight: 700 }}>
          {reviewAction === 'REVIEWED' ? 'Confirm Plagiarism Case Review' : 'Dismiss Similarity Flag'}
        </DialogTitle>
        <DialogContent dividers>
          <Typography variant="body2" sx={{ color: '#475569', mb: 2 }}>
            Record your faculty review decision and explanatory notes for this similarity record.
          </Typography>

          <TextField
            fullWidth
            multiline
            rows={4}
            label="Faculty Review Notes *"
            placeholder="Document academic rationale for confirming or dismissing this similarity flag..."
            value={reviewNotes}
            onChange={(e) => setReviewNotes(e.target.value)}
          />
        </DialogContent>
        <DialogActions sx={{ p: 2 }}>
          <Button onClick={() => setReviewModalOpen(false)} disabled={submittingReview}>
            Cancel
          </Button>
          <Button
            variant="contained"
            color={reviewAction === 'REVIEWED' ? 'success' : 'primary'}
            onClick={handleSubmitReview}
            disabled={submittingReview || reviewNotes.trim().length < 3}
          >
            {submittingReview ? 'Submitting...' : 'Submit Decision'}
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};
