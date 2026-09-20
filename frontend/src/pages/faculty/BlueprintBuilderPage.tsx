import React, { useState } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  TextField,
  Button,
  Divider,
  Alert,
  IconButton,
  Chip
} from '@mui/material';
import { Add, Delete, CheckCircle, Save } from '@mui/icons-material';

export const BlueprintBuilderPage: React.FC = () => {
  const [title, setTitle] = useState('');
  const [subjectId, setSubjectId] = useState('');
  const [totalMarks, setTotalMarks] = useState<number>(100);
  const [rules, setRules] = useState([
    { section: 'Part A', question_count: 10, marks_per_question: 2, total_marks: 20 },
    { section: 'Part B', question_count: 5, marks_per_question: 13, total_marks: 65 },
    { section: 'Part C', question_count: 1, marks_per_question: 15, total_marks: 15 }
  ]);
  const [submitted, setSubmitted] = useState(false);

  const handleAddRule = () => {
    setRules([
      ...rules,
      { section: `Part ${String.fromCharCode(65 + rules.length)}`, question_count: 2, marks_per_question: 5, total_marks: 10 }
    ]);
  };

  const handleRemoveRule = (index: number) => {
    setRules(rules.filter((_, i) => i !== index));
  };

  const calculateConfiguredTotal = () => {
    return rules.reduce((sum, r) => sum + r.question_count * r.marks_per_question, 0);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitted(true);
  };

  const configuredTotal = calculateConfiguredTotal();
  const isValid = Math.abs(configuredTotal - totalMarks) < 0.01;

  return (
    <Box sx={{ p: 3, maxWidth: 1100, margin: '0 auto' }}>
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" sx={{ fontWeight: 700, color: '#0f172a' }}>
          Exam Blueprint Builder
        </Typography>
        <Typography variant="body2" sx={{ color: '#64748b' }}>
          Configure section constraints, marks distribution, and Bloom taxonomy rules for constraint-based paper generation.
        </Typography>
      </Box>

      {submitted && (
        <Alert severity="success" sx={{ mb: 3 }} icon={<CheckCircle />}>
          Blueprint configuration saved and validated successfully! You can now use this blueprint to generate question papers.
        </Alert>
      )}

      <Card sx={{ borderRadius: 3, boxShadow: '0 4px 20px rgba(0,0,0,0.05)', mb: 3 }}>
        <CardContent sx={{ p: 3 }}>
          <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
            General Information
          </Typography>

          <Grid container spacing={2}>
            <Grid item xs={12} sm={6}>
              <TextField
                label="Blueprint Title"
                fullWidth
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g. End-Semester CS301 Blueprint"
              />
            </Grid>
            <Grid item xs={12} sm={3}>
              <TextField
                label="Subject ID"
                fullWidth
                value={subjectId}
                onChange={(e) => setSubjectId(e.target.value)}
                placeholder="Subject UUID or Code"
              />
            </Grid>
            <Grid item xs={12} sm={3}>
              <TextField
                label="Target Total Marks"
                type="number"
                fullWidth
                value={totalMarks}
                onChange={(e) => setTotalMarks(Number(e.target.value))}
              />
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      <Card sx={{ borderRadius: 3, boxShadow: '0 4px 20px rgba(0,0,0,0.05)', mb: 3 }}>
        <CardContent sx={{ p: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6" sx={{ fontWeight: 600 }}>
              Section Rules & Constraints
            </Typography>
            <Button startIcon={<Add />} variant="outlined" onClick={handleAddRule} size="small">
              Add Section Rule
            </Button>
          </Box>

          <Divider sx={{ mb: 2 }} />

          {rules.map((rule, idx) => (
            <Grid container spacing={2} key={idx} alignItems="center" sx={{ mb: 2 }}>
              <Grid item xs={12} sm={3}>
                <TextField
                  label="Section Name"
                  size="small"
                  fullWidth
                  value={rule.section}
                  onChange={(e) => {
                    const newRules = [...rules];
                    newRules[idx].section = e.target.value;
                    setRules(newRules);
                  }}
                />
              </Grid>
              <Grid item xs={12} sm={3}>
                <TextField
                  label="Question Count"
                  type="number"
                  size="small"
                  fullWidth
                  value={rule.question_count}
                  onChange={(e) => {
                    const newRules = [...rules];
                    newRules[idx].question_count = Number(e.target.value);
                    newRules[idx].total_marks = newRules[idx].question_count * newRules[idx].marks_per_question;
                    setRules(newRules);
                  }}
                />
              </Grid>
              <Grid item xs={12} sm={3}>
                <TextField
                  label="Marks Per Question"
                  type="number"
                  size="small"
                  fullWidth
                  value={rule.marks_per_question}
                  onChange={(e) => {
                    const newRules = [...rules];
                    newRules[idx].marks_per_question = Number(e.target.value);
                    newRules[idx].total_marks = newRules[idx].question_count * newRules[idx].marks_per_question;
                    setRules(newRules);
                  }}
                />
              </Grid>
              <Grid item xs={12} sm={2}>
                <Chip
                  label={`Subtotal: ${rule.question_count * rule.marks_per_question} Marks`}
                  color="primary"
                  variant="outlined"
                />
              </Grid>
              <Grid item xs={12} sm={1}>
                <IconButton color="error" onClick={() => handleRemoveRule(idx)}>
                  <Delete />
                </IconButton>
              </Grid>
            </Grid>
          ))}

          <Box sx={{ mt: 3, p: 2, bgcolor: '#f8fafc', borderRadius: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
              Configured Rules Total: {configuredTotal} / {totalMarks} Marks
            </Typography>
            <Chip
              label={isValid ? 'Total Marks Match' : 'Marks Mismatch!'}
              color={isValid ? 'success' : 'error'}
              sx={{ fontWeight: 700 }}
            />
          </Box>
        </CardContent>
      </Card>

      <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 2 }}>
        <Button variant="contained" size="large" startIcon={<Save />} onClick={handleSubmit} disabled={!isValid}>
          Save Blueprint
        </Button>
      </Box>
    </Box>
  );
};
