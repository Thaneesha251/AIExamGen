# AIExamGen

**AI-Powered Exam Generation and Evaluation Platform**

AIExamGen is a full-stack platform that uses Artificial Intelligence to assist faculty in **question generation, exam paper creation, answer evaluation, similarity analysis, analytics, and question-quality assessment**.

The system follows a **Human-in-the-Loop** approach, where AI provides evaluation suggestions while faculty members review, modify, and finalize the results.

## Key Features

* AI-assisted question generation
* Syllabus and question-bank management
* Exam blueprint and paper generation
* Answer-key and rubric management
* Student answer-paper ingestion
* AI-assisted answer evaluation
* Faculty review and manual mark override
* Similarity analysis
* Examination analytics
* Question-quality analysis
* Result finalization

## Tech Stack

**Frontend:** React, Vite
**Backend:** Python, FastAPI, SQLAlchemy
**AI/ML:** Python, NLP, AI-based evaluation
**Database:** SQLite / PostgreSQL
**Migration:** Alembic
**Testing:** Pytest

## Project Structure

```text
AIExamGen/
├── ai/
├── backend/
├── frontend/
├── docs/
├── storage/
├── .env.example
├── docker-compose.yml
└── README.md
```

## Workflow

```text
Syllabus
   ↓
Question Bank
   ↓
AI Question Generation
   ↓
Exam Paper
   ↓
Answer Evaluation
   ↓
Faculty Review
   ↓
Final Results
   ↓
Analytics
```

## Status

**Phases 1–12 implemented**, covering the complete workflow from academic setup and question generation to AI-assisted evaluation, faculty review, similarity analysis, analytics, and question quality.

## Objective

To reduce repetitive examination work using AI while keeping **faculty members as the final authority for academic evaluation**.
