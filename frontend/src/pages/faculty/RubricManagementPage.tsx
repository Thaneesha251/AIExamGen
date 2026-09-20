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
  Chip,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow
} from '@mui/material';
import { Add, Delete, Save, CheckCircle } from '@mui/icons-material';

export const RubricManagementPage: React.FC = () => {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [totalMarks, setTotalMarks] = useState<number>(10);
  const [submitted, setSubmitted] = useState(false);

  const [criteria, setCriteria] = useState([
    { criterion: 'Concept Understanding', description: 'Grasping core theoretical principles', marks: 3 },
    { criterion: 'Algorithm Explanation', description: 'Step-by-step logic clarity', marks: 3 },
    { criterion: 'Time & Space Complexity', description: 'Derivation and accuracy of complexity analysis', marks: 2 },
    { criterion: 'Code / Diagram Clarity', description: 'Proper syntax, formatting, and examples', marks: 2 }
  ]);

  const handleAddCriterion = () => {
    setCriteria([
      ...criteria,
      { criterion: `Criterion ${criteria.length + 1}`, description: '', marks: 2 }
    ]);
  };

  const handleRemoveCriterion = (index: number) => {
    setCriteria(criteria.filter((_, i) => i !== index));
  };

  const calculateSum = () => criteria.reduce((sum, c) => sum + c.marks, 0);

  const currentSum = calculateSum();
  const isValid = Math.abs(currentSum - totalMarks) < 0.01;

  const handleSubmit = () => {
    setSubmitted(true);
  };

  return (
    <Box sx={{ p: 3, maxWidth: 1100, margin: '0 auto' }}>
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" sx={{ fontWeight: 700, color: '#0f172a' }}>
          Evaluation Rubric Builder
        </Typography>
        <Typography variant="body2" sx={{ color: '#64748b' }}>
          Create structured evaluation rubrics with explicit criteria weights and partial credit rules.
        </Typography>
      </Box>

      {submitted && (
        <Alert severity="success" sx={{ mb: 3 }} icon={<CheckCircle />}>
          Rubric saved and validated successfully! Total criterion marks equal target marks ({totalMarks}).
        </Alert>
      )}

      <Card sx={{ borderRadius: 3, boxShadow: '0 4px 20px rgba(0,0,0,0.05)', mb: 3 }}>
        <CardContent sx={{ p: 3 }}>
          <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
            Rubric Overview
          </Typography>

          <Grid container spacing={2}>
            <Grid item xs={12} sm={6}>
              <TextField
                label="Rubric Name"
                fullWidth
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. 10-Mark Descriptive Evaluation Rubric"
              />
            </Grid>
            <Grid item xs={12} sm={3}>
              <TextField
                label="Target Question Marks"
                type="number"
                fullWidth
                value={totalMarks}
                onChange={(e) => setTotalMarks(Number(e.target.value))}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                label="Description"
                fullWidth
                multiline
                rows={2}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Optional description of evaluation guidelines..."
              />
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      <Card sx={{ borderRadius: 3, boxShadow: '0 4px 20px rgba(0,0,0,0.05)', mb: 3 }}>
        <CardContent sx={{ p: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6" sx={{ fontWeight: 600 }}>
              Criteria Breakdown
            </Typography>
            <Button startIcon={<Add />} variant="outlined" onClick={handleAddCriterion} size="small">
              Add Criterion
            </Button>
          </Box>

          <Divider sx={{ mb: 2 }} />

          <Table>
            <TableHead sx={{ bgcolor: '#f8fafc' }}>
              <TableRow>
                <TableCell sx={{ fontWeight: 700 }}>Criterion Name</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Description</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Marks</TableCell>
                <TableCell align="right" sx={{ fontWeight: 700 }}>Action</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {criteria.map((c, idx) => (
                <TableRow key={idx}>
                  <TableCell>
                    <TextField
                      size="small"
                      fullWidth
                      value={c.criterion}
                      onChange={(e) => {
                        const newC = [...criteria];
                        newC[idx].criterion = e.target.value;
                        setCriteria(newC);
                      }}
                    />
                  </TableCell>
                  <TableCell>
                    <TextField
                      size="small"
                      fullWidth
                      value={c.description}
                      onChange={(e) => {
                        const newC = [...criteria];
                        newC[idx].description = e.target.value;
                        setCriteria(newC);
                      }}
                    />
                  </TableCell>
                  <TableCell style={{ width: 120 }}>
                    <TextField
                      type="number"
                      size="small"
                      fullWidth
                      value={c.marks}
                      onChange={(e) => {
                        const newC = [...criteria];
                        newC[idx].marks = Number(e.target.value);
                        setCriteria(newC);
                      }}
                    />
                  </TableCell>
                  <TableCell align="right">
                    <IconButton color="error" onClick={() => handleRemoveCriterion(idx)}>
                      <Delete />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>

          <Box sx={{ mt: 3, p: 2, bgcolor: '#f8fafc', borderRadius: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
              Criterion Sum: {currentSum} / {totalMarks} Marks
            </Typography>
            <Chip
              label={isValid ? 'Criteria Marks Match Total' : 'Criteria Sum Mismatch!'}
              color={isValid ? 'success' : 'error'}
              sx={{ fontWeight: 700 }}
            />
          </Box>
        </CardContent>
      </Card>

      <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
        <Button variant="contained" size="large" startIcon={<Save />} onClick={handleSubmit} disabled={!isValid}>
          Save Rubric
        </Button>
      </Box>
    </Box>
  );
};
