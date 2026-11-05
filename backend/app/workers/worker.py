"""
NoteIQ Worker: Background Document Analysis Pipeline.
Performs file download, extraction, chunking, embedding, academic rubric evaluation,
and saves results with automatic retry.
"""

import sys
import time
import uuid
from typing import Optional
from sqlalchemy import delete, select
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.logging import logger
from app.db.models import (
    AnalysisFeedback,
    AnalysisTopic,
    Document,
    DocumentAnalysis,
    DocumentChunk,
    Subject,
    SyllabusTopic,
)
from app.db.session import get_sync_db
from app.services.analysis import evaluate_document_notes
from app.services.chunking import chunk_extracted_units
from app.services.embeddings import embedding_service
from app.services.extraction import extract_document_text
from app.services.storage import storage_service


def process_document_job(document_id: str, max_retries: int = 3) -> bool:
    """
    Main background job executed by worker or async pipeline.
    Retries up to max_retries on transient failures.
    """
    doc_uuid = uuid.UUID(document_id)
    attempt = 0

    while attempt < max_retries:
        attempt += 1
        db = get_sync_db()
        try:
            logger.info(f"[WORKER] Starting analysis for document {document_id} (Attempt {attempt}/{max_retries})")

            # 1. Fetch document and related metadata
            stmt = (
                select(Document)
                .where(Document.id == doc_uuid)
                .options(
                    selectinload(Document.subject).selectinload(Subject.stream),
                    selectinload(Document.subject).selectinload(Subject.semester),
                    selectinload(Document.subject).selectinload(Subject.syllabus_topics),
                    selectinload(Document.topic),
                )
            )
            doc = db.execute(stmt).scalar_one_or_none()
            if not doc:
                logger.error(f"[WORKER] Document {document_id} not found in database.")
                return False

            # Set status to processing
            doc.status = "processing"
            doc.failure_reason = None
            db.commit()

            # 2. Download file from storage
            file_bytes = storage_service.download_file_bytes(doc.file_key)

            # Optional ClamAV scan if enabled
            if settings.CLAMAV_ENABLED:
                logger.info(f"[WORKER] ClamAV scan enabled - scanning {doc.original_filename}")

            # 3. Extract text units (PDF/DOCX/PPTX)
            extraction = extract_document_text(doc.file_type, file_bytes)
            if extraction.failure_reason:
                doc.status = "failed"
                doc.failure_reason = extraction.failure_reason
                db.commit()
                logger.warning(f"[WORKER] Document {document_id} extraction failed: {extraction.failure_reason}")
                return False

            # 4. Chunk text and generate embeddings
            chunks = chunk_extracted_units(extraction.units)
            chunk_texts = [c.text for c in chunks]
            embeddings = embedding_service.embed_texts(chunk_texts)

            # Delete any existing chunks for re-analysis
            db.execute(delete(DocumentChunk).where(DocumentChunk.document_id == doc.id))

            for idx, c in enumerate(chunks):
                emb = embeddings[idx] if idx < len(embeddings) else None
                # Store chunk with embedding vector
                chunk_record = DocumentChunk(
                    id=uuid.uuid4(),
                    document_id=doc.id,
                    chunk_index=c.chunk_index,
                    location=c.location,
                    text=c.text,
                    embedding=emb,
                )
                db.add(chunk_record)
            db.flush()

            # 5. Get syllabus checklist if exists
            checklist = [st.name for st in doc.subject.syllabus_topics] if doc.subject.syllabus_topics else None

            # 6. Run Academic Evaluation
            eval_result = evaluate_document_notes(
                units=extraction.units,
                stream=doc.subject.stream.name if doc.subject.stream else "Undergraduate",
                semester=doc.subject.semester.number if doc.subject.semester else 1,
                subject=doc.subject.name,
                topic=doc.topic.name,
                syllabus_checklist=checklist,
                is_low_confidence_extraction=extraction.is_low_confidence,
            )

            # 7. Increment version if re-analysis
            prev_version_stmt = select(DocumentAnalysis.version).where(DocumentAnalysis.document_id == doc.id).order_by(DocumentAnalysis.version.desc())
            latest_version = db.execute(prev_version_stmt).scalars().first() or 0
            new_version = latest_version + 1

            # Save Analysis Record
            analysis = DocumentAnalysis(
                id=uuid.uuid4(),
                document_id=doc.id,
                version=new_version,
                rubric_version=eval_result["rubric_version"],
                model_name=eval_result["model_name"],
                topic_coverage_pct=eval_result["topic_coverage_pct"],
                accuracy_score=eval_result["accuracy_score"],
                explanation_score=eval_result["explanation_score"],
                depth_score=eval_result["depth_score"],
                examples_score=eval_result["examples_score"],
                overall_score_raw=eval_result["overall_score_raw"],
                overall_score_display=eval_result["overall_score_display"],
                confidence=eval_result["confidence"],
                confidence_reason=eval_result["confidence_reason"],
                summary=eval_result["summary"],
                total_topics=eval_result["total_topics"],
                raw_json=eval_result["raw_json"],
            )
            db.add(analysis)
            db.flush()

            # Save Topics
            for t in eval_result["topics_identified"]:
                top_name = t.get("name", "Topic") if isinstance(t, dict) else str(t)
                top_note = t.get("note", "") if isinstance(t, dict) else ""
                db.add(AnalysisTopic(
                    id=uuid.uuid4(),
                    analysis_id=analysis.id,
                    topic_name=top_name,
                    note=top_note,
                ))

            # Save Feedback (strengths, improvements, missing_concepts, errors)
            for s in eval_result.get("strengths", []):
                db.add(AnalysisFeedback(id=uuid.uuid4(), analysis_id=analysis.id, kind="strength", text=str(s)))
            for imp in eval_result.get("improvements", []):
                db.add(AnalysisFeedback(id=uuid.uuid4(), analysis_id=analysis.id, kind="improvement", text=str(imp)))
            for mc in eval_result.get("missing_concepts", []):
                db.add(AnalysisFeedback(id=uuid.uuid4(), analysis_id=analysis.id, kind="missing_concept", text=str(mc)))
            for err in eval_result.get("errors_found", []):
                err_text = err.get("description", str(err)) if isinstance(err, dict) else str(err)
                err_loc = err.get("location") if isinstance(err, dict) else None
                db.add(AnalysisFeedback(id=uuid.uuid4(), analysis_id=analysis.id, kind="error_found", text=err_text, evidence_ref=err_loc))

            # 8. Mark document as complete
            doc.status = "complete"
            doc.failure_reason = None
            db.commit()

            logger.info(f"[WORKER] Successfully analysed document {document_id}: Rating {eval_result['overall_score_display']}/5.0")
            return True

        except Exception as e:
            db.rollback()
            logger.exception(f"[WORKER] Error analysing document {document_id} on attempt {attempt}: {e}")
            if attempt >= max_retries:
                # Mark as failed permanently with readable reason
                try:
                    fail_db = get_sync_db()
                    failed_doc = fail_db.get(Document, doc_uuid)
                    if failed_doc:
                        failed_doc.status = "failed"
                        failed_doc.failure_reason = f"Processing error during AI evaluation: {str(e)[:200]}"
                        fail_db.commit()
                        fail_db.close()
                except Exception:
                    pass
                return False
            time.sleep(2 ** attempt)
        finally:
            db.close()

    return False


def start_worker():
    """Runs standard RQ worker listening on document_analysis queue."""
    import redis
    from rq import Worker, Queue, Connection
    listen = ["document_analysis"]
    conn = redis.from_url(settings.REDIS_URL)
    with Connection(conn):
        worker = Worker(map(Queue, listen))
        logger.info("[WORKER] RQ Worker started. Listening on 'document_analysis'...")
        worker.work()


if __name__ == "__main__":
    start_worker()
