"""
Optional NoteIQ Demo Data Script.
Creates realistic sample documents, evaluations, chunks, and student reviews
for demonstration and UI inspection across BCA, BBA, and B.Voc streams.
Clearly separate from core seed reference data.
"""

import os
import sys
import uuid
from datetime import datetime, timezone

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.core.normalizer import normalize_name
from app.core.security import hash_password
from app.db.models import (
    AnalysisFeedback,
    AnalysisTopic,
    Document,
    DocumentAnalysis,
    DocumentChunk,
    Review,
    Semester,
    Stream,
    Subject,
    SyllabusTopic,
    Topic,
    User,
)
from app.db.session import SyncSessionLocal
from app.services.embeddings import embedding_service
from app.services.scoring import calculate_overall_scores, calculate_topic_coverage


def populate_demo_data():
    db = SyncSessionLocal()
    try:
        print("[DEMO] Checking existing reference streams and semesters...")
        bca = db.query(Stream).filter(Stream.slug == "bca").first()
        bba = db.query(Stream).filter(Stream.slug == "bba").first()
        sem1 = db.query(Semester).filter(Semester.number == 1).first()
        sem2 = db.query(Semester).filter(Semester.number == 2).first()

        if not bca or not sem1:
            print("[ERROR] Please run `python scripts/seed_reference_data.py` first.")
            return

        # 1. Demo Users
        faculty = db.query(User).filter(User.email == "prof.sharma@college.edu").first()
        if not faculty:
            faculty = User(
                name="Prof. Rajesh Sharma",
                email="prof.sharma@college.edu",
                password_hash=hash_password("DemoPassword123!"),
                role="faculty",
            )
            db.add(faculty)
            db.flush()

        student = db.query(User).filter(User.email == "aarav.patel@student.edu").first()
        if not student:
            student = User(
                name="Aarav Patel",
                email="aarav.patel@student.edu",
                password_hash=hash_password("DemoPassword123!"),
                role="student",
            )
            db.add(student)
            db.flush()

        # 2. Demo Subject & Syllabus Checklist
        subj_name = "C Programming & Problem Solving"
        subj_norm = normalize_name(subj_name)
        subject = db.query(Subject).filter(Subject.normalized_name == subj_norm).first()
        if not subject:
            subject = Subject(
                stream_id=bca.id,
                semester_id=sem1.id,
                name=subj_name,
                normalized_name=subj_norm,
                created_by=faculty.id,
            )
            db.add(subject)
            db.flush()

            # Add syllabus checklist
            checklist = ["Pointers", "Dynamic Memory", "Structures", "File Handling", "Recursion"]
            for c_item in checklist:
                db.add(SyllabusTopic(subject_id=subject.id, name=c_item, added_by=faculty.id))
            db.flush()

        # 3. Demo Topic
        topic_name = "Pointers & Memory Allocation"
        topic_norm = normalize_name(topic_name)
        topic = db.query(Topic).filter(Topic.normalized_name == topic_norm, Topic.subject_id == subject.id).first()
        if not topic:
            topic = Topic(subject_id=subject.id, name=topic_name, normalized_name=topic_norm)
            db.add(topic)
            db.flush()

        # 4. Demo Document
        doc = db.query(Document).filter(Document.topic_id == topic.id).first()
        if not doc:
            doc = Document(
                id=uuid.uuid4(),
                subject_id=subject.id,
                topic_id=topic.id,
                uploader_id=faculty.id,
                title="Pointers, Addresses, and Dynamic Memory in C",
                description="Comprehensive lecture slides explaining memory addresses, dereferencing, malloc, calloc, and free with diagrams.",
                file_key=f"demo/pointers_{uuid.uuid4().hex[:8]}.pdf",
                original_filename="Pointers_and_Memory.pdf",
                file_type="pdf",
                file_size=1024 * 450,
                checksum_sha256="demo_checksum_" + uuid.uuid4().hex,
                status="complete",
                download_count=42,
            )
            db.add(doc)
            db.flush()

            # Chunks
            sample_chunks = [
                ("Page 1", "Pointers are variables that store the memory address of another variable. In C, we declare a pointer using the asterisk symbol (*). For example: int *ptr = &num; where & is the address-of operator."),
                ("Page 2", "Dynamic memory allocation in C is handled via stdlib.h. malloc(size_t size) allocates contiguous bytes on the heap. calloc(size_t n, size_t size) allocates and zeroes out memory. Every allocation must be paired with free(ptr)."),
            ]
            embeddings = embedding_service.embed_texts([c[1] for c in sample_chunks])
            for i, (loc, txt) in enumerate(sample_chunks):
                db.add(DocumentChunk(
                    id=uuid.uuid4(),
                    document_id=doc.id,
                    chunk_index=i,
                    location=loc,
                    text=txt,
                    embedding=embeddings[i],
                ))

            # Analysis
            acc, exp, dep, exm = 4.5, 4.5, 4.0, 4.5
            raw, disp = calculate_overall_scores(acc, exp, dep, exm)
            analysis = DocumentAnalysis(
                id=uuid.uuid4(),
                document_id=doc.id,
                version=1,
                rubric_version="v1",
                model_name="gemini-2.5-flash",
                topic_coverage_pct=40.0,
                accuracy_score=acc,
                explanation_score=exp,
                depth_score=dep,
                examples_score=exm,
                overall_score_raw=raw,
                overall_score_display=disp,
                confidence="high",
                confidence_reason="Crystal clear syntax, correct pointer arithmetic diagrams, verified worked examples.",
                summary="Rigorous undergraduate notes detailing pointer mechanics, memory models, and heap allocations with clean illustrative C code.",
                total_topics=2,
            )
            db.add(analysis)
            db.flush()

            # Feedback
            db.add(AnalysisTopic(analysis_id=analysis.id, topic_name="Pointer Mechanics", note="Address-of and dereferencing."))
            db.add(AnalysisTopic(analysis_id=analysis.id, topic_name="Heap Allocation", note="malloc, calloc, and free."))
            db.add(AnalysisFeedback(analysis_id=analysis.id, kind="strength", text="Excellent step-by-step memory layout diagrams."))
            db.add(AnalysisFeedback(analysis_id=analysis.id, kind="strength", text="Comprehensive memory leak warnings with free()."))
            db.add(AnalysisFeedback(analysis_id=analysis.id, kind="improvement", text="Include function pointers and void pointer casting."))
            db.add(AnalysisFeedback(analysis_id=analysis.id, kind="missing_concept", text="Dangling pointers and memory fragmentation."))

            # Reviews
            db.add(Review(
                document_id=doc.id,
                user_id=student.id,
                stars=5,
                comment="Helped me ace my mid-term exam! The heap vs stack comparison is super clear.",
            ))

        db.commit()
        print("[SUCCESS] Demo data populated successfully!")
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Failed to populate demo data: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    populate_demo_data()
