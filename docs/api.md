# AI ExamGen — REST API Documentation

## Base URL
All API endpoints are versioned under `/api/v1`.

---

## 1. Authentication & Users
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/auth/login` | Authenticate user & get JWT bearer token |
| `GET` | `/api/v1/auth/me` | Fetch current authenticated user profile |
| `POST` | `/api/v1/auth/register` | Public student self-registration |
| `GET` | `/api/v1/users` | Admin user listing & filtering |
| `PUT` | `/api/v1/users/{id}/role` | Admin role assignment |

---

## 2. Exam Blueprints & Rules (Phase 6)
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/blueprints` | Create exam blueprint with section rules & distributions |
| `GET` | `/api/v1/blueprints` | List blueprints by subject/status |
| `GET` | `/api/v1/blueprints/{id}` | Get blueprint details & validation summary |
| `PUT` | `/api/v1/blueprints/{id}` | Update blueprint & rules |
| `DELETE` | `/api/v1/blueprints/{id}` | Delete or archive blueprint |
| `POST` | `/api/v1/blueprints/{id}/validate` | Validate rules, mark totals, and question bank pool |

---

## 3. Question Papers & Generation (Phase 6 & 7)
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/question-papers/generate` | Deterministic AI question paper generation using seed |
| `GET` | `/api/v1/question-papers` | List question papers |
| `GET` | `/api/v1/question-papers/{id}` | Get paper details & active version items |
| `POST` | `/api/v1/question-papers/{id}/replace-question` | Replace single question (creates version vN+1) |
| `POST` | `/api/v1/question-papers/{id}/regenerate-section` | Regenerate paper section (creates version vN+1) |
| `POST` | `/api/v1/question-papers/{id}/regenerate` | Full paper regeneration with new seed (creates version vN+1) |

---

## 4. Answer Keys & AI Drafting (Phase 7)
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/question-papers/versions/{ver_id}/answer-key/generate` | Generate initial answer key from paper version snapshots |
| `GET` | `/api/v1/question-papers/versions/{ver_id}/answer-key` | Fetch latest answer key for paper version |
| `PUT` | `/api/v1/answer-keys/{id}` | Edit model answers, keywords, marking notes (versioned) |
| `POST` | `/api/v1/answer-keys/{id}/validate` | Validate completeness and mark consistency |

---

## 5. Evaluation Rubrics (Phase 7)
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/rubrics` | Create evaluation rubric with weighted criteria |
| `GET` | `/api/v1/rubrics` | List rubrics by subject/type |
| `GET` | `/api/v1/rubrics/{id}` | Get rubric details |
| `PUT` | `/api/v1/rubrics/{id}` | Update rubric criteria |
| `DELETE` | `/api/v1/rubrics/{id}` | Delete rubric |
| `POST` | `/api/v1/rubrics/{id}/assign` | Assign rubric to question / answer key item |

---

## 6. Faculty Review, Approval & Export (Phase 7)
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/question-papers/{id}/review` | Fetch review checklist and validation summary |
| `POST` | `/api/v1/question-papers/{id}/approve` | Faculty paper & answer key approval |
| `POST` | `/api/v1/question-papers/{id}/publish` | Publish paper & freeze version immutability |
| `GET` | `/api/v1/question-papers/{id}/export/pdf` | Download print-ready Question Paper PDF |
| `GET` | `/api/v1/question-papers/{id}/answer-key/export/pdf` | Download Faculty Answer Key PDF (Faculty only) |
