# AI ExamGen — Technical System Architecture

## 1. High-Level Architecture Overview

AI ExamGen follows a decoupled, modular service-oriented architecture designed for scalability, maintainability, and domain isolation.

```text
+-----------------------------------------------------------------------+
|                            FRONTEND LAYER                             |
|       React 18 + Vite + TypeScript + Material UI (SPA Dashboard)       |
+-----------------------------------------------------------------------+
                                   |
                             HTTP / REST API
                                   v
+-----------------------------------------------------------------------+
|                            BACKEND LAYER                              |
|   FastAPI Application (/api/v1)                                       |
|   ├── Auth & Security (JWT / Bcrypt)                                  |
|   ├── Controller Routes & Validation (Pydantic v2)                    |
|   ├── Repository Data Access Layer                                    |
|   └── Storage Abstraction (Syllabus, Answer Sheets, Reports)          |
+-----------------------------------------------------------------------+
            |                                         |
            v                                         v
+-----------------------+                 +-----------------------+
|    DATABASE LAYER     |                 |       AI LAYER        |
|  PostgreSQL / SQLite  |                 | Modular Agents &      |
|  SQLAlchemy 2.0 ORM   |                 | Replaceable Providers |
|  (30+ Domain Models)  |                 | (Gemini/OpenAI/Mock)  |
+-----------------------+                 +-----------------------+
```

## 2. Component Breakdown

### Frontend Layer (`frontend/`)
- Single Page Application (SPA) built with React 18, Vite, and TypeScript.
- Material UI (MUI v5) academic theme tokens with custom card elevation, table typography, and role badges.
- Dynamic visualizations powered by Recharts.
- Axios HTTP client wrapping REST endpoints (`/api/v1`) with request/response interceptors for token management.

### Backend API Layer (`backend/`)
- Python FastAPI application running asynchronously via Uvicorn.
- Pydantic v2 for payload validation and schema serialization.
- Middleware handles CORS, global error handling, and structured request logging.
- SQLAlchemy 2.0 ORM with Alembic database migrations and platform-independent GUID support.

### Database Layer (`backend/app/db/models/`)
- 30+ relational entity models grouped into modular domains: `user`, `academic`, `question`, `blueprint`, `question_paper`, `answer_key`, `rubric`, `examination`, `file_asset`, `answer_paper`, `evaluation`, `plagiarism`, `analytics`, `audit`.
- Historical snapshot integrity on `QuestionPaperItem` ensuring questions published on exam papers never change retroactively.

### AI Engine Layer (`ai/`)
- Decoupled from core web framework to enable independent scaling and testing.
- Provider abstraction pattern (`BaseLLMProvider`) allows switching between Google Gemini, OpenAI, or local/mock models.
- Specialized agents handle syllabus parsing, question generation, answer key creation, answer evaluation, feedback, and academic insights.
- Document AI pipeline integrates OCR services (`BaseOCRProvider` for Tesseract / EasyOCR abstraction).
