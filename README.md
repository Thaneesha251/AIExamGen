# AI ExamGen — Intelligent Question Paper Generation, Automated Answer Evaluation & Examination Analytics Platform

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/Python-3.14%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-green)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-red)
![React](https://img.shields.io/badge/React-18.2-blue)
![TypeScript](https://img.shields.io/badge/TypeScript-5.0-blue)

AI ExamGen is a complete, enterprise-grade academic examination lifecycle management platform. It automates question paper creation, blueprint verification, structured answer key generation, OCR-based answer sheet extraction, multi-layered NLP/AI answer evaluation, human-in-the-loop mark verification, plagiarism analysis, and comprehensive examination analytics.

---

## 🏛 System Architecture Overview

```text
AIExamGen/
├── frontend/             # React 18 + Vite + TypeScript + Material UI
├── backend/              # Python FastAPI + SQLAlchemy 2.0 + Pydantic v2
│   ├── app/
│   │   ├── api/          # Versioned REST APIs (/api/v1)
│   │   ├── core/         # Security (Direct Bcrypt / PyJWT), Config, Logging
│   │   ├── db/           # Session management, GUID type & Complete ORM Models
│   │   │   └── models/   # 30+ Domain Entities (Users, Academic, Questions, Papers, Evaluation)
│   │   ├── schemas/      # Request & Response Pydantic v2 schemas
│   │   ├── repositories/ # Clean Repository Data Access Layer
│   │   └── services/     # Storage, Auth & Domain Services
│   ├── migrations/       # Alembic Database Migrations
│   └── scripts/          # Seed Database Script (Realistic Academic Data)
├── ai/                   # Modular AI/ML Services Architecture
├── storage/              # Storage abstraction for syllabus PDFs, answer sheets, reports
├── docs/                 # System Architecture, Database ER Diagram & API Documentation
└── tests/                # Automated Test Suites (Pytest)
```

---

## 🚀 Technology Stack

- **Frontend**: React, Vite, TypeScript, Material-UI (MUI), Recharts, Axios, React Router v6
- **Backend**: Python 3.14+, FastAPI, SQLAlchemy 2.0 ORM, Pydantic v2, Alembic, Bcrypt, PyJWT
- **Database**: PostgreSQL (Production) / SQLite (Local Dev Fallback with GUID support)
- **AI & Document Processing**: Generative AI Provider Abstraction (Google Gemini / OpenAI / Mock), scikit-learn, Sentence-Transformers, Tesseract/EasyOCR pipeline

---

## 💻 Local Quickstart Guide (Windows Environment)

### Prerequisites
- Node.js v18+ & npm
- Python 3.11+
- Git

### 1. Backend & Database Setup
```powershell
# Navigate to backend directory
cd backend

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Apply Alembic Migrations
python -m alembic upgrade head

# Seed Database with Realistic Academic Data
python scripts/seed_database.py

# Run Automated Tests
python -m pytest tests/

# Run FastAPI Dev Server
uvicorn app.main:app --reload --port 8000
```
Backend Swagger API Documentation will be live at: `http://localhost:8000/docs`

### 2. Frontend Setup
```powershell
# In a separate terminal, navigate to frontend directory
cd frontend

# Verify TypeScript compilation
npx tsc --noEmit

# Start Vite React Dev Server
npm run dev
```
Frontend web application will be live at: `http://localhost:5173`

---

## 🔑 Development Seed Credentials

| Role | Email | Password | Identifier |
|------|-------|----------|------------|
| **Admin** | `admin@example.com` | `admin123` | `ADM-001` |
| **Faculty** | `faculty@example.com` | `faculty123` | `FAC-001` |
| **Student** | `student1@example.com` | `student123` | `REG2026001` |
| **Student** | `student2@example.com` | `student123` | `REG2026002` |

---

## 📋 Project Status & Roadmap

- [x] **Phase 1**: Architecture & Foundational Setup
- [x] **Phase 2**: Database Architecture, Complete Models, Migrations & Seed Data
- [ ] **Phase 3**: Authentication & RBAC User Management Gateway
- [ ] **Phase 4**: Subject & Syllabus Management Engine
- [ ] **Phase 5**: Question Bank Management System
- [ ] **Phase 6**: AI Question Generation Engine & Duplicate Detection
- [ ] **Phase 7**: Question Paper Blueprint & Generator Engine
- [ ] **Phase 8**: Examination & OCR Answer Sheet Processor
- [ ] **Phase 9**: AI Answer Evaluation Engine (NLP + Rubrics + Similarity)
- [ ] **Phase 10**: Specialized Evaluators, Plagiarism & Human Review Interface
- [ ] **Phase 11**: Analytics Engine, Performance Profiling & AI Insights
- [ ] **Phase 12**: Professional PDF/Excel Reports & Complete Integration
- [ ] **Phase 13**: End-to-End Verification, Security & Final Demo Readiness
