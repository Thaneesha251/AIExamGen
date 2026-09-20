# Weak Topic Detection Engine

## Overview
The Weak Topic Detection Engine analyzes performance across topics to pinpoint syllabus areas requiring academic remediation or faculty intervention.

> [!TIP]
> **Threshold & Sample-Size Control:** Configurable percentage threshold (e.g. \(<50\%\)) and minimum response count filters prevent false positives on single-question anomalies.

## Weak Topic Criteria
A topic is classified as **WEAK** if:
1. **Average Cohort Score Percentage:** Total marks obtained in the topic divided by maximum achievable marks falls below the `threshold_percentage` (default `50.0%`).
2. **Minimum Response Count:** Total evaluated answer items mapped to the topic meets or exceeds `minimum_responses` (default `3` for examination level, `1` for individual student level).

## Output Structure & Evidence
Each detected weak topic includes:
- **Topic Identifiers:** `topic_id`, `topic_name`, `unit_id`, `unit_name`, `subject_name`.
- **Performance Metrics:** `average_percentage`, `marks_obtained`, `max_marks`, `response_count`.
- **Question Evidence:** Array of contributing questions under the topic, including question text, average marks, max marks, and percentage achieved.

## API Endpoints
- `GET /api/v1/analytics/examinations/{examination_id}/weak-topics`: Detect weak topics for an examination cohort (`?threshold=50.0&min_responses=3`).
- `GET /api/v1/analytics/students/{student_id}/weak-topics`: Detect weak topics for an individual student across all finalized exams (`?threshold=50.0&min_responses=1`).
