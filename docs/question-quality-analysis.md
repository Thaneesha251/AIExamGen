# Question Quality & Discrimination Analysis Engine

## Overview
Phase 12 introduces post-evaluation question quality and discrimination analysis for evaluated student answer papers within an examination.
The engine calculates normalized average score percentages, discrimination indices (top 27% vs bottom 27%), difficulty categories, and quality status classifications.

> [!IMPORTANT]
> **Advisory & Faculty-In-The-Loop Principle:** Question quality analysis generates descriptive statuses (`GOOD`, `REVIEW_DIFFICULTY`, `REVIEW_DISCRIMINATION`, `REVIEW_SIMILARITY`, `REVIEW_MULTIPLE_SIGNALS`, `INSUFFICIENT_DATA`). The system **NEVER** automatically deletes, disables, or invalidates questions, nor does it modify finalized student marks.

## Mathematical Formulas

### Normalized Question Score
\[
\text{normalized\_score} = \frac{\text{awarded\_marks}}{\text{maximum\_marks}}
\]

### Difficulty Index & Categories
\[
\text{difficulty\_index} = \text{average}(\text{normalized\_score}) \times 100
\]
- **Easy:** \(\ge 75.0\%\) (`QUESTION_DIFFICULTY_EASY_THRESHOLD`)
- **Moderate:** \(\ge 40.0\%\) and \(< 75.0\%\) (`QUESTION_DIFFICULTY_MODERATE_THRESHOLD`)
- **Difficult:** \(< 40.0\%\)

### Discrimination Index Calculation
Divides finalized student cohort into top 27% (upper group) and bottom 27% (lower group) based on total finalized examination score.
\[
\text{Discrimination Index} = \text{Upper Group Mean} - \text{Lower Group Mean}
\]
- **Strong:** \(\ge 0.40\) (`DISCRIMINATION_STRONG_THRESHOLD`)
- **Acceptable:** \(0.20 \le \text{Index} < 0.40\) (`DISCRIMINATION_ACCEPTABLE_THRESHOLD`)
- **Weak:** \(0.00 \le \text{Index} < 0.20\) (`DISCRIMINATION_WEAK_THRESHOLD`)
- **Negative:** \(< 0.00\) (Indicates weaker students outscored top students)
- **Insufficient Sample:** Returned if cohort size \(< 4\) or top/bottom groups are empty.

## API Endpoints
- `GET /api/v1/analytics/exams/{examination_id}/quality`: Full Exam Quality Dashboard analysis.
- `GET /api/v1/analytics/exams/{examination_id}/questions`: Question quality analysis list.
- `GET /api/v1/analytics/exams/{examination_id}/questions/{question_id}`: Comprehensive single question detail.
- `POST /api/v1/analytics/questions/{question_id}/review`: Record faculty quality review decision and note.
