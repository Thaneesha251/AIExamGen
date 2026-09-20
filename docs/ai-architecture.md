# AI ExamGen — AI & Document Processing Architecture

## 1. Hybrid AI Pipeline

AI ExamGen avoids reliance on single unvalidated LLM calls by leveraging a deterministic multi-stage evaluation pipeline:

```text
Student Answer Sheet
       │
       ▼
[ OCR Service ] ──────────► Text Extraction & Page Alignment
       │
       ▼
[ Preprocessing & Segmentation ] ─► Question Identification
       │
       ▼
[ Layer 1: Keyword Coverage ] ────► N-gram & Vocabulary Matching
       │
       ▼
[ Layer 2: Concept Extraction ] ──► Key Concept Matching
       │
       ▼
[ Layer 3: Semantic Similarity ] ─► Cosine / Embedding Vector Similarity
       │
       ▼
[ Layer 4: Pattern Evaluation ] ──► Algorithmic / Structural Rubric Rules
       │
       ▼
[ Layer 5: Score Aggregation ] ───► Confidence Calculation & Partial Credit Mapping
       │
       ▼
[ Human-in-the-Loop Review ] ─────► Faculty Audit & Override Interface
```

## 2. AI Provider Abstraction

All LLM operations inherit from `BaseLLMProvider` located in `ai/services/llm_service.py`. This ensures zero vendor lock-in and seamless model switching via configuration (`AI_PROVIDER="google" | "openai" | "mock"`).
