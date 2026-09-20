# Answer Similarity & Plagiarism Detection Engine

## Overview
Phase 11 introduces a multi-signal pairwise similarity detection system for evaluated student answer papers within an examination.
The engine calculates lexical (N-gram overlap & TF-IDF similarity) and semantic (embedding cosine similarity) distance between all student responses submitted for the same question.

> [!IMPORTANT]
> **Faculty-In-The-Loop Principle:** Similarity detection yields `FLAGGED FOR FACULTY REVIEW` status or low similarity scores. The system **NEVER** issues automatic academic misconduct or cheating verdicts. All decisions rest with authorized faculty members.

## Multi-Signal Algorithm
For each question item \(Q\) across all finalized student answer papers:
1. **Lexical N-Gram Jaccard Index:** Computes 3-gram character set overlap between Answer \(A_i\) and Answer \(A_j\).
2. **Lexical TF-IDF Cosine Similarity:** Vectorizes unigrams/bigrams across responses for question \(Q\) and computes cosine dot product.
3. **Semantic Embedding Cosine Similarity:** Computes cosine similarity of normalized answer vector embeddings (or high-level semantic representation).
4. **Combined Similarity Score:**
   \[
   S_{ij} = w_{ngram} \cdot S_{ngram} + w_{tfidf} \cdot S_{tfidf} + w_{semantic} \cdot S_{semantic}
   \]

## Thresholds & Aggregation
- **Item Threshold (`similarity_threshold`):** Default `0.75`. Answers exceeding this threshold are flagged in `AnswerSimilarity`.
- **Paper Threshold (`plagiarism_threshold`):** Default `0.70`. Answer papers with overall aggregated similarity exceeding this threshold produce a `PlagiarismResult` record.
- **Review Actions:** Faculty can review a flagged `PlagiarismResult` case and mark it `REVIEWED` (with optional notes) or `DISMISSED`.

## API Endpoints
- `POST /api/v1/plagiarism/examinations/{examination_id}/analyze`: Triggers multi-signal analysis for an exam.
- `GET /api/v1/plagiarism/examinations/{examination_id}/summary`: Returns exam-level plagiarism aggregate summary.
- `GET /api/v1/plagiarism/answer-papers/{answer_paper_id}`: Gets plagiarism result for a single student paper.
- `GET /api/v1/plagiarism/answer-papers/{answer_paper_id}/similarities`: Returns pairwise answer similarity details.
- `POST /api/v1/plagiarism/results/{result_id}/review`: Faculty review action (confirm review or dismiss case).
