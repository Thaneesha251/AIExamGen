import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Container,
  Typography,
  Paper,
  Grid,
  Card,
  CardContent,
  Button,
  Chip,
  LinearProgress,
  Divider,
  Alert,
  CircularProgress,
  Stack,
  Table,
  TableHead,
  TableBody,
  TableRow,
  TableCell,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Tooltip
} from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';
import RefreshIcon from '@mui/icons-material/Refresh';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import LockIcon from '@mui/icons-material/Lock';
import EditIcon from '@mui/icons-material/Edit';
import HistoryIcon from '@mui/icons-material/History';
import ThumbUpIcon from '@mui/icons-material/ThumbUp';
import DoneAllIcon from '@mui/icons-material/DoneAll';
import LockOpenIcon from '@mui/icons-material/LockOpen';

import { Evaluation, EvaluationItem, FacultyReviewRecord } from '../../types/evaluation';
import { AnswerPaper } from '../../types/answerPaper';
import {
  getEvaluationByPaperId,
  triggerAnswerPaperEvaluation,
  acceptItemAIMark,
  overrideItemMark,
  requestItemReevaluation,
  bulkAcceptHighConfidence,
  approveEvaluation,
  finalizeEvaluation,
  reopenEvaluation,
  getEvaluationReviews
} from '../../services/evaluationService';
import { getAnswerPaperDetails } from '../../services/answerPaperService';

