# NoteIQ 🎓

> **AI-Powered Academic Notes Rating, Discovery & Active Learning Platform**  
> Designed for Undergraduate Students & Faculty across BBA, BCA, and B.Voc streams.

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-14_App_Router-000000?style=flat&logo=next.js&logoColor=white)](https://nextjs.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16_+_pgvector-336791?style=flat&logo=postgresql&logoColor=white)](https://www.postgresql.org)
[![Gemini](https://img.shields.io/badge/Google_Gemini-2.5_Flash-4285F4?style=flat&logo=google&logoColor=white)](https://ai.google.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-3178C6?style=flat&logo=typescript&logoColor=white)](https://www.typescriptlang.org)
[![TailwindCSS](https://img.shields.io/badge/TailwindCSS-3.4+-38B2AC?style=flat&logo=tailwind-css&logoColor=white)](https://tailwindcss.com)

---

## 🔑 Demo Access Credentials

To test the platform locally or in evaluation mode, use these pre-seeded demo accounts:

| Role | Email | Password | Access Rights |
|---|---|---|---|
| **Student** | `arjun.patel@student.edu.in` | `DemoPassword123!` | Browse, Download, Flashcards, Mind Map, Viva, Reviews |
| **Faculty / Admin** | `faculty.admin@university.edu` | `DemoPassword123!` | Upload Notes, Edit Syllabus, Flag Moderation |

---

## 🌟 The 10 AI Active Learning Innovations

Beyond standard note repository features, NoteIQ introduces **10 cutting-edge pedagogical tools** that transform static PDF notes into interactive, science-backed learning tools:

### 1. 🎴 Concept Flashcards & Active Recall Quiz
- **Flip Cards**: 3D interactive flashcards with front concept and back breakdown.
- **Active Recall Quiz**: 4-option randomized multiple-choice quiz with immediate rationales and final percentage scores.

### 2. 🎯 University Exam Question Predictor (2M / 5M / 10M)
- Predicts likely semester exam questions divided strictly by university weightages:
  - **2-Mark**: Rapid definitions and core formulas.
  - **5-Mark**: Intermediate explanations and component distinctions.
  - **10-Mark**: Comprehensive essays with mandatory diagram checklists.

### 3. 🕸️ Interactive Concept Mind Map & Visual Flowcharts
- Powered by client-side **Mermaid.js**.
- Generates dynamic relational trees showing core roots, subtopics, and structural dependencies across the subject.

### 4. 💡 Multi-Level Simplifier (ELI5, Hinglish, Industry, Jargon)
- **ELI5 (Like I'm 5)**: Everyday intuitive analogies without academic jargon.
- **College Hinglish**: Conversational Indian college Hindi-English blend for relatable explanations.
- **Industry Application**: Practical production/business use-case in tech and management.
- **Jargon Busters**: Side-by-side vocabulary dictionary.

### 5. 🧭 Syllabus Gap & Completeness Heatmap
- Objectively cross-references note contents against the university's reference curriculum.
- Displays a completeness score (%) and explicitly lists **Missing Topics** to prevent exam surprises.

### 6. 🎙️ NotebookLM-Style 2-Host AI Audio Study Podcast
- Synthesizes a natural, back-and-forth conversational dialogue between Host Alex and Subject Specialist Sam.
- Integrated with browser-native Web Speech synthesis for real-time spoken audio without paid API keys.

### 7. 📄 1-Page Printable Exam Formula & Revision Cheat Sheet
- Printable A4 summary with formulas, key definitions, comparison tables, rapid mnemonics, and common exam traps.
- Print-optimized CSS (`@media print`) for 1-click clean paper handouts.

### 8. 🎓 AI Viva Voce / Oral Exam Simulator
- External University Examiner persona with difficulty scaling (`Easy`, `Medium`, `Hard`).
- **Voice Readout**: Examiner questions spoken aloud.
- **Microphone Dictation**: Students answer via microphone speech-to-text or typing.
- **Live Examiner Grading**: Instant score (/10), identified strengths, missing technical points, and a model 10/10 answer.

### 9. 📅 7-Day Spaced Repetition Exam Study Planner
- Implements the **Ebbinghaus Forgetting Curve** across 7 structured days:
  - Days 1-3: Foundations & Deep Dive
  - Day 4: 1st Spaced Review & Quiz
  - Day 5: 10-Mark University Mastery
  - Day 6: 2nd Spaced Review & Viva Probing
  - Day 7: Mock Sprint & Final Formula Cramming
- Interactive task checkboxes with automatic `localStorage` progress persistence.

### 10. 📖 Interactive Note Reader with Floating Highlight Assist
- Distraction-free reading paper mode with font scaling and section navigation.
- **Floating Action Pill**: Highlight any text on the screen to trigger an instant popover for **ELI5**, **Hinglish**, **Exam Trap**, or **Save to Personal Highlights**.
- Export saved highlights to Markdown (`.md`).

---

## 🏛️ Core Platform Capabilities

- **Dynamic Catalogue**: Streams (BBA, BCA, B.Voc) and Semesters (1–6).
- **Multi-Format Extraction**: Ingests PDF (PyMuPDF with Tesseract OCR fallback), DOCX, and PPTX.
- **4-Dimensional AI Academic Rubric**: Evaluates notes objectively on **Accuracy**, **Explanation Quality**, **Content Depth**, and **Examples/Illustrations** (0–5 in 0.5 increments with exact page citations).
- **Grounded Assistant (RAG)**: Multi-turn conversational assistant with hybrid retrieval (Vector Embeddings + BM25 Full-Text Search with Reciprocal Rank Fusion) and parameterized database tools.
- **Safety & Moderation**: Double-submit CSRF tokens, Argon2 password hashing, signed S3 download URLs, and community flagging with moderator approval.

---

## 🏗️ System Architecture

```text
┌─────────────────────────┐          ┌──────────────────────────┐          ┌────────────────────────┐
│  Next.js 14 Frontend    │  HTTP    │ FastAPI Backend Service  │SQLAlchemy│ PostgreSQL 16          │
│  - App Router           ├─────────►│ - REST Endpoints (/v1)   ├─────────►│ - pgvector (HNSW)      │
│  - Web Speech Engine    │ Cookies  │ - Gemini 2.5 Flash LLM   │          │ - tsvector (GIN FTS)   │
│  - Mermaid.js Visuals   │          │ - Heuristic Fallback     │          └────────────────────────┘
└─────────────────────────┘          └────────────┬─────────────┘
                                                  │
                                       Enqueues   │ Redis + RQ
                                                  ▼
                                      ┌──────────────────────────┐          ┌────────────────────────┐
                                      │ Background Worker        │  S3 API  │ MinIO / S3 /           │
                                      │ - PyMuPDF Extraction     ├─────────►│ Cloudflare R2          │
                                      │ - Rubric Evaluation Job  │          │ (Encrypted File Store) │
                                      └──────────────────────────┘          └────────────────────────┘
```

---

## 🚀 Quick Start (Local Development)

### 1. Backend Setup
```bash
cd backend
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000` in your browser.

---

## 🧪 Automated Testing

### Backend Unit & Integration Tests (Pytest)
```bash
cd backend
python -m pytest tests/ -v
```
*(All 19 innovation and core tests pass with 100% success rate)*

### Frontend TypeScript Verification
```bash
cd frontend
npm run type-check
```
*(Verified with 0 TypeScript compilation errors)*

---

## 📜 License
MIT License. Built with clean, reliable, and production-grade architecture.
