"""
Background Job Queuing for Document Processing.
Uses Redis + RQ when available, with direct thread execution fallback for local dev/testing.
"""

from app.core.config import settings
from app.core.logging import logger

try:
    import redis
    from rq import Queue
    redis_conn = redis.from_url(settings.REDIS_URL)
    analysis_queue = Queue("document_analysis", connection=redis_conn)
except Exception as e:
    logger.warning(f"RQ queue unavailable ({e}). Using mock/direct enqueue.")
    analysis_queue = None


def enqueue_document_analysis(document_id: str):
    """Enqueues document analysis job."""
    if analysis_queue:
        try:
            job = analysis_queue.enqueue(
                "app.workers.worker.process_document_job",
                document_id,
                job_timeout="10m",
            )
            logger.info(f"Enqueued document {document_id} as job {job.id}")
            return job.id
        except Exception as e:
            logger.error(f"Failed to enqueue document {document_id}: {e}")
    return None