export const FacultyEvaluationViewPage: React.FC = () => {
  const { paperId } = useParams<{ paperId: string }>();
  const navigate = useNavigate();

  const [paper, setPaper] = useState<AnswerPaper | null>(null);
  const [evaluation, setEvaluation] = useState<Evaluation | null>(null);
  const [reviewsHistory, setReviewsHistory] = useState<FacultyReviewRecord[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [actionLoading, setActionLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Override Modal state
  const [overrideItem, setOverrideItem] = useState<EvaluationItem | null>(null);
  const [overrideMarkInput, setOverrideMarkInput] = useState<number>(0);
  const [overrideReasonInput, setOverrideReasonInput] = useState<string>('');
  const [overrideCommentInput, setOverrideCommentInput] = useState<string>('');

  // Re-evaluation Request Modal state
  const [reevalItem, setReevalItem] = useState<EvaluationItem | null>(null);
  const [reevalReasonInput, setReevalReasonInput] = useState<string>('');

  // Finalization / Approval Modal states
  const [showApproveModal, setShowApproveModal] = useState<boolean>(false);
  const [showFinalizeModal, setShowFinalizeModal] = useState<boolean>(false);
  const [finalizationNotes, setFinalizationNotes] = useState<string>('');

  // Reopen Modal state (Admin)
  const [showReopenModal, setShowReopenModal] = useState<boolean>(false);
  const [reopenReasonInput, setReopenReasonInput] = useState<string>('');

  // History Drawer/Modal
  const [showHistoryModal, setShowHistoryModal] = useState<boolean>(false);

  const currentUser = JSON.parse(localStorage.getItem('user') || '{}');
  const isAdmin = currentUser?.role?.name === 'ADMIN' || currentUser?.role === 'ADMIN';

  const fetchPaperAndEvaluation = async () => {
    if (!paperId) return;
    setLoading(true);
    setError(null);
    try {
      const paperData = await getAnswerPaperDetails(paperId);
      setPaper(paperData);

      try {
        const evalData = await getEvaluationByPaperId(paperId);
        setEvaluation(evalData);
        fetchHistory(evalData.id);
      } catch (err: any) {
        if (err.status === 404) {
          setEvaluation(null);
        } else {
          setError(err.message || 'Failed to fetch evaluation');
        }
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load answer paper');
    } finally {
      setLoading(false);
    }
  };

  const fetchHistory = async (evalId: string) => {
    try {
      const revs = await getEvaluationReviews(evalId);
      setReviewsHistory(revs);
    } catch (e) {
      // Ignore history fetch error if missing
    }
  };

  useEffect(() => {
    fetchPaperAndEvaluation();
  }, [paperId]);

  const handleRunEvaluation = async () => {
    if (!paperId) return;
    setActionLoading(true);
    setError(null);
    try {
      const result = await triggerAnswerPaperEvaluation(paperId);
      setEvaluation(result);
      setSuccessMsg('AI Evaluation pipeline completed successfully.');
      fetchHistory(result.id);
    } catch (err: any) {
      setError(err.message || 'Evaluation run failed');
    } finally {
      setActionLoading(false);
    }
  };

  const handleAcceptAI = async (item: EvaluationItem) => {
    if (!evaluation) return;
    setActionLoading(true);
    setError(null);
    try {
      const updatedItem = await acceptItemAIMark(evaluation.id, item.id, { comment: 'Accepted AI mark' });
      setEvaluation((prev) => {
        if (!prev) return prev;
        const updatedItems = prev.items.map((it) => (it.id === item.id ? updatedItem : it));
        const totalFinal = updatedItems.reduce((sum, curr) => sum + (curr.final_marks ?? curr.ai_marks ?? 0), 0);
        return {
          ...prev,
          status: prev.status === 'COMPLETED' ? 'UNDER_REVIEW' : prev.status,
          total_final_marks: totalFinal,
          items: updatedItems,
        };
      });
      setSuccessMsg(`Question ${item.question_number} AI mark accepted.`);
      fetchHistory(evaluation.id);
    } catch (err: any) {
      setError(err.message || 'Failed to accept AI mark');
    } finally {
      setActionLoading(false);
    }
  };

  const handleOpenOverrideModal = (item: EvaluationItem) => {
    setOverrideItem(item);
    setOverrideMarkInput(item.final_marks ?? item.ai_marks ?? 0);
    setOverrideReasonInput(item.override_reason || '');
    setOverrideCommentInput(item.faculty_comment || '');
  };

  const handleSaveOverride = async () => {
    if (!evaluation || !overrideItem) return;
    if (overrideReasonInput.trim().length < 10) {
      setError('Override reason is mandatory and must be at least 10 characters long.');
      return;
    }
    setActionLoading(true);
    setError(null);
    try {
      const updatedItem = await overrideItemMark(evaluation.id, overrideItem.id, {
        final_marks: Number(overrideMarkInput),
        reason: overrideReasonInput.trim(),
        comment: overrideCommentInput.trim() || undefined
      });

      setEvaluation((prev) => {
        if (!prev) return prev;
        const updatedItems = prev.items.map((it) => (it.id === overrideItem.id ? updatedItem : it));
        const totalFinal = updatedItems.reduce((sum, curr) => sum + (curr.final_marks ?? curr.ai_marks ?? 0), 0);
        return {
          ...prev,
          status: prev.status === 'COMPLETED' ? 'UNDER_REVIEW' : prev.status,
          total_final_marks: totalFinal,
          items: updatedItems,
        };
      });

      setSuccessMsg(`Question ${overrideItem.question_number} mark overridden to ${overrideMarkInput}.`);
      setOverrideItem(null);
      fetchHistory(evaluation.id);
    } catch (err: any) {
      setError(err.message || 'Failed to save mark override');
    } finally {
      setActionLoading(false);
    }
  };

  const handleOpenReevalModal = (item: EvaluationItem) => {
    setReevalItem(item);
    setReevalReasonInput('');
  };

  const handleConfirmReeval = async () => {
    if (!evaluation || !reevalItem) return;
    setActionLoading(true);
    setError(null);
    try {
      const updatedItem = await requestItemReevaluation(evaluation.id, reevalItem.id, reevalReasonInput);
      setEvaluation((prev) => {
        if (!prev) return prev;
        const updatedItems = prev.items.map((it) => (it.id === reevalItem.id ? updatedItem : it));
        return { ...prev, items: updatedItems };
      });
      setSuccessMsg(`Re-evaluation requested for Question ${reevalItem.question_number}.`);
      setReevalItem(null);
      fetchHistory(evaluation.id);
    } catch (err: any) {
      setError(err.message || 'Failed to request re-evaluation');
    } finally {
      setActionLoading(false);
    }
  };

  const handleBulkAccept = async () => {
    if (!evaluation) return;
    setActionLoading(true);
    setError(null);
    try {
      const result = await bulkAcceptHighConfidence(evaluation.id, 0.65);
      setSuccessMsg(`Bulk accepted ${result.accepted_count} high-confidence AI marks (${result.skipped_count} skipped).`);
      const updatedEval = await getEvaluationByPaperId(paperId!);
      setEvaluation(updatedEval);
      fetchHistory(evaluation.id);
    } catch (err: any) {
      setError(err.message || 'Bulk accept failed');
    } finally {
      setActionLoading(false);
    }
  };

  const handleConfirmApprove = async () => {
    if (!evaluation) return;
    setActionLoading(true);
    setError(null);
    try {
      const updated = await approveEvaluation(evaluation.id, { notes: finalizationNotes });
      setEvaluation(updated);
      setSuccessMsg('Evaluation successfully APPROVED by faculty.');
      setShowApproveModal(false);
      fetchHistory(evaluation.id);
    } catch (err: any) {
      setError(err.message || 'Failed to approve evaluation');
    } finally {
      setActionLoading(false);
    }
  };

  const handleConfirmFinalize = async () => {
    if (!evaluation) return;
    setActionLoading(true);
    setError(null);
    try {
      const updated = await finalizeEvaluation(evaluation.id, { notes: finalizationNotes });
      setEvaluation(updated);
      setSuccessMsg('Evaluation FINALIZED. Results locked.');
      setShowFinalizeModal(false);
      fetchHistory(evaluation.id);
    } catch (err: any) {
      setError(err.message || 'Failed to finalize evaluation');
    } finally {
      setActionLoading(false);
    }
  };

  const handleConfirmReopen = async () => {
    if (!evaluation) return;
    if (reopenReasonInput.trim().length < 10) {
      setError('Reopening reason is mandatory and must be at least 10 characters long.');
      return;
    }
    setActionLoading(true);
    setError(null);
    try {
      const updated = await reopenEvaluation(evaluation.id, { reason: reopenReasonInput.trim() });
      setEvaluation(updated);
      setSuccessMsg('Evaluation REOPENED by Admin for edits.');
      setShowReopenModal(false);
      fetchHistory(evaluation.id);
    } catch (err: any) {
      setError(err.message || 'Failed to reopen evaluation');
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress color="primary" size={50} />
      </Box>
    );
  }

  const isFinalized = evaluation?.status === 'FINALIZED';
  const reviewedItemsCount = evaluation?.items?.filter((it) => it.review_status && it.review_status !== 'PENDING').length || 0;
  const totalItemsCount = evaluation?.items?.length || 0;
  const isReviewComplete = totalItemsCount > 0 && reviewedItemsCount === totalItemsCount;
  const eligibleBulkCount = evaluation?.items?.filter((it) => (it.confidence || 0) >= 0.65 && !it.requires_faculty_review && (!it.review_status || it.review_status === 'PENDING')).length || 0;

  const getStatusChipColor = (st: string) => {
    switch (st) {
      case 'FINALIZED': return 'success';
      case 'APPROVED': return 'info';
      case 'UNDER_REVIEW': return 'warning';
      case 'REOPENED': return 'secondary';
      default: return 'default';
    }
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {/* Top Action Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3} flexWrap="wrap" gap={2}>
        <Button
          startIcon={<ArrowBackIcon />}
          onClick={() => navigate('/faculty/answer-papers')}
          variant="outlined"
          sx={{ borderRadius: 2 }}
        >
          Back to Answer Papers
        </Button>

        {evaluation && (
          <Stack direction="row" spacing={1.5} flexWrap="wrap">
            <Button
              startIcon={<HistoryIcon />}
              onClick={() => setShowHistoryModal(true)}
              variant="outlined"
              color="secondary"
              sx={{ borderRadius: 2 }}
            >
              Review History ({reviewsHistory.length})
            </Button>

            {!isFinalized && eligibleBulkCount > 0 && (
              <Button
                startIcon={<DoneAllIcon />}
                onClick={handleBulkAccept}
                disabled={actionLoading}
                variant="outlined"
                color="success"
                sx={{ borderRadius: 2 }}
              >
                Bulk Accept High-Confidence ({eligibleBulkCount})
              </Button>
            )}

            {!isFinalized && (
              <>
                <Button
                  startIcon={<ThumbUpIcon />}
                  onClick={() => setShowApproveModal(true)}
                  disabled={actionLoading || !isReviewComplete || evaluation.status === 'APPROVED'}
                  variant="contained"
                  color="info"
                  sx={{ borderRadius: 2 }}
                >
                  Approve Evaluation
                </Button>

                <Button
                  startIcon={<LockIcon />}
                  onClick={() => setShowFinalizeModal(true)}
                  disabled={actionLoading || !isReviewComplete}
                  variant="contained"
                  color="success"
                  sx={{ borderRadius: 2, background: 'linear-gradient(135deg, #10B981 0%, #059669 100%)' }}
                >
                  Finalize Evaluation
                </Button>
              </>
            )}

            {isFinalized && isAdmin && (
              <Button
                startIcon={<LockOpenIcon />}
                onClick={() => setShowReopenModal(true)}
                variant="contained"
                color="secondary"
                sx={{ borderRadius: 2 }}
              >
                Reopen Evaluation (Admin)
              </Button>
            )}
          </Stack>
        )}
      </Box>

      {error && <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>{error}</Alert>}
      {successMsg && <Alert severity="success" sx={{ mb: 3 }} onClose={() => setSuccessMsg(null)}>{successMsg}</Alert>}

      {/* Answer Paper & Status Header */}
      <Paper elevation={0} sx={{ p: 3, mb: 3, borderRadius: 3, border: '1px solid #E2E8F0', backgroundColor: '#FFFFFF' }}>
        <Box display="flex" justifyContent="space-between" alignItems="center" flexWrap="wrap" gap={2}>
          <Box>
            <Typography variant="h5" fontWeight={700} gutterBottom>
              Evaluation & Human-in-the-Loop Review: Paper #{paperId?.slice(0, 8)}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Student ID: {paper?.student_id || 'N/A'} | Exam: {paper?.examination_id?.slice(0, 8)} | Uploaded:{' '}
              {paper?.uploaded_at ? new Date(paper.uploaded_at).toLocaleString() : 'N/A'}
            </Typography>
          </Box>

          {evaluation && (
            <Box display="flex" alignItems="center" gap={1.5}>
              <Chip
                label={`Status: ${evaluation.status}`}
                color={getStatusChipColor(evaluation.status)}
                sx={{ fontWeight: 700, fontSize: '0.9rem', py: 2, px: 1 }}
              />
              <Chip label={`Version v${evaluation.version}`} variant="outlined" />
            </Box>
          )}
        </Box>
      </Paper>

      {/* Lock Banner if Finalized */}
      {isFinalized && (
        <Alert severity="success" icon={<LockIcon />} sx={{ mb: 3, borderRadius: 2 }}>
          <Typography variant="subtitle2" fontWeight={700}>
            Evaluation Finalized & Locked
          </Typography>
          This evaluation has been finalized by faculty. Final student marks are locked. Administrative reopening is required to make further edits.
        </Alert>
      )}

      {/* Evaluation Content */}
      {!evaluation ? (
        <Paper elevation={0} sx={{ p: 6, textAlign: 'center', borderRadius: 4, border: '2px dashed #CBD5E1', backgroundColor: '#F8FAFC' }}>
          <AutoAwesomeIcon sx={{ fontSize: 60, color: '#6366F1', mb: 2 }} />
          <Typography variant="h5" fontWeight={700} gutterBottom>
            No AI Evaluation Run Yet
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ maxWidth: 500, mx: 'auto', mb: 4 }}>
            Run the multi-layer AI scoring pipeline to analyze student answers against model answers and rubrics.
          </Typography>
          <Button
            variant="contained"
            size="large"
            startIcon={actionLoading ? <CircularProgress size={24} color="inherit" /> : <AutoAwesomeIcon />}
            onClick={handleRunEvaluation}
            disabled={actionLoading}
            sx={{ px: 4, py: 1.5, borderRadius: 3, background: 'linear-gradient(135deg, #6366F1 0%, #4F46E5 100%)' }}
          >
            {actionLoading ? 'Running AI Pipeline...' : 'Trigger AI Answer Evaluation'}
          </Button>
        </Paper>
      ) : (
        <>
          {/* Summary Metric Cards */}
          <Grid container spacing={3} sx={{ mb: 4 }}>
            <Grid item xs={12} sm={6} md={3}>
              <Card elevation={0} sx={{ borderRadius: 3, border: '1px solid #E2E8F0', backgroundColor: '#F8FAFC' }}>
                <CardContent>
                  <Typography variant="caption" color="text.secondary" fontWeight={600}>
                    AI SUGGESTED MARKS
                  </Typography>
                  <Typography variant="h4" fontWeight={800} color="text.secondary" sx={{ my: 0.5 }}>
                    {evaluation.total_ai_marks.toFixed(1)}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Raw AI Calculation
                  </Typography>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} sm={6} md={3}>
              <Card elevation={0} sx={{ borderRadius: 3, border: '1px solid #6366F1', backgroundColor: '#EEF2FF' }}>
                <CardContent>
                  <Typography variant="caption" color="primary.main" fontWeight={700}>
                    FINAL FACULTY MARKS
                  </Typography>
                  <Typography variant="h4" fontWeight={800} color="primary.main" sx={{ my: 0.5 }}>
                    {(evaluation.total_final_marks ?? evaluation.total_ai_marks).toFixed(1)}
                  </Typography>
                  <Typography variant="caption" color="primary.main" fontWeight={600}>
                    Official Mark Total
                  </Typography>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} sm={6} md={3}>
              <Card elevation={0} sx={{ borderRadius: 3, border: '1px solid #E2E8F0', backgroundColor: '#F8FAFC' }}>
                <CardContent>
                  <Typography variant="caption" color="text.secondary" fontWeight={600}>
                    REVIEW PROGRESS
                  </Typography>
                  <Typography variant="h5" fontWeight={800} sx={{ my: 0.5 }}>
                    {reviewedItemsCount} / {totalItemsCount} Reviewed
                  </Typography>
                  <LinearProgress
                    variant="determinate"
                    value={totalItemsCount > 0 ? (reviewedItemsCount / totalItemsCount) * 100 : 0}
                    sx={{ height: 6, borderRadius: 3, mt: 1 }}
                  />
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} sm={6} md={3}>
              <Card elevation={0} sx={{ borderRadius: 3, border: '1px solid #E2E8F0', backgroundColor: '#F8FAFC' }}>
                <CardContent>
                  <Typography variant="caption" color="text.secondary" fontWeight={600}>
                    CONFIDENCE SCORE
                  </Typography>
                  <Typography variant="h4" fontWeight={800} sx={{ my: 0.5 }}>
                    {(evaluation.overall_confidence * 100).toFixed(1)}%
                  </Typography>
                  <Chip
                    label={evaluation.overall_confidence >= 0.8 ? 'HIGH' : 'REVIEW NEEDED'}
                    color={evaluation.overall_confidence >= 0.8 ? 'success' : 'warning'}
                    size="small"
                    sx={{ fontWeight: 700 }}
                  />
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          {/* Question Items List */}
          <Typography variant="h6" fontWeight={700} sx={{ mb: 2 }}>
            Question Items Review ({evaluation.items.length})
          </Typography>

          <Stack spacing={3}>
            {evaluation.items.map((item: EvaluationItem) => (
              <Paper
                key={item.id}
                elevation={0}
                sx={{
                  p: 3,
                  borderRadius: 3,
                  border: item.review_status === 'OVERRIDDEN'
                    ? '2px solid #6366F1'
                    : item.review_status === 'ACCEPTED'
                    ? '1.5px solid #10B981'
                    : '1px solid #E2E8F0',
                  boxShadow: '0 4px 6px -1px rgba(0,0,0,0.05)'
                }}
              >
                {/* Item Header */}
                <Box display="flex" justifyContent="space-between" alignItems="center" flexWrap="wrap" gap={2} mb={2}>
                  <Box display="flex" alignItems="center" gap={1.5}>
                    <Typography variant="h6" fontWeight={700}>
                      Question {item.question_number}
                    </Typography>

                    <Chip
                      label={item.review_status || 'PENDING'}
                      color={
                        item.review_status === 'ACCEPTED'
                          ? 'success'
                          : item.review_status === 'OVERRIDDEN'
                          ? 'primary'
                          : item.review_status === 'RE_EVALUATED'
                          ? 'secondary'
                          : 'warning'
                      }
                      size="small"
                      sx={{ fontWeight: 700 }}
                    />

                    {item.requires_faculty_review && (
                      <Chip label="Flagged" color="error" size="small" variant="outlined" />
                    )}
                  </Box>

                  {/* Mark Display & Item Actions */}
                  <Box display="flex" alignItems="center" gap={2}>
                    <Box textAlign="right">
                      <Typography variant="caption" color="text.secondary" display="block">
                        AI Marks: {item.ai_marks?.toFixed(1)} / {item.maximum_marks}
                      </Typography>
                      <Typography variant="h6" fontWeight={800} color="primary.main">
                        Final Mark: {(item.final_marks ?? item.ai_marks ?? 0).toFixed(1)} / {item.maximum_marks}
                      </Typography>
                    </Box>

                    {!isFinalized && (
                      <Stack direction="row" spacing={1}>
                        <Button
                          size="small"
                          startIcon={<ThumbUpIcon />}
                          onClick={() => handleAcceptAI(item)}
                          disabled={actionLoading || item.review_status === 'ACCEPTED'}
                          variant={item.review_status === 'ACCEPTED' ? 'contained' : 'outlined'}
                          color="success"
                          sx={{ borderRadius: 2 }}
                        >
                          Accept AI
                        </Button>

                        <Button
                          size="small"
                          startIcon={<EditIcon />}
                          onClick={() => handleOpenOverrideModal(item)}
                          disabled={actionLoading}
                          variant={item.review_status === 'OVERRIDDEN' ? 'contained' : 'outlined'}
                          color="primary"
                          sx={{ borderRadius: 2 }}
                        >
                          Override
                        </Button>

                        <Button
                          size="small"
                          startIcon={<RefreshIcon />}
                          onClick={() => handleOpenReevalModal(item)}
                          disabled={actionLoading}
                          variant="outlined"
                          color="secondary"
                          sx={{ borderRadius: 2 }}
                        >
                          Re-Eval
                        </Button>
                      </Stack>
                    )}
                  </Box>
                </Box>

                {/* Faculty Override Banner if Overridden */}
                {item.review_status === 'OVERRIDDEN' && (
                  <Box p={2} mb={2} sx={{ backgroundColor: '#EEF2FF', borderRadius: 2, borderLeft: '4px solid #6366F1' }}>
                    <Typography variant="subtitle2" fontWeight={700} color="primary.main">
                      Faculty Override Recorded: {item.final_marks} / {item.maximum_marks}
                    </Typography>
                    <Typography variant="body2" color="text.primary" sx={{ mt: 0.5 }}>
                      <strong>Reason:</strong> {item.override_reason}
                    </Typography>
                    {item.faculty_comment && (
                      <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                        <strong>Comment:</strong> {item.faculty_comment}
                      </Typography>
                    )}
                  </Box>
                )}

                <Divider sx={{ my: 2 }} />

                {/* 6-Layer Scoring Component Breakdown */}
                <Typography variant="subtitle2" fontWeight={700} gutterBottom sx={{ color: '#334155' }}>
                  Multi-Layer Score Component Breakdown:
                </Typography>
                <Grid container spacing={2} sx={{ mb: 2 }}>
                  <Grid item xs={12} sm={4}>
                    <Typography variant="caption" color="text.secondary">
                      Keyword Score: {(item.keyword_score * 100).toFixed(0)}%
                    </Typography>
                    <LinearProgress variant="determinate" value={item.keyword_score * 100} sx={{ height: 6, borderRadius: 3, mt: 0.5 }} />
                  </Grid>

                  <Grid item xs={12} sm={4}>
                    <Typography variant="caption" color="text.secondary">
                      Concept Coverage: {(item.concept_score * 100).toFixed(0)}%
                    </Typography>
                    <LinearProgress variant="determinate" value={item.concept_score * 100} color="secondary" sx={{ height: 6, borderRadius: 3, mt: 0.5 }} />
                  </Grid>

                  <Grid item xs={12} sm={4}>
                    <Typography variant="caption" color="text.secondary">
                      Semantic Similarity: {(item.semantic_score * 100).toFixed(0)}%
                    </Typography>
                    <LinearProgress variant="determinate" value={item.semantic_score * 100} color="info" sx={{ height: 6, borderRadius: 3, mt: 0.5 }} />
                  </Grid>
                </Grid>

                {/* AI Explanation */}
                {item.evaluation_explanation && (
                  <Box p={2} sx={{ backgroundColor: '#F8FAFC', borderRadius: 2, borderLeft: '3px solid #CBD5E1', mt: 2 }}>
                    <Typography variant="caption" fontWeight={700} color="text.secondary" display="block">
                      AI EVALUATION REASONING:
                    </Typography>
                    <Typography variant="body2" color="text.primary" style={{ whiteSpace: 'pre-line' }}>
                      {item.evaluation_explanation}
                    </Typography>
                  </Box>
                )}
              </Paper>
            ))}
          </Stack>
        </>
      )}

      {/* Override Mark Modal */}
      <Dialog open={Boolean(overrideItem)} onClose={() => setOverrideItem(null)} maxWidth="sm" fullWidth>
        <DialogTitle sx={{ fontWeight: 700 }}>
          Manual Mark Override — Question {overrideItem?.question_number}
        </DialogTitle>
        <DialogContent dividers>
          <Typography variant="body2" color="text.secondary" mb={2}>
            AI Suggested Mark: {overrideItem?.ai_marks} / {overrideItem?.maximum_marks}
          </Typography>

          <TextField
            label="Revised Final Mark"
            type="number"
            fullWidth
            value={overrideMarkInput}
            onChange={(e) => setOverrideMarkInput(Number(e.target.value))}
            inputProps={{ min: 0, max: overrideItem?.maximum_marks, step: 0.5 }}
            sx={{ mb: 3 }}
          />

          <TextField
            label="Override Reason (Mandatory, min 10 chars)"
            multiline
            rows={3}
            fullWidth
            required
            value={overrideReasonInput}
            onChange={(e) => setOverrideReasonInput(e.target.value)}
            placeholder="e.g. Student provided valid alternative approach not present in model answer."
            error={overrideReasonInput.length > 0 && overrideReasonInput.length < 10}
            helperText={overrideReasonInput.length < 10 ? 'Minimum 10 characters required' : ''}
            sx={{ mb: 2 }}
          />

          <TextField
            label="Faculty Comment (Optional)"
            multiline
            rows={2}
            fullWidth
            value={overrideCommentInput}
            onChange={(e) => setOverrideCommentInput(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOverrideItem(null)}>Cancel</Button>
          <Button
            variant="contained"
            color="primary"
            onClick={handleSaveOverride}
            disabled={actionLoading || overrideReasonInput.trim().length < 10}
          >
            Save Mark Override
          </Button>
        </DialogActions>
      </Dialog>

      {/* Re-evaluation Request Modal */}
      <Dialog open={Boolean(reevalItem)} onClose={() => setReevalItem(null)} maxWidth="sm" fullWidth>
        <DialogTitle sx={{ fontWeight: 700 }}>
          Request AI Re-Evaluation — Question {reevalItem?.question_number}
        </DialogTitle>
        <DialogContent dividers>
          <Typography variant="body2" color="text.secondary" mb= {2}>
            Specify why this question should be re-evaluated by the AI pipeline.
          </Typography>
          <TextField
            label="Reason for Re-Evaluation"
            multiline
            rows={3}
            fullWidth
            value={reevalReasonInput}
            onChange={(e) => setReevalReasonInput(e.target.value)}
            placeholder="e.g. OCR text was corrected / Model answer updated."
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setReevalItem(null)}>Cancel</Button>
          <Button variant="contained" color="secondary" onClick={handleConfirmReeval} disabled={actionLoading}>
            Request Re-Evaluation
          </Button>
        </DialogActions>
      </Dialog>

      {/* Approve Evaluation Modal */}
      <Dialog open={showApproveModal} onClose={() => setShowApproveModal(false)} maxWidth="sm" fullWidth>
        <DialogTitle sx={{ fontWeight: 700 }}>Approve Evaluation?</DialogTitle>
        <DialogContent dividers>
          <Typography variant="body1" gutterBottom>
            You are approving the marks for Paper #{paperId?.slice(0, 8)}.
          </Typography>
          <Box p={2} sx={{ backgroundColor: '#F8FAFC', borderRadius: 2, my: 2 }}>
            <Typography variant="body2"><strong>Reviewed Items:</strong> {reviewedItemsCount} / {totalItemsCount}</Typography>
            <Typography variant="body2"><strong>Final Total Marks:</strong> {(evaluation?.total_final_marks ?? evaluation?.total_ai_marks)?.toFixed(1)}</Typography>
          </Box>
          <TextField
            label="Approval Notes (Optional)"
            multiline
            rows={2}
            fullWidth
            value={finalizationNotes}
            onChange={(e) => setFinalizationNotes(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowApproveModal(false)}>Cancel</Button>
          <Button variant="contained" color="info" onClick={handleConfirmApprove} disabled={actionLoading}>
            Approve Evaluation
          </Button>
        </DialogActions>
      </Dialog>

      {/* Finalize Evaluation Modal */}
      <Dialog open={showFinalizeModal} onClose={() => setShowFinalizeModal(false)} maxWidth="sm" fullWidth>
        <DialogTitle sx={{ fontWeight: 700, color: 'success.main' }}>
          Finalize & Lock Evaluation?
        </DialogTitle>
        <DialogContent dividers>
          <Alert severity="warning" sx={{ mb: 2 }}>
            After finalization, marks are locked and cannot be edited by faculty.
          </Alert>
          <Typography variant="body2" gutterBottom>
            <strong>Final Student Total:</strong> {(evaluation?.total_final_marks ?? evaluation?.total_ai_marks)?.toFixed(1)} Marks
          </Typography>
          <TextField
            label="Finalization Notes (Optional)"
            multiline
            rows={2}
            fullWidth
            value={finalizationNotes}
            onChange={(e) => setFinalizationNotes(e.target.value)}
            sx={{ mt: 2 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowFinalizeModal(false)}>Cancel</Button>
          <Button variant="contained" color="success" onClick={handleConfirmFinalize} disabled={actionLoading}>
            Finalize & Lock Evaluation
          </Button>
        </DialogActions>
      </Dialog>

      {/* Admin Reopen Modal */}
      <Dialog open={showReopenModal} onClose={() => setShowReopenModal(false)} maxWidth="sm" fullWidth>
        <DialogTitle sx={{ fontWeight: 700, color: 'secondary.main' }}>
          Reopen Finalized Evaluation (Admin Only)
        </DialogTitle>
        <DialogContent dividers>
          <Typography variant="body2" color="text.secondary" mb={2}>
            Administrative reopening will unlock marks for further review and modification.
          </Typography>
          <TextField
            label="Reopening Reason (Mandatory, min 10 chars)"
            multiline
            rows={3}
            fullWidth
            required
            value={reopenReasonInput}
            onChange={(e) => setReopenReasonInput(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowReopenModal(false)}>Cancel</Button>
          <Button
            variant="contained"
            color="secondary"
            onClick={handleConfirmReopen}
            disabled={actionLoading || reopenReasonInput.trim().length < 10}
          >
            Confirm Reopen
          </Button>
        </DialogActions>
      </Dialog>

      {/* Review History Modal */}
      <Dialog open={showHistoryModal} onClose={() => setShowHistoryModal(false)} maxWidth="md" fullWidth>
        <DialogTitle sx={{ fontWeight: 700 }}>Faculty Review Audit History</DialogTitle>
        <DialogContent dividers>
          {reviewsHistory.length === 0 ? (
            <Typography variant="body2" color="text.secondary" align="center" py={3}>
              No faculty review history entries recorded yet.
            </Typography>
          ) : (
            <Table size="small">
              <TableHead sx={{ backgroundColor: '#F1F5F9' }}>
                <TableRow>
                  <TableCell sx={{ fontWeight: 700 }}>Timestamp</TableCell>
                  <TableCell sx={{ fontWeight: 700 }}>Action</TableCell>
                  <TableCell sx={{ fontWeight: 700 }}>Faculty ID</TableCell>
                  <TableCell sx={{ fontWeight: 700 }}>Original AI</TableCell>
                  <TableCell sx={{ fontWeight: 700 }}>Revised</TableCell>
                  <TableCell sx={{ fontWeight: 700 }}>Reason / Comment</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {reviewsHistory.map((rev) => (
                  <TableRow key={rev.id}>
                    <TableCell>{rev.reviewed_at ? new Date(rev.reviewed_at).toLocaleString() : 'N/A'}</TableCell>
                    <TableCell><Chip label={rev.action} size="small" variant="outlined" /></TableCell>
                    <TableCell>{rev.faculty_id?.slice(0, 8)}</TableCell>
                    <TableCell>{rev.original_ai_marks ?? '-'}</TableCell>
                    <TableCell sx={{ fontWeight: 700, color: 'primary.main' }}>{rev.revised_marks}</TableCell>
                    <TableCell>{rev.reason || rev.comment || '-'}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowHistoryModal(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default FacultyEvaluationViewPage;
