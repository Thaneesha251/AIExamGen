import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  Grid,
  Button,
  TextField,
  MenuItem,
  Chip,
  Card,
  CardContent,
  Alert,
  CircularProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Divider,
} from '@mui/material';
import {
  AutoAwesome as AIIcon,
  CheckCircle as ApproveIcon,
  Cancel as RejectIcon,
  Visibility as ViewIcon,
  Warning as WarningIcon,
} from '@mui/icons-material';
import { QuestionType, DifficultyLevel, BloomLevel, QuestionGenerationRun, Question } from '../../types/question';
import { academicService, Subject, Unit, Topic, LearningOutcome } from '../../services/academicService';
import { questionService } from '../../services/questionService';
import { QuestionReviewModal } from './QuestionReviewModal';

export const QuestionGenerationPage: React.FC = () => {
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [units, setUnits] = useState<Unit[]>([]);
  const [topics, setTopics] = useState<Topic[]>([]);
  const [learningOutcomes, setLearningOutcomes] = useState<LearningOutcome[]>([]);

  // Selection parameters
  const [subjectId, setSubjectId] = useState('');
  const [unitId, setUnitId] = useState('');
  const [topicId, setTopicId] = useState('');
  const [loId, setLoId] = useState('');

  const [questionType, setQuestionType] = useState<QuestionType>('SHORT_ANSWER');
  const [difficulty, setDifficulty] = useState<DifficultyLevel>('MEDIUM');
  const [bloomLevel, setBloomLevel] = useState<BloomLevel>('UNDERSTAND');
  const [marks, setMarks] = useState<number>(5.0);
  const [count, setCount] = useState<number>(3);

  // Run execution state
  const [generating, setGenerating] = useState(false);
  const [generationRun, setGenerationRun] = useState<QuestionGenerationRun | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Review Modal State
  const [reviewQuestion, setReviewQuestion] = useState<Question | null>(null);
  const [reviewModalOpen, setReviewModalOpen] = useState(false);

  useEffect(() => {
    loadSubjects();
  }, []);

  useEffect(() => {
    if (subjectId) {
      loadHierarchy(subjectId);
    }
  }, [subjectId]);

  const loadSubjects = async () => {
    try {
      const data = await academicService.getSubjects();
      setSubjects(data);
      if (data.length > 0) {
        setSubjectId(data[0].id);
      }
    } catch (err) {
      console.error('Failed to load subjects', err);
    }
  };

  const loadHierarchy = async (sId: string) => {
    try {
      const hierarchy = await academicService.getAcademicHierarchy(sId);
      setUnits(hierarchy.units || []);
      setLearningOutcomes(hierarchy.learning_outcomes || []);
      setUnitId('');
      setTopicId('');
      setLoId('');
    } catch (err) {
      console.error('Failed to load academic hierarchy', err);
    }
  };

  const handleUnitChange = (uId: string) => {
    setUnitId(uId);
    const u = units.find((item) => item.id === uId);
    setTopics(u?.topics || []);
    setTopicId('');
  };

  const handleGenerate = async () => {
    if (!subjectId) return;
    setGenerating(true);
    setError(null);
    try {
      const run = await questionService.generateQuestions({
        subject_id: subjectId,
        unit_id: unitId || undefined,
        topic_id: topicId || undefined,
        learning_outcome_id: loId || undefined,
        question_type: questionType,
        difficulty,
        bloom_level: bloomLevel,
        marks,
        count,
      });
      setGenerationRun(run);
    } catch (err: any) {
      setError(err.message || 'AI Question Generation failed');
    } finally {
      setGenerating(false);
    }
  };

  const handleApproveQuestion = async (qId: string) => {
    try {
      await questionService.updateQuestionStatus(qId, 'APPROVED');
      // Refresh run details
      if (generationRun) {
        const updatedRun = await questionService.getGenerationRun(generationRun.id);
        setGenerationRun(updatedRun);
      }
    } catch (err: any) {
      alert(err.message || 'Failed to approve question');
    }
  };

  return (
    <Box p={3}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <div>
          <Typography variant="h4" fontWeight="bold" display="flex" alignItems="center" gap={1}>
            <AIIcon color="primary" sx={{ fontSize: 32 }} /> AI Question Generation Engine
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Generate high-quality academic questions with automated quality checks and duplicate detection.
          </Typography>
        </div>
      </Box>

      <Grid container spacing={3}>
        {/* Left Column: Parameter Form */}
        <Grid item xs={12} md={5}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" fontWeight="bold" mb={2}>
              Generation Parameters
            </Typography>

            {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

            <Box display="flex" flexDirection="column" gap={2}>
              <TextField
                select
                label="Subject"
                fullWidth
                size="small"
                value={subjectId}
                onChange={(e) => setSubjectId(e.target.value)}
              >
                {subjects.map((s) => (
                  <MenuItem key={s.id} value={s.id}>
                    {s.code} — {s.name}
                  </MenuItem>
                ))}
              </TextField>

              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <TextField
                    select
                    label="Unit (Optional)"
                    fullWidth
                    size="small"
                    value={unitId}
                    onChange={(e) => handleUnitChange(e.target.value)}
                  >
                    <MenuItem value="">All Units</MenuItem>
                    {units.map((u) => (
                      <MenuItem key={u.id} value={u.id}>
                        Unit {u.unit_number}: {u.title}
                      </MenuItem>
                    ))}
                  </TextField>
                </Grid>

                <Grid item xs={6}>
                  <TextField
                    select
                    label="Topic (Optional)"
                    fullWidth
                    size="small"
                    value={topicId}
                    disabled={!unitId}
                    onChange={(e) => setTopicId(e.target.value)}
                  >
                    <MenuItem value="">All Topics</MenuItem>
                    {topics.map((t) => (
                      <MenuItem key={t.id} value={t.id}>
                        {t.name}
                      </MenuItem>
                    ))}
                  </TextField>
                </Grid>
              </Grid>

              <TextField
                select
                label="Learning Outcome (Optional)"
                fullWidth
                size="small"
                value={loId}
                onChange={(e) => setLoId(e.target.value)}
              >
                <MenuItem value="">All Outcomes</MenuItem>
                {learningOutcomes.map((lo) => (
                  <MenuItem key={lo.id} value={lo.id}>
                    {lo.code} — {lo.description}
                  </MenuItem>
                ))}
              </TextField>

              <Divider sx={{ my: 1 }} />

              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <TextField
                    select
                    label="Question Type"
                    fullWidth
                    size="small"
                    value={questionType}
                    onChange={(e) => setQuestionType(e.target.value as QuestionType)}
                  >
                    <MenuItem value="MCQ">MCQ</MenuItem>
                    <MenuItem value="SHORT_ANSWER">Short Answer</MenuItem>
                    <MenuItem value="LONG_ANSWER">Long Answer</MenuItem>
                    <MenuItem value="NUMERICAL">Numerical</MenuItem>
                    <MenuItem value="PROGRAMMING">Programming</MenuItem>
                  </TextField>
                </Grid>
                <Grid item xs={6}>
                  <TextField
                    select
                    label="Difficulty"
                    fullWidth
                    size="small"
                    value={difficulty}
                    onChange={(e) => setDifficulty(e.target.value as DifficultyLevel)}
                  >
                    <MenuItem value="EASY">EASY</MenuItem>
                    <MenuItem value="MEDIUM">MEDIUM</MenuItem>
                    <MenuItem value="HARD">HARD</MenuItem>
                  </TextField>
                </Grid>
                <Grid item xs={6}>
                  <TextField
                    select
                    label="Bloom Level"
                    fullWidth
                    size="small"
                    value={bloomLevel}
                    onChange={(e) => setBloomLevel(e.target.value as BloomLevel)}
                  >
                    <MenuItem value="REMEMBER">REMEMBER</MenuItem>
                    <MenuItem value="UNDERSTAND">UNDERSTAND</MenuItem>
                    <MenuItem value="APPLY">APPLY</MenuItem>
                    <MenuItem value="ANALYZE">ANALYZE</MenuItem>
                    <MenuItem value="EVALUATE">EVALUATE</MenuItem>
                    <MenuItem value="CREATE">CREATE</MenuItem>
                  </TextField>
                </Grid>
                <Grid item xs={3}>
                  <TextField
                    type="number"
                    label="Marks"
                    fullWidth
                    size="small"
                    value={marks}
                    onChange={(e) => setMarks(Number(e.target.value))}
                  />
                </Grid>
                <Grid item xs={3}>
                  <TextField
                    type="number"
                    label="Count"
                    fullWidth
                    size="small"
                    value={count}
                    onChange={(e) => setCount(Number(e.target.value))}
                  />
                </Grid>
              </Grid>

              <Button
                variant="contained"
                size="large"
                fullWidth
                startIcon={generating ? <CircularProgress size={20} color="inherit" /> : <AIIcon />}
                onClick={handleGenerate}
                disabled={generating || !subjectId}
                sx={{ mt: 2 }}
              >
                {generating ? 'Generating Questions...' : 'Generate Questions with AI'}
              </Button>
            </Box>
          </Paper>
        </Grid>

        {/* Right Column: Generation Run Output */}
        <Grid item xs={12} md={7}>
          {generationRun ? (
            <Paper sx={{ p: 3 }}>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                <Typography variant="h6" fontWeight="bold">
                  Generation Run Results
                </Typography>
                <Chip label={`Status: ${generationRun.status}`} color="success" />
              </Box>

              <Grid container spacing={2} mb={3}>
                <Grid item xs={3}>
                  <Card variant="outlined">
                    <CardContent sx={{ p: 1.5, '&:last-child': { pb: 1.5 } }}>
                      <Typography variant="caption" color="text.secondary">Requested</Typography>
                      <Typography variant="h6">{generationRun.requested_count}</Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={3}>
                  <Card variant="outlined">
                    <CardContent sx={{ p: 1.5, '&:last-child': { pb: 1.5 } }}>
                      <Typography variant="caption" color="text.secondary">Generated</Typography>
                      <Typography variant="h6">{generationRun.generated_count}</Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={3}>
                  <Card variant="outlined">
                    <CardContent sx={{ p: 1.5, '&:last-child': { pb: 1.5 } }}>
                      <Typography variant="caption" color="text.secondary">Accepted</Typography>
                      <Typography variant="h6" color="success.main">{generationRun.accepted_count}</Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={3}>
                  <Card variant="outlined">
                    <CardContent sx={{ p: 1.5, '&:last-child': { pb: 1.5 } }}>
                      <Typography variant="caption" color="text.secondary">Flagged</Typography>
                      <Typography variant="h6" color="error.main">{generationRun.rejected_count}</Typography>
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>

              <Typography variant="subtitle2" mb={1}>
                Generated Questions for Faculty Review ({generationRun.questions?.length || 0})
              </Typography>

              <TableContainer>
                <Table size="small">
                  <TableHead sx={{ background: '#f8f9fa' }}>
                    <TableRow>
                      <TableCell>Question</TableCell>
                      <TableCell>Type</TableCell>
                      <TableCell>Status</TableCell>
                      <TableCell>Validation</TableCell>
                      <TableCell align="right">Action</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {generationRun.questions?.map((q) => (
                      <TableRow key={q.id}>
                        <TableCell sx={{ maxWidth: 240 }}>
                          <Typography variant="body2" fontWeight="500" noWrap>
                            {q.question_text}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Chip label={q.question_type} size="small" variant="outlined" />
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={q.status}
                            size="small"
                            color={q.status === 'APPROVED' ? 'success' : 'warning'}
                          />
                        </TableCell>
                        <TableCell>
                          {q.validation_data ? (
                            <Chip
                              label={q.validation_data.is_valid ? 'Valid' : 'Flagged'}
                              size="small"
                              color={q.validation_data.is_valid ? 'success' : 'error'}
                              icon={!q.validation_data.is_valid ? <WarningIcon /> : undefined}
                            />
                          ) : (
                            'N/A'
                          )}
                        </TableCell>
                        <TableCell align="right">
                          <IconButton
                            size="small"
                            color="primary"
                            onClick={() => {
                              setReviewQuestion(q);
                              setReviewModalOpen(true);
                            }}
                          >
                            <ViewIcon fontSize="small" />
                          </IconButton>
                          {q.status !== 'APPROVED' && (
                            <IconButton
                              size="small"
                              color="success"
                              onClick={() => handleApproveQuestion(q.id)}
                            >
                              <ApproveIcon fontSize="small" />
                            </IconButton>
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Paper>
          ) : (
            <Paper sx={{ p: 5, textAlign: 'center', background: '#fafafa' }}>
              <AIIcon sx={{ fontSize: 48, color: 'text.disabled', mb: 2 }} />
              <Typography variant="h6" color="text.secondary">
                No Questions Generated Yet
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Configure parameters on the left and click "Generate Questions with AI" to start.
              </Typography>
            </Paper>
          )}
        </Grid>
      </Grid>

      <QuestionReviewModal
        open={reviewModalOpen}
        question={reviewQuestion}
        onClose={() => setReviewModalOpen(false)}
        onQuestionUpdated={async () => {
          if (generationRun) {
            const updatedRun = await questionService.getGenerationRun(generationRun.id);
            setGenerationRun(updatedRun);
          }
        }}
      />
    </Box>
  );
};
