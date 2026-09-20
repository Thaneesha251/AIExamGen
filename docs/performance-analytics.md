# Student Performance Analytics Engine

## Overview
The Performance Analytics Engine processes finalized examination evaluations (`Evaluation.status == FINALIZED`) to compute multi-dimensional academic metrics.

> [!NOTE]
> **Finalized Evaluation Invariant:** To prevent skewed or premature statistics, draft or un-reviewed evaluations are strictly excluded from all performance metrics.

## Aggregation Dimensions
1. **Examination Overview:** Cohort total students, finalized paper count, average marks, median marks, highest marks, lowest marks, max possible marks, average percentage, and pass rate (\(\ge 40\%\)).
2. **Student Performance List & Ranking:** Per-student total score, percentage, evaluation status, finalized timestamp, and rank.
3. **Question Analytics:** Response count, max marks, average marks, percentage achieved, highest/lowest marks, difficulty, and Bloom taxonomy level per question.
4. **Unit Breakdown:** Performance grouped by academic Unit (Unit number, title, question count, average marks, percentage).
5. **Topic Breakdown:** Performance grouped by Topic under each Unit.
6. **Course Outcome (CO) Breakdown:** Alignment with mapped Learning Outcomes (CO code, description, percentage achieved).
7. **Bloom Taxonomy Level Breakdown:** Distribution across REMEMBER, UNDERSTAND, APPLY, ANALYZE, EVALUATE, CREATE.
8. **Difficulty Level Breakdown:** Distribution across EASY, MEDIUM, HARD.

## API Endpoints
- `GET /api/v1/analytics/examinations/{examination_id}`: Exam overview analytics.
- `GET /api/v1/analytics/examinations/{examination_id}/students`: Student list performance ranking.
- `GET /api/v1/analytics/examinations/{examination_id}/questions`: Question level performance breakdown.
- `GET /api/v1/analytics/examinations/{examination_id}/units`: Unit level performance breakdown.
- `GET /api/v1/analytics/examinations/{examination_id}/topics`: Topic level performance breakdown.
- `GET /api/v1/analytics/examinations/{examination_id}/learning-outcomes`: Learning Outcome (CO) breakdown.
- `GET /api/v1/analytics/examinations/{examination_id}/bloom`: Bloom taxonomy level breakdown.
- `GET /api/v1/analytics/examinations/{examination_id}/difficulty`: Difficulty level breakdown.
- `GET /api/v1/analytics/students/{student_id}`: Single student multi-exam performance profile.
