# AI ExamGen — Faculty Human-in-the-Loop Review & Result Finalization

## 1. Overview & Core Philosophy

In **AI ExamGen**, the AI evaluation engine serves as an intelligent grading assistant, but the **faculty member remains the final academic authority**. 

AI-suggested marks are never automatically published as final student grades without passing through the human-in-the-loop review pipeline.

---

## 2. Review State Machine

An evaluation progresses through the following strict state transitions:

```text
       PENDING
          ↓
      PROCESSING
          ↓
      COMPLETED
          ↓
    UNDER_REVIEW  ←────── (Item Accepted / Overridden / Re-evaluated)
          ↓
       APPROVED   ←────── (All Items Reviewed + Review Completeness Enforced)
          ↓
      FINALIZED   ←────── (Marks Locked + Student Paper Status Set to FINALIZED)
          ↓
       REOPENED   ←────── (Admin Only Reopening for Dispute Investigation)
```

---

## 3. Human-in-the-Loop Decision Options

For every evaluated question item, faculty can execute one of three explicit decisions:

1. **Accept AI Mark (`ACCEPT_AI_MARK`)**
   - Sets `final_marks = ai_marks` and `review_status = "ACCEPTED"`.
   - Records optional faculty comment.

2. **Manual Mark Override (`OVERRIDE_MARK`)**
   - Allows faculty to enter a revised final mark (`0.0 <= final_marks <= maximum_marks`).
   - Requires a mandatory override reason (minimum 10 characters).
   - Preserves original `ai_marks` intact for historical comparison.

3. **Request AI Re-Evaluation (`REQUEST_REEVALUATION`)**
   - Re-evaluates a single question or paper when OCR or key mapping changes.
   - Generates a new evaluation version (`v1 -> v2`), preserving all previous evaluation and review versions in history.

4. **Bulk Accept High-Confidence (`BULK_AI_MARKS_ACCEPTED`)**
   - Accepts all eligible items where `confidence >= 0.65` and `requires_faculty_review == False` in one click.

---

## 4. Finalization & Lock Safeguards

- **Review Completeness Check:** An evaluation cannot be transitioned to `APPROVED` or `FINALIZED` if any question item remains in `PENDING` review status.
- **Server-Side Mark Recalculation:** `evaluation.total_final_marks` is automatically computed server-side as `SUM(item.final_marks)` and validated against total paper maximum marks.
- **Immutable Lock:** Once an evaluation reaches `FINALIZED` status:
  - Faculty review endpoints reject modifications (`400 Bad Request`).
  - Answer paper status transitions to `FINALIZED`.
  - Reopening is restricted strictly to `ADMIN` users with a mandatory administrative reason.

---

## 5. Audit Logging & Security

Every faculty decision is logged to the immutable `audit_logs` table:
- `AI_MARK_ACCEPTED`
- `MARK_OVERRIDDEN`
- `REEVALUATION_REQUESTED`
- `EVALUATION_APPROVED`
- `EVALUATION_FINALIZED`
- `EVALUATION_REOPENED`
- `BULK_AI_MARKS_ACCEPTED`

**RBAC & Ownership:**
- **FACULTY:** Access restricted to examinations and subjects assigned/authorized to them. Attempts to access unauthorized papers return `403 Forbidden`.
- **STUDENT:** Blocked from all evaluation review and modification endpoints (`403 Forbidden`).
