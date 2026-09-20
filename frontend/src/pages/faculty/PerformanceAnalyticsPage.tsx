import React, { useState } from 'react';
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
  Alert,
  CircularProgress,
  Tabs,
  Tab,
  Card,
  CardContent,
  Slider
} from '@mui/material';
import {
  Analytics,
  TrendingUp,
  School,
  Assessment,
  Quiz,
  MenuBook,
  AssignmentTurnedIn,
  Psychology,
  Speed,
  Warning
} from '@mui/icons-material';
import { analyticsService } from '@/services/analyticsService';
import {
  ExamAnalyticsOverview,
  QuestionAnalytics,
  UnitAnalytics,
  TopicAnalytics,
  COAnalytics,
  BloomAnalytics,
  DifficultyAnalytics,
  WeakTopicResponse
} from '@/types/analytics';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div role="tabpanel" hidden={value !== index} {...other}>
      {value === index && <Box sx={{ pt: 3 }}>{children}</Box>}
    </div>
  );
}

export const PerformanceAnalyticsPage: React.FC = () => {
  const [examId, setExamId] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Tab state
  const [tabIndex, setTabIndex] = useState<number>(0);

  // Data states
  const [overview, setOverview] = useState<ExamAnalyticsOverview | null>(null);
  const [questions, setQuestions] = useState<QuestionAnalytics[]>([]);
  const [units, setUnits] = useState<UnitAnalytics[]>([]);
  const [topics, setTopics] = useState<TopicAnalytics[]>([]);
  const [cos, setCos] = useState<COAnalytics[]>([]);
  const [bloom, setBloom] = useState<BloomAnalytics[]>([]);
  const [difficulty, setDifficulty] = useState<DifficultyAnalytics[]>([]);
  const [weakTopics, setWeakTopics] = useState<WeakTopicResponse | null>(null);

  // Weak Topic Controls
  const [weakThreshold, setWeakThreshold] = useState<number>(50);
  const [minResponses, setMinResponses] = useState<number>(3);

  const fetchAnalytics = async (targetExamId: string) => {
    if (!targetExamId.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const [
        overviewRes,
        questionsRes,
        unitsRes,
        topicsRes,
        cosRes,
        bloomRes,
        difficultyRes,
        weakRes
      ] = await Promise.all([
        analyticsService.getExamOverview(targetExamId),
        analyticsService.getQuestionAnalytics(targetExamId),
        analyticsService.getUnitAnalytics(targetExamId),
        analyticsService.getTopicAnalytics(targetExamId),
        analyticsService.getCOAnalytics(targetExamId),
        analyticsService.getBloomAnalytics(targetExamId),
        analyticsService.getDifficultyAnalytics(targetExamId),
        analyticsService.getExamWeakTopics(targetExamId, weakThreshold, minResponses)
      ]);

      setOverview(overviewRes);
      setQuestions(questionsRes);
      setUnits(unitsRes);
      setTopics(topicsRes);
      setCos(cosRes);
      setBloom(bloomRes);
      setDifficulty(difficultyRes);
      setWeakTopics(weakRes);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch examination performance analytics');
    } finally {
      setLoading(false);
    }
  };

  const handleFetchWeakTopicsOnly = async () => {
    if (!examId.trim()) return;
    try {
      const data = await analyticsService.getExamWeakTopics(examId, weakThreshold, minResponses);
      setWeakTopics(data);
    } catch (err: any) {
      setError('Failed to update weak topics threshold');
    }
  };

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 6 }}>
      {/* Header Banner */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 800, color: '#1e293b', mb: 1, display: 'flex', alignItems: 'center', gap: 1.5 }}>
          <Analytics color="primary" fontSize="large" /> Student Performance & Weak Topic Analytics
        </Typography>
        <Typography variant="body1" sx={{ color: '#64748b' }}>
          Server-side aggregate analytics derived strictly from <strong>FINALIZED</strong> evaluations across questions, units, topics, learning outcomes, Bloom taxonomy, and difficulty levels.
        </Typography>
      </Box>

      {/* Examination Selector */}
      <Paper sx={{ p: 3, mb: 4, borderRadius: 3, border: '1px solid #e2e8f0' }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={8}>
            <TextField
              fullWidth
              label="Examination ID"
              placeholder="Enter Examination UUID..."
              value={examId}
              onChange={(e) => setExamId(e.target.value)}
              variant="outlined"
            />
          </Grid>
          <Grid item xs={12} md={4}>
            <Button
              fullWidth
              variant="contained"
              color="primary"
              size="large"
              startIcon={loading ? <CircularProgress size={20} color="inherit" /> : <TrendingUp />}
              onClick={() => fetchAnalytics(examId)}
              disabled={loading || !examId.trim()}
              sx={{ py: 1.5, borderRadius: 2, fontWeight: 700 }}
            >
              {loading ? 'Loading Analytics...' : 'Load Analytics'}
            </Button>
          </Grid>
        </Grid>

        {error && (
          <Alert severity="error" sx={{ mt: 2 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}
      </Paper>

      {/* Cohort Overview Metrics */}
      {overview && (
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ borderRadius: 3, bgcolor: '#f8fafc', border: '1px solid #e2e8f0' }}>
              <CardContent>
                <Typography variant="caption" sx={{ color: '#64748b', fontWeight: 700 }}>
                  EVALUATED STUDENTS
                </Typography>
                <Typography variant="h3" sx={{ fontWeight: 800, color: '#1e293b', mt: 1 }}>
                  {overview.finalized_evaluations}
                </Typography>
                <Typography variant="caption" sx={{ color: '#94a3b8' }}>
                  out of {overview.total_students} registered
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ borderRadius: 3, bgcolor: '#eff6ff', border: '1px solid #bfdbfe' }}>
              <CardContent>
                <Typography variant="caption" sx={{ color: '#1e40af', fontWeight: 700 }}>
                  AVERAGE SCORE
                </Typography>
                <Typography variant="h3" sx={{ fontWeight: 800, color: '#2563eb', mt: 1 }}>
                  {overview.average_percentage}%
                </Typography>
                <Typography variant="caption" sx={{ color: '#3b82f6' }}>
                  {overview.average_marks} / {overview.max_possible_marks} marks
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ borderRadius: 3, bgcolor: '#f0fdf4', border: '1px solid #bbf7d0' }}>
              <CardContent>
                <Typography variant="caption" sx={{ color: '#166534', fontWeight: 700 }}>
                  PASS PERCENTAGE
                </Typography>
                <Typography variant="h3" sx={{ fontWeight: 800, color: '#16a34a', mt: 1 }}>
                  {overview.pass_percentage}%
                </Typography>
                <Typography variant="caption" sx={{ color: '#22c55e' }}>
                  Highest: {overview.highest_marks} | Lowest: {overview.lowest_marks}
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ borderRadius: 3, bgcolor: '#fcf5ff', border: '1px solid #f0abfc' }}>
              <CardContent>
                <Typography variant="caption" sx={{ color: '#86198f', fontWeight: 700 }}>
                  MEDIAN SCORE
                </Typography>
                <Typography variant="h3" sx={{ fontWeight: 800, color: '#c026d3', mt: 1 }}>
                  {overview.median_marks}
                </Typography>
                <Typography variant="caption" sx={{ color: '#d946ef' }}>
                  cohort central tendency
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Dimensional Analytics Tabs */}
      {overview && (
        <Paper sx={{ borderRadius: 3, border: '1px solid #e2e8f0', p: 3 }}>
          <Tabs
            value={tabIndex}
            onChange={(_, val) => setTabIndex(val)}
            variant="scrollable"
            scrollButtons="auto"
            sx={{ borderBottom: 1, borderColor: 'divider' }}
          >
            <Tab icon={<Quiz />} iconPosition="start" label="Questions" />
            <Tab icon={<MenuBook />} iconPosition="start" label="Units" />
            <Tab icon={<School />} iconPosition="start" label="Topics" />
            <Tab icon={<AssignmentTurnedIn />} iconPosition="start" label="Learning Outcomes" />
            <Tab icon={<Psychology />} iconPosition="start" label="Bloom's Taxonomy" />
            <Tab icon={<Speed />} iconPosition="start" label="Difficulty Level" />
            <Tab icon={<Warning color="error" />} iconPosition="start" label="Weak Topics" />
          </Tabs>

          {/* Question Analytics Tab */}
          <TabPanel value={tabIndex} index={0}>
            <TableContainer>
              <Table>
                <TableHead sx={{ bgcolor: '#f8fafc' }}>
                  <TableRow>
                    <TableCell sx={{ fontWeight: 700 }}>Q#</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Question Text</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Type</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Bloom</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Difficulty</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Max Marks</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Avg Score</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Achieved %</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {questions.map((q) => (
                    <TableRow key={q.question_id} hover>
                      <TableCell sx={{ fontWeight: 700 }}>{q.question_number}</TableCell>
                      <TableCell sx={{ maxWidth: 300 }}>{q.question_text}</TableCell>
                      <TableCell><Chip label={q.question_type} size="small" variant="outlined" /></TableCell>
                      <TableCell>{q.bloom_level || 'N/A'}</TableCell>
                      <TableCell>{q.difficulty_level || 'N/A'}</TableCell>
                      <TableCell>{q.max_marks}</TableCell>
                      <TableCell>{q.average_marks}</TableCell>
                      <TableCell>
                        <Chip
                          label={`${q.percentage_achieved}%`}
                          color={q.percentage_achieved >= 60 ? 'success' : q.percentage_achieved >= 40 ? 'warning' : 'error'}
                          sx={{ fontWeight: 700 }}
                        />
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </TabPanel>

          {/* Unit Analytics Tab */}
          <TabPanel value={tabIndex} index={1}>
            <TableContainer>
              <Table>
                <TableHead sx={{ bgcolor: '#f8fafc' }}>
                  <TableRow>
                    <TableCell sx={{ fontWeight: 700 }}>Unit Name</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Questions</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Responses</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Average Score</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Percentage</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {units.map((u) => (
                    <TableRow key={u.id} hover>
                      <TableCell sx={{ fontWeight: 600 }}>{u.name}</TableCell>
                      <TableCell>{u.question_count}</TableCell>
                      <TableCell>{u.response_count}</TableCell>
                      <TableCell>{u.average_marks}</TableCell>
                      <TableCell>
                        <Chip
                          label={`${u.percentage}%`}
                          color={u.percentage >= 60 ? 'success' : u.percentage >= 40 ? 'warning' : 'error'}
                          sx={{ fontWeight: 700 }}
                        />
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </TabPanel>

          {/* Topic Analytics Tab */}
          <TabPanel value={tabIndex} index={2}>
            <TableContainer>
              <Table>
                <TableHead sx={{ bgcolor: '#f8fafc' }}>
                  <TableRow>
                    <TableCell sx={{ fontWeight: 700 }}>Topic Name</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Questions</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Responses</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Average Score</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Percentage</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {topics.map((t) => (
                    <TableRow key={t.id} hover>
                      <TableCell sx={{ fontWeight: 600 }}>{t.name}</TableCell>
                      <TableCell>{t.question_count}</TableCell>
                      <TableCell>{t.response_count}</TableCell>
                      <TableCell>{t.average_marks}</TableCell>
                      <TableCell>
                        <Chip
                          label={`${t.percentage}%`}
                          color={t.percentage >= 60 ? 'success' : t.percentage >= 40 ? 'warning' : 'error'}
                          sx={{ fontWeight: 700 }}
                        />
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </TabPanel>

          {/* CO Attainment Tab */}
          <TabPanel value={tabIndex} index={3}>
            <TableContainer>
              <Table>
                <TableHead sx={{ bgcolor: '#f8fafc' }}>
                  <TableRow>
                    <TableCell sx={{ fontWeight: 700 }}>Course Outcome (CO)</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Questions</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Responses</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Average Score</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Attainment %</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {cos.map((c) => (
                    <TableRow key={c.id} hover>
                      <TableCell sx={{ fontWeight: 600 }}>{c.name}</TableCell>
                      <TableCell>{c.question_count}</TableCell>
                      <TableCell>{c.response_count}</TableCell>
                      <TableCell>{c.average_marks}</TableCell>
                      <TableCell>
                        <Chip
                          label={`${c.percentage}%`}
                          color={c.percentage >= 60 ? 'success' : c.percentage >= 40 ? 'warning' : 'error'}
                          sx={{ fontWeight: 700 }}
                        />
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </TabPanel>

          {/* Bloom Taxonomy Tab */}
          <TabPanel value={tabIndex} index={4}>
            <TableContainer>
              <Table>
                <TableHead sx={{ bgcolor: '#f8fafc' }}>
                  <TableRow>
                    <TableCell sx={{ fontWeight: 700 }}>Bloom Level</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Questions</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Responses</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Average Score</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Percentage</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {bloom.map((b) => (
                    <TableRow key={b.id} hover>
                      <TableCell sx={{ fontWeight: 700 }}>{b.name}</TableCell>
                      <TableCell>{b.question_count}</TableCell>
                      <TableCell>{b.response_count}</TableCell>
                      <TableCell>{b.average_marks}</TableCell>
                      <TableCell>
                        <Chip
                          label={`${b.percentage}%`}
                          color={b.percentage >= 60 ? 'success' : b.percentage >= 40 ? 'warning' : 'error'}
                          sx={{ fontWeight: 700 }}
                        />
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </TabPanel>

          {/* Difficulty Tab */}
          <TabPanel value={tabIndex} index={5}>
            <TableContainer>
              <Table>
                <TableHead sx={{ bgcolor: '#f8fafc' }}>
                  <TableRow>
                    <TableCell sx={{ fontWeight: 700 }}>Difficulty Level</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Questions</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Responses</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Average Score</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Percentage</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {difficulty.map((d) => (
                    <TableRow key={d.id} hover>
                      <TableCell sx={{ fontWeight: 700 }}>{d.name}</TableCell>
                      <TableCell>{d.question_count}</TableCell>
                      <TableCell>{d.response_count}</TableCell>
                      <TableCell>{d.average_marks}</TableCell>
                      <TableCell>
                        <Chip
                          label={`${d.percentage}%`}
                          color={d.percentage >= 60 ? 'success' : d.percentage >= 40 ? 'warning' : 'error'}
                          sx={{ fontWeight: 700 }}
                        />
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </TabPanel>

          {/* Weak Topics Tab */}
          <TabPanel value={tabIndex} index={6}>
            <Paper sx={{ p: 3, mb: 3, bgcolor: '#fff5f5', border: '1px solid #fed7d7' }}>
              <Grid container spacing={3} alignItems="center">
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" sx={{ fontWeight: 700, mb: 1 }}>
                    Weak Topic Threshold Percentage ({weakThreshold}%)
                  </Typography>
                  <Slider
                    value={weakThreshold}
                    min={10}
                    max={90}
                    step={5}
                    onChange={(_, val) => setWeakThreshold(val as number)}
                    valueLabelDisplay="auto"
                  />
                </Grid>
                <Grid item xs={12} md={4}>
                  <TextField
                    fullWidth
                    type="number"
                    label="Minimum Student Responses Required"
                    value={minResponses}
                    onChange={(e) => setMinResponses(parseInt(e.target.value) || 1)}
                  />
                </Grid>
                <Grid item xs={12} md={2}>
                  <Button
                    fullWidth
                    variant="contained"
                    color="error"
                    onClick={handleFetchWeakTopicsOnly}
                    sx={{ py: 1.5, fontWeight: 700 }}
                  >
                    Recalculate
                  </Button>
                </Grid>
              </Grid>
            </Paper>

            {weakTopics && weakTopics.weak_topics.length === 0 ? (
              <Alert severity="success">
                No weak topics detected under threshold {weakThreshold}% with minimum {minResponses} responses.
              </Alert>
            ) : (
              <Grid container spacing={3}>
                {weakTopics?.weak_topics.map((item) => (
                  <Grid item xs={12} md={6} key={item.topic_id}>
                    <Card sx={{ borderRadius: 3, border: '1px solid #fecaca', bgcolor: '#fff' }}>
                      <CardContent>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                          <Typography variant="h6" sx={{ fontWeight: 800, color: '#dc2626' }}>
                            {item.topic_name}
                          </Typography>
                          <Chip label={`WEAK TOPIC (${item.percentage}%)`} color="error" sx={{ fontWeight: 700 }} />
                        </Box>

                        <Typography variant="caption" display="block" sx={{ color: '#64748b', mb: 2 }}>
                          {item.unit_name ? `Unit: ${item.unit_name}` : 'Unit Unmapped'} | Student Responses: {item.response_count}
                        </Typography>

                        <Typography variant="subtitle2" sx={{ fontWeight: 700, mb: 1 }}>
                          Supporting Questions Evidence:
                        </Typography>
                        {item.supporting_questions.map((q) => (
                          <Box key={q.question_id} sx={{ p: 1.5, mb: 1, bgcolor: '#f8fafc', borderRadius: 2 }}>
                            <Typography variant="body2" sx={{ fontWeight: 600 }}>
                              {q.question_number}: {q.question_text}
                            </Typography>
                            <Typography variant="caption" sx={{ color: '#ef4444' }}>
                              Avg Score: {q.average_marks} / {q.max_marks} ({q.percentage}%)
                            </Typography>
                          </Box>
                        ))}
                      </CardContent>
                    </Card>
                  </Grid>
                ))}
              </Grid>
            )}
          </TabPanel>
        </Paper>
      )}
    </Container>
  );
};
