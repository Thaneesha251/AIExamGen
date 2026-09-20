import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Box,
  Chip,
  Grid,
  Divider,
  TextField,
  Alert,
  List,
  ListItem,
  ListItemText,
  Tab,
  Tabs,
  CircularProgress,
} from '@mui/material';
import {
  CheckCircle as ApproveIcon,
  Cancel as RejectIcon,
  History as HistoryIcon,
  Warning as WarningIcon,
  Edit as EditIcon,
  Save as SaveIcon,
} from '@mui/icons-material';
import { Question, QuestionStatus, QuestionType, DifficultyLevel, BloomLevel } from '../../types/question';
import { questionService } from '../../services/questionService';

interface QuestionReviewModalProps {
  open: boolean;
  question: Question | null;
  onClose: () => void;
  onQuestionUpdated: () => void;
}

export const QuestionReviewModal: React.FC<QuestionReviewModalProps> = ({
  open,
  question,
  onClose,
  onQuestionUpdated,
}) => {
  const [activeTab, setActiveTab] = useState(0);
  const [isEditing, setIsEditing] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Edit State
  const [questionText, setQuestionText] = useState('');
  const [marks, setMarks] = useState<number>(5);
  const [expectedAnswer, setExpectedAnswer] = useState('');
  const [changeReason, setChangeReason] = useState('Faculty review edit');

  React.useEffect(() => {
    if (question) {
      setQuestionText(question.question_text);
      setMarks(question.marks);
      setExpectedAnswer(question.expected_answer || '');
      setIsEditing(false);
      setError(null);
    }
  }, [question]);

  if (!question) return null;

  const handleStatusChange = async (newStatus: QuestionStatus) => {
    setLoading(true);
    setError(null);
    try {
      await questionService.updateQuestionStatus(question.id, newStatus);
      onQuestionUpdated();
      onClose();
    } catch (err: any) {
      setError(err.message || 'Failed to update question status');
    } finally {
      setLoading(false);
    }
  };

  const handleSaveEdit = async () => {
    setLoading(true);
    setError(null);
    try {
      await questionService.updateQuestion(question.id, {
        question_text: questionText,
        marks,
        expected_answer: expectedAnswer,
        change_reason: changeReason,
      });
      setIsEditing(false);
      onQuestionUpdated();
    } catch (err: any) {
      setError(err.message || 'Failed to save question edits');
    } finally {
      setLoading(false);
    }
  };

  const valData = question.validation_data;

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Box display="flex" alignItems="center" gap={1}>
          <Typography variant="h6">Question Details & Review</Typography>
          <Chip label={`Version ${question.version}`} color="info" size="small" />
          <Chip
            label={question.status}
            color={
              question.status === 'APPROVED' || question.status === 'ACTIVE'
                ? 'success'
                : question.status === 'UNDER_REVIEW' || question.status === 'AI_GENERATED'
                ? 'warning'
                : 'error'
            }
            size="small"
          />
        </Box>
        <Box>
          {!isEditing ? (
            <Button startIcon={<EditIcon />} variant="outlined" size="small" onClick={() => setIsEditing(true)}>
              Edit
            </Button>
          ) : (
            <Button startIcon={<SaveIcon />} variant="contained" size="small" onClick={handleSaveEdit} disabled={loading}>
              Save Changes
            </Button>
          )}
        </Box>
      </DialogTitle>
      <Divider />

      <DialogContent>
        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

        <Tabs value={activeTab} onChange={(_, v) => setActiveTab(v)} sx={{ mb: 2 }}>
          <Tab label="Question Content" />
          <Tab label="AI Validation Metrics" />
          <Tab label={`Version History (${question.versions?.length || 1})`} icon={<HistoryIcon />} iconPosition="start" />
        </Tabs>

        {activeTab === 0 && (
          <Box display="flex" flexDirection="column" gap={2}>
            {/* Metadata Tags */}
            <Grid container spacing={2}>
              <Grid item xs={3}>
                <Typography variant="caption" color="text.secondary">Type</Typography>
                <Typography variant="body2" fontWeight="bold">{question.question_type}</Typography>
              </Grid>
              <Grid item xs={3}>
                <Typography variant="caption" color="text.secondary">Marks</Typography>
                {isEditing ? (
                  <TextField
                    type="number"
                    size="small"
                    value={marks}
                    onChange={(e) => setMarks(Number(e.target.value))}
                    fullWidth
                  />
                ) : (
                  <Typography variant="body2" fontWeight="bold">{question.marks}</Typography>
                )}
              </Grid>
              <Grid item xs={3}>
                <Typography variant="caption" color="text.secondary">Difficulty</Typography>
                <Typography variant="body2" fontWeight="bold">{question.difficulty}</Typography>
              </Grid>
              <Grid item xs={3}>
                <Typography variant="caption" color="text.secondary">Bloom Level</Typography>
                <Typography variant="body2" fontWeight="bold">{question.bloom_level}</Typography>
              </Grid>
            </Grid>

            <Divider />

            {/* Question Text */}
            <Typography variant="subtitle2" color="primary">Question Text</Typography>
            {isEditing ? (
              <TextField
                multiline
                rows={3}
                fullWidth
                value={questionText}
                onChange={(e) => setQuestionText(e.target.value)}
              />
            ) : (
              <Typography variant="body1" sx={{ background: '#f8f9fa', p: 2, borderRadius: 1 }}>
                {question.question_text}
              </Typography>
            )}

            {/* MCQ Options */}
            {question.question_type === 'MCQ' && question.options && (
              <Box>
                <Typography variant="subtitle2" color="primary" sx={{ mb: 1 }}>MCQ Options</Typography>
                <List dense sx={{ background: '#f1f3f5', borderRadius: 1 }}>
                  {question.options.options?.map((opt, i) => (
                    <ListItem key={i}>
                      <ListItemText
                        primary={opt}
                        primaryTypographyProps={{
                          fontWeight: opt === question.options?.correct_option ? 'bold' : 'normal',
                          color: opt === question.options?.correct_option ? 'success.main' : 'text.primary',
                        }}
                      />
                      {opt === question.options?.correct_option && (
                        <Chip label="Correct" color="success" size="small" />
                      )}
                    </ListItem>
                  ))}
                </List>
              </Box>
            )}

            {/* Expected Answer */}
            <Typography variant="subtitle2" color="primary">Expected / Model Answer</Typography>
            {isEditing ? (
              <TextField
                multiline
                rows={2}
                fullWidth
                value={expectedAnswer}
                onChange={(e) => setExpectedAnswer(e.target.value)}
              />
            ) : (
              <Typography variant="body2" sx={{ background: '#f8f9fa', p: 2, borderRadius: 1 }}>
                {question.expected_answer || 'No model answer provided.'}
              </Typography>
            )}

            {isEditing && (
              <TextField
                label="Edit Reason / Audit Note"
                size="small"
                fullWidth
                value={changeReason}
                onChange={(e) => setChangeReason(e.target.value)}
              />
            )}
          </Box>
        )}

        {activeTab === 1 && (
          <Box display="flex" flexDirection="column" gap={2}>
            {valData ? (
              <>
                <Grid container spacing={2}>
                  <Grid item xs={4}>
                    <Box textAlign="center" p={2} sx={{ background: valData.is_valid ? '#e6f4ea' : '#fce8e6', borderRadius: 1 }}>
                      <Typography variant="caption">Valid Status</Typography>
                      <Typography variant="h6" color={valData.is_valid ? 'success.main' : 'error.main'}>
                        {valData.is_valid ? 'PASSED' : 'FLAGGED'}
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={4}>
                    <Box textAlign="center" p={2} sx={{ background: '#f1f3f5', borderRadius: 1 }}>
                      <Typography variant="caption">Duplicate Score</Typography>
                      <Typography variant="h6" color={valData.duplicate_score > 0.5 ? 'error.main' : 'success.main'}>
                        {(valData.duplicate_score * 100).toFixed(1)}%
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={4}>
                    <Box textAlign="center" p={2} sx={{ background: '#f1f3f5', borderRadius: 1 }}>
                      <Typography variant="caption">Completeness</Typography>
                      <Typography variant="h6">
                        {(valData.completeness_score * 100).toFixed(0)}%
                      </Typography>
                    </Box>
                  </Grid>
                </Grid>

                {valData.warnings && valData.warnings.length > 0 && (
                  <Box>
                    <Typography variant="subtitle2" color="warning.main" display="flex" alignItems="center" gap={1}>
                      <WarningIcon /> Quality Warnings ({valData.warnings.length})
                    </Typography>
                    <List dense>
                      {valData.warnings.map((w, idx) => (
                        <ListItem key={idx}>
                          <ListItemText primary={`• ${w}`} />
                        </ListItem>
                      ))}
                    </List>
                  </Box>
                )}
              </>
            ) : (
              <Typography color="text.secondary">No validation metrics available for this question.</Typography>
            )}
          </Box>
        )}

        {activeTab === 2 && (
          <Box display="flex" flexDirection="column" gap={2}>
            {question.versions && question.versions.length > 0 ? (
              <List>
                {question.versions.map((ver) => (
                  <ListItem key={ver.id} divider>
                    <ListItemText
                      primary={`Version ${ver.version_number} — ${new Date(ver.created_at).toLocaleString()}`}
                      secondary={
                        <>
                          <Typography variant="body2" color="text.primary">{ver.question_text}</Typography>
                          <Typography variant="caption" color="text.secondary">Reason: {ver.change_reason || 'N/A'}</Typography>
                        </>
                      }
                    />
                  </ListItem>
                ))}
              </List>
            ) : (
              <Typography color="text.secondary">Initial Version 1</Typography>
            )}
          </Box>
        )}
      </DialogContent>

      <Divider />
      <DialogActions sx={{ p: 2, justifyContent: 'space-between' }}>
        <Button onClick={onClose}>Close</Button>
        <Box display="flex" gap={1}>
          <Button
            variant="outlined"
            color="error"
            startIcon={<RejectIcon />}
            onClick={() => handleStatusChange('REJECTED')}
            disabled={loading}
          >
            Reject
          </Button>
          <Button
            variant="contained"
            color="success"
            startIcon={<ApproveIcon />}
            onClick={() => handleStatusChange('APPROVED')}
            disabled={loading}
          >
            Approve Question
          </Button>
        </Box>
      </DialogActions>
    </Dialog>
  );
};
