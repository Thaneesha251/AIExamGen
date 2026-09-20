# AI ExamGen — Answer Key & Rubric Workflow Guide

## Overview

Phase 7 introduces complete Answer Key Management, Rubric Engine, Faculty Review & Approval/Publish Lifecycle, and Print-Ready PDF Exports for AI ExamGen.

---

## Architecture & Workflow

```text
QuestionPaper
    │
    └── QuestionPaperVersion (Immutable Historical Snapshot)
            │
            ├── QuestionPaperItems (Text, Options, Type, Difficulty, Bloom, Marks)
            │
            └── AnswerKey (Version 1, Version 2...)
                    │
                    ├── AnswerKeyItems (Model Answer, Keywords, Concepts, Marking Notes)
                    │       │
                    │       └── Linked Rubric (Criteria, Weights, Partial Credit Rules)
                    │
                    └── AuditLog (ANSWER_KEY_CREATED, PAPER_APPROVED, PAPER_PUBLISHED)
```

---

## Key Features

1. **Answer Key Generation**: Automatically populates `AnswerKeyItem` entries from `QuestionPaperVersion` question snapshots and expected answers.
2. **Faculty Review Checklist**: Evaluates blueprint validity, question paper marks integrity, duplicate prevention, answer key coverage, and rubric compatibility.
3. **Immutability & Versioning**: Editing model answers or questions on approved/published paper versions generates a new version (`vN+1`) without altering historical snapshots.
4. **Professional PDF Export**:
   - **Question Paper PDF**: Print-ready exam format with institution header, instructions, sections, question layout, and options.
   - **Faculty Answer Key PDF**: Confidential faculty guide with model answers, keywords, marking guidance, and rubrics.
