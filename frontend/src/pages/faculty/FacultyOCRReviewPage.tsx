import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  Button,
  Chip,
  TextField,
  Divider,
  Paper,
  IconButton,
  Alert,
  Checkbox,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  CircularProgress
} from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import SaveIcon from '@mui/icons-material/Save';
import MergeTypeIcon from '@mui/icons-material/MergeType';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import WarningIcon from '@mui/icons-material/Warning';
import RefreshIcon from '@mui/icons-material/Refresh';
import {
  getAnswerPaperDetails,
  correctOCRText,
  mapAnswerToQuestion,
  mergeAnswerSegments,
  completeOCRReview,
  retrySinglePageOCR
} from '../../services/answerPaperService';
import { AnswerPaper, ExtractedAnswer, AnswerPage } from '../../types/answerPaper';

export const FacultyOCRReviewPage: React.FC = () => {
  const { paperId } = useParams<{ paperId: string }>();
  const navigate = useNavigate();

  const [paper, setPaper] = useState<AnswerPaper | null>(null);
  const [selectedPageNum, setSelectedPageNum] = useState<number>(1);
  const [loading, setLoading] = useState<boolean>(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Edit state for text corrections
  const [editingText, setEditingText] = useState<{ [id: string]: string }>({});

  // Merge state
  const [selectedForMerge, setSelectedForMerge] = useState<string[]>([]);
  const [mergeDialogOpen, setMergeDialogOpen] = useState<boolean>(false);
  const [mergeQNum, setMergeQNum] = useState<string>('');

  useEffect(() => {
    if (paperId) loadPaperDetails(paperId);
  }, [paperId]);

  const loadPaperDetails = async (id: string) => {
    setLoading(true);
    try {
      const data = await getAnswerPaperDetails(id);
      setPaper(data);
      const textMap: { [id: string]: string } = {};
      data.extracted_answers.forEach((ans) => {
        textMap[ans.id] = ans.extracted_text;
      });
      setEditingText(textMap);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to load answer paper review data.');
    } finally {
      setLoading(false);
    }
  };

  const handleTextSave = async (ansId: string) => {
    if (!paperId || !editingText[ansId]) return;
    try {
      const updated = await correctOCRText(paperId, ansId, { extracted_text: editingText[ansId] });
      setSuccessMsg(`OCR text for Question ${updated.question_number} updated to HYBRID extraction.`);
      loadPaperDetails(paperId);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to update OCR text.');
    }
  };

  const handleMergeSubmit = async () => {
    if (!paperId || selectedForMerge.length < 2 || !mergeQNum) return;
    try {
      await mergeAnswerSegments(paperId, {
        source_answer_ids: selectedForMerge,
        target_question_number: mergeQNum
      });
      setSuccessMsg(`Successfully merged ${selectedForMerge.length} answer segments into Question ${mergeQNum}.`);
      setSelectedForMerge([]);
      setMergeDialogOpen(false);
      setMergeQNum('');
      loadPaperDetails(paperId);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to merge segments.');
    }
  };

  const handleCompleteReview = async () => {
    if (!paperId) return;
    try {
      await completeOCRReview(paperId);
      setSuccessMsg('OCR Review marked COMPLETE! Status set to EVALUATION_PENDING.');
      loadPaperDetails(paperId);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to complete review.');
    }
  };

  const handlePageRetry = async (pageId: string) => {
    if (!paperId) return;
    try {
      await retrySinglePageOCR(paperId, pageId);
      setSuccessMsg('Single page OCR retried successfully.');
      loadPaperDetails(paperId);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to retry page OCR.');
    }
  };

  const toggleMergeSelect = (id: string) => {
    setSelectedForMerge((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]
    );
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 6 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (!paper) {
    return (
      <Box sx={{ p: 4 }}>
        <Alert severity="error">Answer paper record not found.</Alert>
      </Box>
    );
  }

  const currentPage = paper.pages.find((p) => p.page_number === selectedPageNum) || paper.pages[0];

  return (
    <Box sx={{ p: 3, height: 'calc(100vh - 70px)', display: 'flex', flexDirection: 'column' }}>
      {/* Header bar */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Button startIcon={<ArrowBackIcon />} onClick={() => navigate('/faculty/answer-papers')}>
          Back to Papers
        </Button>
        <Typography variant="h5" fontWeight={700} color="primary.main">
          Faculty OCR & Answer Segmentation Review
        </Typography>
        <Box sx={{ display: 'flex', gap: 2 }}>
          {selectedForMerge.length >= 2 && (
            <Button
              variant="outlined"
              color="secondary"
              startIcon={<MergeTypeIcon />}
              onClick={() => setMergeDialogOpen(true)}
            >
              Merge {selectedForMerge.length} Selected Segments
            </Button>
          )}
          <Button
            variant="contained"
            color="success"
            startIcon={<CheckCircleIcon />}
            onClick={handleCompleteReview}
          >
            Mark Review Complete
          </Button>
        </Box>
      </Box>

      {errorMsg && <Alert severity="error" sx={{ mb: 2 }}>{errorMsg}</Alert>}
      {successMsg && <Alert severity="success" sx={{ mb: 2 }}>{successMsg}</Alert>}

      {/* Split Screen Grid */}
      <Grid container spacing={2} sx={{ flexGrow: 1, overflow: 'hidden' }}>
        {/* Left Side: Page Image / Viewer */}
        <Grid item xs={12} md={6} sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
          <Paper sx={{ p: 2, height: '100%', display: 'flex', flexDirection: 'column', borderRadius: 3 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6" fontWeight={600}>
                Page {selectedPageNum} of {paper.pages.length}
              </Typography>
              <Box sx={{ display: 'flex', gap: 1 }}>
                {paper.pages.map((p) => (
                  <Button
                    key={p.id}
                    size="small"
                    variant={p.page_number === selectedPageNum ? 'contained' : 'outlined'}
                    onClick={() => setSelectedPageNum(p.page_number)}
                  >
                    P{p.page_number}
                  </Button>
                ))}
              </Box>
            </Box>

            <Divider sx={{ mb: 2 }} />

            <Box
              sx={{
                flexGrow: 1,
                backgroundColor: 'grey.900',
                borderRadius: 2,
                p: 2,
                color: 'common.white',
                overflowY: 'auto',
                fontFamily: 'monospace'
              }}
            >
              <Typography variant="subtitle2" sx={{ opacity: 0.8, mb: 1 }}>
                [Page {selectedPageNum} Raw OCR Output]:
              </Typography>
              <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                {currentPage?.ocr_text || '[No OCR Text extracted for this page]'}
              </Typography>
            </Box>

            <Box sx={{ mt: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Chip
                label={`Provider: ${currentPage?.ocr_provider || 'MockOCR'} | Confidence: ${((currentPage?.ocr_confidence || 0.9) * 100).toFixed(0)}%`}
                color="info"
                variant="outlined"
                size="small"
              />
              <Button
                size="small"
                startIcon={<RefreshIcon />}
                onClick={() => currentPage && handlePageRetry(currentPage.id)}
              >
                Retry Page OCR
              </Button>
            </Box>
          </Paper>
        </Grid>

        {/* Right Side: Structured Extracted Answers & Review Controls */}
        <Grid item xs={12} md={6} sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
          <Paper sx={{ p: 2, height: '100%', overflowY: 'auto', borderRadius: 3 }}>
            <Typography variant="h6" fontWeight={600} gutterBottom>
              Extracted Answer Segments ({paper.extracted_answers.length})
            </Typography>
            <Divider sx={{ mb: 2 }} />

            {paper.extracted_answers.map((ans) => {
              const isLowConfidence = (ans.ocr_confidence || 0.9) < 0.70;
              return (
                <Card
                  key={ans.id}
                  variant="outlined"
                  sx={{
                    mb: 2,
                    borderRadius: 2,
                    borderColor: isLowConfidence ? 'warning.main' : 'divider',
                    backgroundColor: selectedForMerge.includes(ans.id) ? 'action.selected' : 'background.paper'
                  }}
                >
                  <CardContent sx={{ p: 2 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Checkbox
                          checked={selectedForMerge.includes(ans.id)}
                          onChange={() => toggleMergeSelect(ans.id)}
                        />
                        <Typography variant="subtitle1" fontWeight={700} color="primary.main">
                          Question {ans.question_number}
                        </Typography>
                      </Box>
                      <Box sx={{ display: 'flex', gap: 1 }}>
                        <Chip
                          label={`${((ans.ocr_confidence || 0.9) * 100).toFixed(0)}% OCR Conf`}
                          color={isLowConfidence ? 'warning' : 'success'}
                          size="small"
                        />
                        <Chip
                          label={ans.extraction_method}
                          color={ans.extraction_method === 'HYBRID' ? 'secondary' : 'default'}
                          size="small"
                        />
                      </Box>
                    </Box>

                    {isLowConfidence && (
                      <Alert severity="warning" icon={<WarningIcon />} sx={{ py: 0, mb: 1 }}>
                        Low OCR Confidence — Faculty review recommended.
                      </Alert>
                    )}

                    <TextField
                      multiline
                      rows={3}
                      fullWidth
                      value={editingText[ans.id] || ''}
                      onChange={(e) => setEditingText({ ...editingText, [ans.id]: e.target.value })}
                      sx={{ mt: 1, mb: 1 }}
                    />

                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Typography variant="caption" color="text.secondary">
                        Pages: {ans.page_start}–{ans.page_end}
                      </Typography>
                      <Button
                        size="small"
                        startIcon={<SaveIcon />}
                        onClick={() => handleTextSave(ans.id)}
                      >
                        Save Correction
                      </Button>
                    </Box>
                  </CardContent>
                </Card>
              );
            })}
          </Paper>
        </Grid>
      </Grid>

      {/* Merge Dialog */}
      <Dialog open={mergeDialogOpen} onClose={() => setMergeDialogOpen(false)}>
        <DialogTitle>Merge Selected Answer Segments</DialogTitle>
        <DialogContent>
          <Typography variant="body2" sx={{ mb: 2 }}>
            You have selected {selectedForMerge.length} segments to merge into a single question answer.
          </Typography>
          <TextField
            label="Target Question Number (e.g. Q2)"
            fullWidth
            value={mergeQNum}
            onChange={(e) => setMergeQNum(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setMergeDialogOpen(false)}>Cancel</Button>
          <Button variant="contained" color="secondary" onClick={handleMergeSubmit} disabled={!mergeQNum}>
            Confirm Merge
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};
