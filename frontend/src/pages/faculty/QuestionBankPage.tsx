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
  IconButton,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  Tabs,
  Tab,
  Card,
  CardContent,
  Checkbox,
  Tooltip,
} from '@mui/material';
import {
  Add as AddIcon,
  UploadFile as UploadIcon,
  Search as SearchIcon,
  Visibility as ViewIcon,
  Folder as FolderIcon,
  Warning as WarningIcon,
  CheckCircle as ApproveIcon,
  Delete as DeleteIcon,
} from '@mui/icons-material';
import { Question, QuestionBank, QuestionType, DifficultyLevel, BloomLevel, QuestionStatus } from '../../types/question';
import { academicService, Subject } from '../../services/academicService';
import { questionService } from '../../services/questionService';
import { QuestionReviewModal } from './QuestionReviewModal';

export const QuestionBankPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState(0);
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [selectedSubjectId, setSelectedSubjectId] = useState<string>('');

  // Filters
  const [searchQuery, setSearchQuery] = useState('');
  const [typeFilter, setTypeFilter] = useState<string>('');
  const [diffFilter, setDiffFilter] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('');

  // Questions Data
  const [questions, setQuestions] = useState<Question[]>([]);
  const [totalQuestions, setTotalQuestions] = useState(0);
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(10);
  const [loading, setLoading] = useState(false);
  const [selectedQuestionIds, setSelectedQuestionIds] = useState<string[]>([]);

  // Question Banks Data
  const [questionBanks, setQuestionBanks] = useState<QuestionBank[]>([]);

  // Modals
  const [selectedQuestion, setSelectedQuestion] = useState<Question | null>(null);
  const [reviewModalOpen, setReviewModalOpen] = useState(false);
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [csvModalOpen, setCsvModalOpen] = useState(false);
  const [bankModalOpen, setBankModalOpen] = useState(false);

  // New Question Form State
  const [newText, setNewText] = useState('');
  const [newType, setNewType] = useState<QuestionType>('SHORT_ANSWER');
  const [newMarks, setNewMarks] = useState(5);
  const [newDiff, setNewDiff] = useState<DifficultyLevel>('MEDIUM');
  const [newBloom, setNewBloom] = useState<BloomLevel>('UNDERSTAND');
  const [newAnswer, setNewAnswer] = useState('');

  // MCQ Options
  const [mcqOpts, setMcqOpts] = useState<string[]>(['Option A', 'Option B', 'Option C', 'Option D']);
  const [mcqCorrect, setMcqCorrect] = useState<string>('Option A');

  // CSV Import State
  const [csvFile, setCsvFile] = useState<File | null>(null);
  const [csvResult, setCsvResult] = useState<{ created_count: number; failed_count: number; errors: string[] } | null>(null);

  // Bank Form State
  const [bankName, setBankName] = useState('');
  const [bankDesc, setBankDesc] = useState('');

  useEffect(() => {
    loadSubjects();
  }, []);

  useEffect(() => {
    if (selectedSubjectId) {
      fetchQuestions();
      fetchQuestionBanks();
    }
  }, [selectedSubjectId, page, pageSize, searchQuery, typeFilter, diffFilter, statusFilter]);

  const loadSubjects = async () => {
    try {
      const data = await academicService.getSubjects();
      setSubjects(data);
      if (data.length > 0) {
        setSelectedSubjectId(data[0].id);
      }
    } catch (err) {
      console.error('Failed to load subjects', err);
    }
  };

  const fetchQuestions = async () => {
    if (!selectedSubjectId) return;
    setLoading(true);
    try {
      const res = await questionService.searchQuestions({
        subject_id: selectedSubjectId,
        search: searchQuery || undefined,
        question_type: typeFilter || undefined,
        difficulty: diffFilter || undefined,
        status: statusFilter || undefined,
        page: page + 1,
        page_size: pageSize,
      });
      setQuestions(res.items);
      setTotalQuestions(res.total);
    } catch (err) {
      console.error('Failed to fetch questions', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchQuestionBanks = async () => {
    if (!selectedSubjectId) return;
    try {
      const data = await questionService.listQuestionBanks(selectedSubjectId);
      setQuestionBanks(data);
    } catch (err) {
      console.error('Failed to fetch question banks', err);
    }
  };

  const handleCreateQuestion = async () => {
    if (!selectedSubjectId || !newText) return;
    try {
      await questionService.createQuestion({
        subject_id: selectedSubjectId,
        question_text: newText,
        question_type: newType,
        marks: newMarks,
        difficulty: newDiff,
        bloom_level: newBloom,
        expected_answer: newAnswer,
        options: newType === 'MCQ' ? { options: mcqOpts, correct_option: mcqCorrect } : undefined,
      });
      setCreateModalOpen(false);
      setNewText('');
      setNewAnswer('');
      fetchQuestions();
    } catch (err: any) {
      alert(err.message || 'Failed to create question');
    }
  };

  const handleCsvImport = async () => {
    if (!selectedSubjectId || !csvFile) return;
    try {
      const res = await questionService.importCsvQuestions(selectedSubjectId, csvFile);
      setCsvResult(res);
      fetchQuestions();
    } catch (err: any) {
      alert(err.message || 'CSV Import failed');
    }
  };

  const handleCreateBank = async () => {
    if (!selectedSubjectId || !bankName) return;
    try {
      await questionService.createQuestionBank({
        subject_id: selectedSubjectId,
        name: bankName,
        description: bankDesc,
      });
      setBankModalOpen(false);
      setBankName('');
      setBankDesc('');
      fetchQuestionBanks();
    } catch (err: any) {
      alert(err.message || 'Failed to create question bank');
    }
  };

  const handleSelectAll = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.checked) {
      setSelectedQuestionIds(questions.map((q) => q.id));
    } else {
      setSelectedQuestionIds([]);
    }
  };

  const handleSelectOne = (id: string) => {
    if (selectedQuestionIds.includes(id)) {
      setSelectedQuestionIds(selectedQuestionIds.filter((item) => item !== id));
    } else {
      setSelectedQuestionIds([...selectedQuestionIds, id]);
    }
  };

  return (
    <Box p={3}>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <div>
          <Typography variant="h4" fontWeight="bold">
            Question Bank Management
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Manage academic questions, version history, quality validation, and question pools.
          </Typography>
        </div>
        <Box display="flex" gap={2}>
          <Button
            variant="outlined"
            startIcon={<UploadIcon />}
            onClick={() => {
              setCsvResult(null);
              setCsvFile(null);
              setCsvModalOpen(true);
            }}
          >
            Import CSV
          </Button>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setCreateModalOpen(true)}
          >
            Create Question
          </Button>
        </Box>
      </Box>

      {/* Subject Filter Bar */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} sm={4}>
            <TextField
              select
              label="Select Subject"
              fullWidth
              size="small"
              value={selectedSubjectId}
              onChange={(e) => setSelectedSubjectId(e.target.value)}
            >
              {subjects.map((sub) => (
                <MenuItem key={sub.id} value={sub.id}>
                  {sub.code} — {sub.name}
                </MenuItem>
              ))}
            </TextField>
          </Grid>
          <Grid item xs={12} sm={3}>
            <TextField
              size="small"
              fullWidth
              placeholder="Search questions..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              InputProps={{ startAdornment: <SearchIcon color="action" sx={{ mr: 1 }} /> }}
            />
          </Grid>
          <Grid item xs={6} sm={2}>
            <TextField
              select
              size="small"
              fullWidth
              label="Question Type"
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
            >
              <MenuItem value="">All Types</MenuItem>
              <MenuItem value="MCQ">MCQ</MenuItem>
              <MenuItem value="SHORT_ANSWER">Short Answer</MenuItem>
              <MenuItem value="LONG_ANSWER">Long Answer</MenuItem>
              <MenuItem value="NUMERICAL">Numerical</MenuItem>
              <MenuItem value="PROGRAMMING">Programming</MenuItem>
            </TextField>
          </Grid>
          <Grid item xs={6} sm={3}>
            <TextField
              select
              size="small"
              fullWidth
              label="Status"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
            >
              <MenuItem value="">All Statuses</MenuItem>
              <MenuItem value="ACTIVE">Active</MenuItem>
              <MenuItem value="APPROVED">Approved</MenuItem>
              <MenuItem value="UNDER_REVIEW">Under Review</MenuItem>
              <MenuItem value="REJECTED">Rejected</MenuItem>
            </TextField>
          </Grid>
        </Grid>
      </Paper>

      {/* Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}>
        <Tabs value={activeTab} onChange={(_, v) => setActiveTab(v)}>
          <Tab label={`Question Repository (${totalQuestions})`} />
          <Tab label={`Question Banks (${questionBanks.length})`} icon={<FolderIcon />} iconPosition="start" />
        </Tabs>
      </Box>

      {/* Tab 0: Question Repository Table */}
      {activeTab === 0 && (
        <Paper>
          <TableContainer>
            <Table>
              <TableHead sx={{ background: '#f8f9fa' }}>
                <TableRow>
                  <TableCell padding="checkbox">
                    <Checkbox
                      checked={questions.length > 0 && selectedQuestionIds.length === questions.length}
                      onChange={handleSelectAll}
                    />
                  </TableCell>
                  <TableCell>Question Text</TableCell>
                  <TableCell>Type</TableCell>
                  <TableCell>Marks</TableCell>
                  <TableCell>Difficulty</TableCell>
                  <TableCell>Bloom</TableCell>
                  <TableCell>Version</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell align="right">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {questions.map((q) => (
                  <TableRow key={q.id} hover selected={selectedQuestionIds.includes(q.id)}>
                    <TableCell padding="checkbox">
                      <Checkbox
                        checked={selectedQuestionIds.includes(q.id)}
                        onChange={() => handleSelectOne(q.id)}
                      />
                    </TableCell>
                    <TableCell sx={{ maxWidth: 320 }}>
                      <Typography variant="body2" fontWeight="500" noWrap>
                        {q.question_text}
                      </Typography>
                      {q.validation_data && !q.validation_data.is_valid && (
                        <Box display="flex" alignItems="center" gap={0.5} mt={0.5}>
                          <WarningIcon color="warning" sx={{ fontSize: 16 }} />
                          <Typography variant="caption" color="warning.main">
                            Flagged ({q.validation_data.warnings.length} warning)
                          </Typography>
                        </Box>
                      )}
                    </TableCell>
                    <TableCell>
                      <Chip label={q.question_type} size="small" variant="outlined" />
                    </TableCell>
                    <TableCell>{q.marks}</TableCell>
                    <TableCell>
                      <Chip
                        label={q.difficulty}
                        size="small"
                        color={q.difficulty === 'EASY' ? 'success' : q.difficulty === 'MEDIUM' ? 'warning' : 'error'}
                      />
                    </TableCell>
                    <TableCell>{q.bloom_level}</TableCell>
                    <TableCell>
                      <Chip label={`v${q.version}`} size="small" color="info" />
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={q.status}
                        size="small"
                        color={
                          q.status === 'APPROVED' || q.status === 'ACTIVE'
                            ? 'success'
                            : q.status === 'UNDER_REVIEW' || q.status === 'AI_GENERATED'
                            ? 'warning'
                            : 'error'
                        }
                      />
                    </TableCell>
                    <TableCell align="right">
                      <Tooltip title="View Details & Review">
                        <IconButton
                          color="primary"
                          onClick={() => {
                            setSelectedQuestion(q);
                            setReviewModalOpen(true);
                          }}
                        >
                          <ViewIcon />
                        </IconButton>
                      </Tooltip>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
          <TablePagination
            component="div"
            count={totalQuestions}
            page={page}
            onPageChange={(_, p) => setPage(p)}
            rowsPerPage={pageSize}
            onRowsPerPageChange={(e) => {
              setPageSize(parseInt(e.target.value, 10));
              setPage(0);
            }}
          />
        </Paper>
      )}

      {/* Tab 1: Question Banks Grid */}
      {activeTab === 1 && (
        <Box>
          <Box display="flex" justifyContent="flex-end" mb={2}>
            <Button variant="contained" startIcon={<FolderIcon />} onClick={() => setBankModalOpen(true)}>
              Create Question Bank
            </Button>
          </Box>
          <Grid container spacing={3}>
            {questionBanks.map((bank) => (
              <Grid item xs={12} sm={6} md={4} key={bank.id}>
                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="h6" fontWeight="bold">
                      {bank.name}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                      {bank.description || 'No description provided.'}
                    </Typography>
                    <Chip label={`${bank.items?.length || 0} Questions`} color="primary" size="small" />
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Box>
      )}

      {/* Question Review Modal */}
      <QuestionReviewModal
        open={reviewModalOpen}
        question={selectedQuestion}
        onClose={() => setReviewModalOpen(false)}
        onQuestionUpdated={() => fetchQuestions()}
      />

      {/* Create Question Modal */}
      <Dialog open={createModalOpen} onClose={() => setCreateModalOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Create Manual Question</DialogTitle>
        <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          <TextField
            label="Question Text"
            multiline
            rows={3}
            fullWidth
            sx={{ mt: 1, mb: 2 }}
            value={newText}
            onChange={(e) => setNewText(e.target.value)}
          />
          <Grid container spacing={2}>
            <Grid item xs={6}>
              <TextField
                select
                label="Type"
                fullWidth
                size="small"
                value={newType}
                onChange={(e) => setNewType(e.target.value as QuestionType)}
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
                type="number"
                label="Marks"
                fullWidth
                size="small"
                value={newMarks}
                onChange={(e) => setNewMarks(Number(e.target.value))}
              />
            </Grid>
            <Grid item xs={6}>
              <TextField
                select
                label="Difficulty"
                fullWidth
                size="small"
                value={newDiff}
                onChange={(e) => setNewDiff(e.target.value as DifficultyLevel)}
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
                value={newBloom}
                onChange={(e) => setNewBloom(e.target.value as BloomLevel)}
              >
                <MenuItem value="REMEMBER">REMEMBER</MenuItem>
                <MenuItem value="UNDERSTAND">UNDERSTAND</MenuItem>
                <MenuItem value="APPLY">APPLY</MenuItem>
                <MenuItem value="ANALYZE">ANALYZE</MenuItem>
                <MenuItem value="EVALUATE">EVALUATE</MenuItem>
                <MenuItem value="CREATE">CREATE</MenuItem>
              </TextField>
            </Grid>
          </Grid>
          <TextField
            label="Expected Answer"
            multiline
            rows={2}
            fullWidth
            sx={{ mt: 2 }}
            value={newAnswer}
            onChange={(e) => setNewAnswer(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateModalOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleCreateQuestion}>Create Question</Button>
        </DialogActions>
      </Dialog>

      {/* CSV Import Modal */}
      <Dialog open={csvModalOpen} onClose={() => setCsvModalOpen(false)} maxWidth="xs" fullWidth>
        <DialogTitle>Import Questions from CSV</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" mb={2}>
            Upload a CSV file containing columns: question_text, question_type, difficulty, bloom_level, marks, expected_answer.
          </Typography>
          <Button variant="outlined" component="label" fullWidth>
            Select CSV File
            <input type="file" accept=".csv" hidden onChange={(e) => setCsvFile(e.target.files?.[0] || null)} />
          </Button>
          {csvFile && <Typography variant="caption" mt={1} display="block">Selected: {csvFile.name}</Typography>}

          {csvResult && (
            <Alert severity={csvResult.failed_count > 0 ? 'warning' : 'success'} sx={{ mt: 2 }}>
              Imported: {csvResult.created_count} questions. Failed: {csvResult.failed_count}.
            </Alert>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCsvModalOpen(false)}>Close</Button>
          <Button variant="contained" disabled={!csvFile} onClick={handleCsvImport}>Import</Button>
        </DialogActions>
      </Dialog>

      {/* Create Bank Modal */}
      <Dialog open={bankModalOpen} onClose={() => setBankModalOpen(false)} maxWidth="xs" fullWidth>
        <DialogTitle>Create Question Bank</DialogTitle>
        <DialogContent>
          <TextField
            label="Bank Name"
            fullWidth
            size="small"
            sx={{ mt: 1, mb: 2 }}
            value={bankName}
            onChange={(e) => setBankName(e.target.value)}
          />
          <TextField
            label="Description"
            multiline
            rows={2}
            fullWidth
            size="small"
            value={bankDesc}
            onChange={(e) => setBankDesc(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setBankModalOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleCreateBank}>Create Bank</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};
