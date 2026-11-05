# NoteIQ 🎓

> AI-Powered Academic Notes Rating & Discovery Platform for Undergraduate Students & Faculty.

NoteIQ enables students and faculty across undergraduate streams (BBA, BCA, B.Voc) to upload academic notes (PDF, DOCX, PPTX). The platform automatically extracts, evaluates, and rates notes across four academic dimensions with transparent evidence references, while students browse, search, download, review, and query a grounded RAG AI assistant.

---

## 🌟 Key Features

- **Dynamic Catalogue**: Streams (BBA, BCA, B.Voc) and Semesters (1–6, Semester 6 with "Coming Soon" indicator). Subjects and topics appear dynamically once notes are contributed.
- **Multi-Format Extraction**: Ingestion of PDF (PyMuPDF with Tesseract OCR fallback), Word DOCX, and PowerPoint PPTX.
- **AI Academic Evaluation**: Multi-dimensional rubrics (Accuracy, Explanation Quality, Content Depth, Examples & Illustrations) scored from 0–5 in 0.5 increments with exact page/slide citations.
- **Topic Coverage**: Computed strictly against reference syllabus checklists—no hallucinations or invented coverage metrics.
- **Student Reviews vs AI Ratings**: Clear separation between AI analytical benchmarks and peer community star ratings and qualitative reviews.
- **Grounded Assistant (RAG)**: Conversational assistant answering strictly from uploaded notes using hybrid retrieval (Vector Embeddings + BM25 Full-Text Search with Reciprocal Rank Fusion) and parameterized database tools.
- **Safety & Moderation**: Double-submit CSRF protection, Argon2 hashing, signed S3 download URLs, and community flagging with moderator capabilities.

---

## 🏗️ Architecture & Tech Stack

```text
┌────────────────┐          ┌────────────────┐          ┌────────────────┐
│  Next.js 14    │  HTTP    │ FastAPI        │  SQLAlchemy│ PostgreSQL 16  │
│  App Router    ├─────────►│ Backend        ├─────────►│ pgvector + FTS │
│  Tailwind/UI   │  Cookies │ /api/v1        │          └────────────────┘
└────────────────┘          └───┬────────────┘
                                │
                     Enqueues   │ Redis + RQ
                                ▼
                            ┌────────────────┐          ┌────────────────┐
                            │ Background     │  S3 API  │ MinIO / S3 /   │
                            │ Worker         ├─────────►│ Cloudflare R2  │
                            │ (PyMuPDF/AI)   │          └────────────────┘
                            └────────────────┘
```

- **Frontend**: Next.js 14 (App Router), TypeScript, Tailwind CSS, shadcn/ui components, Lucide icons.
- **Backend**: FastAPI, SQLAlchemy 2 (async), Pydantic v2, Alembic.
- **Database**: PostgreSQL 16 with `pgvector` for HNSW vector index and `tsvector` for GIN full-text index.
- **Worker & Queue**: Redis with RQ background queue.
- **Object Storage**: S3-compatible (MinIO for local dev, AWS S3 / Cloudflare R2 for production).
- **AI Provider**: Provider-agnostic abstraction supporting Google Gemini (`gemini-2.5-flash`), OpenAI, Anthropic.

---

## 🚀 Quick Start (Docker Compose)

1. Clone repository and copy environment variables:
   ```bash
   cp .env.example .env
   ```
2. Insert your Google Gemini API key into `.env`:
   ```env
   LLM_API_KEY=your_gemini_api_key_here
   EMBEDDING_API_KEY=your_gemini_api_key_here
   ```
3. Boot the complete stack:
   ```bash
   docker compose up --build
   ```
4. Access services:
   - **Frontend**: `http://localhost:3000`
   - **Backend API**: `http://localhost:8000/docs`
   - **MinIO Console**: `http://localhost:9001` (User: `minioadmin`, Pass: `minioadmin`)

---

## 🧪 Running Tests

### Backend Tests
```bash
cd backend
pytest tests/ -v
```

### Frontend Tests
```bash
cd frontend
npm run test:run
```

---

## 📜 License
MIT License. Built with clean, reliable architecture.
