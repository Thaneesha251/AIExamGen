# Exam Quality Intelligence & Blueprint Variance Engine

## Overview
The Exam Quality Intelligence Engine analyzes examination-wide balance against configured blueprint rules across academic dimensions (Units, Topics, Course Outcomes, Bloom levels, Difficulty levels).

## Blueprint Variance Formula
For each academic dimension rule in a blueprint:
\[
\text{variance} = \text{actual\_percentage} - \text{target\_percentage}
\]
where:
- \(\text{target\_percentage} = \frac{\text{rule\_target\_marks}}{\text{blueprint\_total\_marks}} \times 100\)
- \(\text{actual\_percentage} = \frac{\text{actual\_question\_paper\_marks}}{\text{exam\_total\_marks}} \times 100\)

### Status Rules
- **BALANCED:** Absolute variance \(\le 5.0\%\) (`BLUEPRINT_VARIANCE_TOLERANCE`).
- **REVIEW_VARIANCE:** Absolute variance \(> 5.0\%\).

> [!NOTE]
> **Advisory Variance:** Blueprint variance warnings highlight section imbalances to faculty without automatically mutating generated question papers.

## API Endpoints
- `GET /api/v1/analytics/exams/{examination_id}/blueprint`: Exam blueprint balance and variance analysis.
- `GET /api/v1/analytics/exams/{examination_id}/difficulty`: Difficulty distribution breakdown.
- `GET /api/v1/analytics/exams/{examination_id}/discrimination`: Discrimination distribution breakdown.
