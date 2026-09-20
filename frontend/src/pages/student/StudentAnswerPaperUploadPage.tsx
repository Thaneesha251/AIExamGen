import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Button,
  LinearProgress,
  Alert,
  Chip,
  Paper,
  Divider,
  Grid,
  CircularProgress
} from '@mui/material';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import RefreshIcon from '@mui/icons-material/Refresh';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import { uploadAnswerPaper, getAnswerPaperStatus, getAnswerPaperDetails } from '../../services/answerPaperService';
import { AnswerPaper, AnswerPaperStatusResponse } from '../../types/answerPaper';

const MAX_FILE_SIZE_MB = 25;
const ALLOWED_EXTENSIONS = ['.pdf', '.jpg', '.jpeg', '.png'];

export const StudentAnswerPaperUploadPage: React.FC = () => {
  const { examId } = useParams<{ examId: string }>();
  const navigate = useNavigate();

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [fileError, setFileError] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [activePaper, setActivePaper] = useState<AnswerPaper | null>(null);
  const [paperStatus, setPaperStatus] = useState<AnswerPaperStatusResponse | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Poll processing status if paper is currently PROCESSING or UPLOADED
  useEffect(() => {
    let intervalId: any = null;

    if (activePaper && (activePaper.status === 'PROCESSING' || activePaper.status === 'UPLOADED')) {
      intervalId = setInterval(async () => {
        try {
          const statusRes = await getAnswerPaperStatus(activePaper.id);
          setPaperStatus(statusRes);
          if (statusRes.status === 'EVALUATION_PENDING' || statusRes.status === 'OCR_COMPLETED' || statusRes.status === 'ERROR') {
            const updatedPaper = await getAnswerPaperDetails(activePaper.id);
            setActivePaper(updatedPaper);
            clearInterval(intervalId);
          }
        } catch (err) {
          console.error('Failed to poll answer paper status', err);
        }
      }, 3000);
    }

    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [activePaper]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFileError(null);
    setErrorMsg(null);
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      const ext = '.' + file.name.split('.').pop()?.toLowerCase();

      if (!ALLOWED_EXTENSIONS.includes(ext)) {
        setFileError(`Invalid file type. Only ${ALLOWED_EXTENSIONS.join(', ')} files are allowed.`);
        setSelectedFile(null);
        return;
      }

      if (file.size > MAX_FILE_SIZE_MB * 1024 * 1024) {
        setFileError(`File size exceeds maximum allowed limit of ${MAX_FILE_SIZE_MB}MB.`);
        setSelectedFile(null);
        return;
      }

      setSelectedFile(file);
    }
  };

  const handleUploadSubmit = async () => {
    if (!examId || !selectedFile) return;

    setIsUploading(true);
    setErrorMsg(null);
    setSuccessMsg(null);

    try {
      const uploaded = await uploadAnswerPaper(examId, selectedFile);
      setActivePaper(uploaded);
      setSuccessMsg('Answer paper uploaded successfully! Processing OCR and question segmentation in background...');
      setSelectedFile(null);

      const statusRes = await getAnswerPaperStatus(uploaded.id);
      setPaperStatus(statusRes);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to upload answer paper.');
    } finally {
      setIsUploading(false);
    }
  };

  const getStatusChipColor = (status?: string) => {
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
    <Box sx={{ p: 4, maxWidth: 900, mx: 'auto' }}>
      <Button
        startIcon={<ArrowBackIcon />}
        onClick={() => navigate('/student/dashboard')}
        sx={{ mb: 2 }}
      >
        Back to Dashboard
      </Button>

      <Typography variant="h4" fontWeight={700} gutterBottom sx={{ color: 'primary.main' }}>
        Student Answer Paper Upload
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
        Upload your completed answer sheet (PDF or Images). Once uploaded, the system will run OCR page extraction and segment your answers for faculty review.
      </Typography>

      {errorMsg && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {errorMsg}
        </Alert>
      )}

      {successMsg && (
        <Alert severity="success" sx={{ mb: 3 }}>
          {successMsg}
        </Alert>
      )}

      <Card sx={{ borderRadius: 3, boxShadow: 3, mb: 4 }}>
        <CardContent sx={{ p: 4 }}>
          <Typography variant="h6" fontWeight={600} gutterBottom>
            Select Answer Paper File
          </Typography>

          <Box
            sx={{
              border: '2px dashed',
              borderColor: fileError ? 'error.main' : 'primary.light',
              borderRadius: 3,
              p: 4,
              textAlign: 'center',
              backgroundColor: 'background.default',
              cursor: 'pointer',
              transition: 'border-color 0.2s',
              '&:hover': { borderColor: 'primary.main' }
            }}
            component="label"
          >
            <input
              type="file"
              hidden
              accept=".pdf,.jpg,.jpeg,.png"
              onChange={handleFileChange}
            />
            <CloudUploadIcon sx={{ fontSize: 48, color: 'primary.main', mb: 1 }} />
            <Typography variant="subtitle1" fontWeight={600}>
              {selectedFile ? selectedFile.name : 'Click or Drag file to select'}
            </Typography>
            <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 1 }}>
              Supported Formats: PDF, JPG, JPEG, PNG | Maximum Size: {MAX_FILE_SIZE_MB}MB
            </Typography>
          </Box>

          {fileError && (
            <Alert severity="error" sx={{ mt: 2 }}>
              {fileError}
            </Alert>
          )}

          <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
            <Button
              variant="contained"
              size="large"
              disabled={!selectedFile || isUploading}
              onClick={handleUploadSubmit}
              startIcon={isUploading ? <CircularProgress size={20} color="inherit" /> : <CloudUploadIcon />}
            >
              {isUploading ? 'Uploading File...' : 'Upload Answer Paper'}
            </Button>
          </Box>
        </CardContent>
      </Card>

      {/* Submission Status Section */}
      {activePaper && (
        <Card sx={{ borderRadius: 3, boxShadow: 2 }}>
          <CardContent sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6" fontWeight={600}>
                Submission & Processing Status
              </Typography>
              <Chip
                label={paperStatus?.status || activePaper.status}
                color={getStatusChipColor(paperStatus?.status || activePaper.status)}
                variant="filled"
                sx={{ fontWeight: 600 }}
              />
            </Box>

            <Divider sx={{ my: 2 }} />

            <Grid container spacing={2} sx={{ mb: 2 }}>
              <Grid item xs={6} sm={3}>
                <Typography variant="caption" color="text.secondary">Total Pages</Typography>
                <Typography variant="h6">{paperStatus?.total_pages || activePaper.pages.length}</Typography>
              </Grid>
              <Grid item xs={6} sm={3}>
                <Typography variant="caption" color="text.secondary">Processed Pages</Typography>
                <Typography variant="h6">{paperStatus?.processed_pages || 0}</Typography>
              </Grid>
              <Grid item xs={6} sm={3}>
                <Typography variant="caption" color="text.secondary">Extracted Answers</Typography>
                <Typography variant="h6">{paperStatus?.segmented_answers || activePaper.extracted_answers.length}</Typography>
              </Grid>
              <Grid item xs={6} sm={3}>
                <Typography variant="caption" color="text.secondary">Submission #</Typography>
                <Typography variant="h6">{activePaper.submission_number}</Typography>
              </Grid>
            </Grid>

            {paperStatus && paperStatus.progress_percent < 100 && (
              <Box sx={{ width: '100%', mt: 2 }}>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                  OCR & Answer Segmentation Progress: {paperStatus.progress_percent}%
                </Typography>
                <LinearProgress variant="determinate" value={paperStatus.progress_percent} sx={{ height: 8, borderRadius: 2 }} />
              </Box>
            )}

            {paperStatus?.status === 'EVALUATION_PENDING' && (
              <Alert severity="success" icon={<CheckCircleIcon />} sx={{ mt: 2 }}>
                Answer paper successfully ingested and segmented! Ready for evaluation phase.
              </Alert>
            )}
          </CardContent>
        </Card>
      )}
    </Box>
  );
};
