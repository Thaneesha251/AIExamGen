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
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Select,
  MenuItem,
  FormControl,
  InputLabel
} from '@mui/material';
import { ExpandMore, Save, ArrowBack, AutoAwesome, CheckCircle } from '@mui/icons-material';
import { useParams, useNavigate } from 'react-router-dom';

export const AnswerKeyEditorPage: React.FC = () => {
  const { paperId } = useParams<{ paperId: string }>();
  const navigate = useNavigate();

  const [saved, setSaved] = useState(false);
  const [items, setItems] = useState([
    {
      id: 'item-1',
      question_number: 'Q1',
      question_text: 'Explain Binary Search algorithm and derive its time complexity.',
      marks: 5,
      model_answer: 'Binary Search is an efficient searching algorithm that operates on a sorted array by repeatedly dividing the search interval in half. Time complexity is O(log n).',
      keywords: 'binary search, sorted array, O(log n), divide and conquer',
      concepts: 'divide and conquer, search interval',
      marking_notes: 'Award 3 marks for algorithm steps, 2 marks for logarithmic complexity derivation.',
      rubric_id: ''
    },
    {
      id: 'item-2',
      question_number: 'Q2',
      question_text: 'Define Stack ADT and list its primary operations.',
      marks: 2,
      model_answer: 'Stack is a linear Data Structure following LIFO (Last In First Out) principle. Operations: Push, Pop, Peek/Top, IsEmpty.',
      keywords: 'LIFO, push, pop, peek',
      concepts: 'Stack ADT, LIFO',
      marking_notes: '1 mark for LIFO definition, 1 mark for operations list.',
      rubric_id: ''
    }
  ]);

  const handleSave = () => {
    setSaved(true);
  };

  return (
    <Box sx={{ p: 3, maxWidth: 1100, margin: '0 auto' }}>
      <Button startIcon={<ArrowBack />} onClick={() => navigate(`/faculty/question-papers/${paperId}/review`)} sx={{ mb: 2 }}>
        Back to Paper Review
      </Button>

      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 700, color: '#0f172a' }}>
            Answer Key & Solution Editor
          </Typography>
          <Typography variant="body2" sx={{ color: '#64748b' }}>
            Configure model answers, keywords, concepts, evaluation guidance, and linked rubrics for future evaluation.
          </Typography>
        </Box>

        <Button variant="contained" startIcon={<Save />} onClick={handleSave} sx={{ borderRadius: 2.5, px: 3, py: 1 }}>
          Save Changes
        </Button>
      </Box>

      {saved && (
        <Alert severity="success" sx={{ mb: 3 }} icon={<CheckCircle />}>
          Answer key updated successfully! New version created with updated model answers.
        </Alert>
      )}

      {items.map((item, idx) => (
        <Card key={item.id} sx={{ borderRadius: 3, boxShadow: '0 4px 20px rgba(0,0,0,0.05)', mb: 3 }}>
          <CardContent sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1.5 }}>
              <Typography variant="h6" sx={{ fontWeight: 700, color: '#1e3a8a' }}>
                {item.question_number} — [{item.marks} Marks]
              </Typography>
              <Chip label={`${item.marks} Marks`} color="primary" size="small" variant="outlined" />
            </Box>

            <Typography variant="body1" sx={{ fontWeight: 600, mb: 2, color: '#334155' }}>
              Question: {item.question_text}
            </Typography>

            <Divider sx={{ mb: 2 }} />

            <Grid container spacing={2}>
              <Grid item xs={12}>
                <TextField
                  label="Model Answer"
                  multiline
                  rows={4}
                  fullWidth
                  value={item.model_answer}
                  onChange={(e) => {
                    const newItems = [...items];
                    newItems[idx].model_answer = e.target.value;
                    setItems(newItems);
                  }}
                />
              </Grid>

              <Grid item xs={12} sm={6}>
                <TextField
                  label="Keywords (comma separated)"
                  fullWidth
                  size="small"
                  value={item.keywords}
                  onChange={(e) => {
                    const newItems = [...items];
                    newItems[idx].keywords = e.target.value;
                    setItems(newItems);
                  }}
                />
              </Grid>

              <Grid item xs={12} sm={6}>
                <TextField
                  label="Academic Concepts"
                  fullWidth
                  size="small"
                  value={item.concepts}
                  onChange={(e) => {
                    const newItems = [...items];
                    newItems[idx].concepts = e.target.value;
                    setItems(newItems);
                  }}
                />
              </Grid>

              <Grid item xs={12}>
                <TextField
                  label="Faculty Marking Notes & Evaluation Guidance"
                  fullWidth
                  size="small"
                  value={item.marking_notes}
                  onChange={(e) => {
                    const newItems = [...items];
                    newItems[idx].marking_notes = e.target.value;
                    setItems(newItems);
                  }}
                />
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      ))}
    </Box>
  );
};
