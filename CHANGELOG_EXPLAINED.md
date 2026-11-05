# NoteIQ — Architecture Decisions & Interview Cheatsheet

This document provides a concise architectural guide and interview cheatsheet for **NoteIQ (Ai_Notes_Rating_System)**, explaining key technical choices in simple, direct language.

---

## 1. Project Overview & Business Value

| Property | Details |
|---|---|
| **Core Concept** | AI-powered academic notes evaluation, rubric scoring, and RAG discovery platform for undergraduate students (BCA, BBA, B.Voc). |
| **Backend Stack** | Python, FastAPI, SQLAlchemy 2 (async), Pydantic v2, Alembic |
| **Database** | PostgreSQL 16 with `pgvector` (vector embeddings) and `tsvector` (full-text search) |
| **Background Processing**| Redis + RQ worker queue for async OCR extraction (PyMuPDF / Tesseract) |
| **Frontend Stack** | Next.js 14 (App Router), TypeScript, Tailwind CSS, shadcn/ui components |
| **Object Storage** | S3-compatible storage (MinIO for local development, AWS S3 for production) |
| **Security & Auth** | Double-submit CSRF protection, Argon2 password hashing, rate limiting, and signed download URLs |

---

## 2. Key Architecture Decisions

### 1. Multi-Dimensional Rubric-Based Evaluation (No Hallucinated Scores)
- Rather than asking an LLM for an arbitrary "1-10" rating, NoteIQ evaluates academic notes across **4 strict dimensions** (Accuracy, Explanation Quality, Content Depth, and Examples/Illustrations) scored from 0.0 to 5.0 with exact page citations and syllabus checklist cross-referencing.

### 2. Hybrid Search (pgvector + PostgreSQL Full-Text Search)
- Notes discovery combines dense semantic vector search with keyword-based full-text indexing to ensure students find both conceptual topic matches and exact technical terms.

### 3. Asynchronous Worker Architecture
- Ingesting 50-page lecture slides with OCR takes 5–15 seconds. Processing this in the main API request would block HTTP threads and lead to request timeouts. NoteIQ enqueues file parsing tasks into a **Redis RQ worker queue**, returning an immediate tracking ID to the frontend.

---

## 3. Technical Interview Cheatsheet

### Q: Why did you separate the background worker from the main FastAPI server?
> **Answer:** "Document extraction (PDF parsing with OCR fallback and generating chunk embeddings) is CPU- and I/O-intensive. If executed synchronously inside API endpoints, it would exhaust FastAPI's worker threads and degrade response latency for other users. Decoupling extraction via Redis and background workers ensures the API remains responsive."
