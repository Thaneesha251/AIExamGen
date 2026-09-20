# Question Bank Insights & Weak Coverage Detection Engine

## Overview
The Question Bank Insights Engine evaluates multi-examination historical performance data and usage metrics across all questions for a subject.

## Multi-Exam Empirical Aggregations
For each question in a subject's question bank:
- **Times Used:** Count of distinct historical question paper versions containing the question.
- **Total Responses:** Total evaluated responses in finalized examinations (`Evaluation.status == FINALIZED`).
- **Historical Average Percentage:** Mean normalized score percentage across all finalized examinations.
- **Status Indicator:** `STABLE` (has finalized historical evaluation data) or `UNTESTED` (no finalized evaluation data yet).

## Weak Assessment Coverage
Analyzes syllabus Units and Learning Outcomes to detect areas with zero or low historical assessment coverage (`LOW`, `MODERATE`, `HIGH`), helping faculty identify under-assessed syllabus topics before drafting future exam papers.

## API Endpoints
- `GET /api/v1/analytics/question-bank/insights`: Empirical multi-exam question bank usage and quality insights.
- `GET /api/v1/analytics/question-bank/weak-coverage`: Assessment coverage analysis by syllabus unit.
