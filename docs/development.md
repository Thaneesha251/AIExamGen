# AI ExamGen — Development & Database Guide

## 1. Local Windows Development Setup

### Backend Setup
```powershell
# Navigate to backend directory
cd backend

# Create virtual environment (if not already created)
py -m venv .venv

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Install requirements
pip install -r requirements.txt

# Run Alembic Database Migrations
python -m alembic upgrade head

# Seed Database with Realistic Academic Data
python scripts/seed_database.py

# Run Pytest Verification Suite
python -m pytest tests/

# Run FastAPI Local Server
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup
```powershell
# Navigate to frontend directory
cd frontend

# Install Node dependencies
npm install

# Check TypeScript types
npx tsc --noEmit

# Run Vite Dev Server
npm run dev
```

---

## 2. Database Commands & Safety Notes

### Alembic Migrations
- Check current revision: `python -m alembic current`
- View migration history: `python -m alembic history`
- Apply migrations: `python -m alembic upgrade head`

### Seed Credentials
- **Admin**: `admin@example.com` / `admin123`
- **Faculty**: `faculty@example.com` / `faculty123`
- **Student**: `student1@example.com` / `student123`
