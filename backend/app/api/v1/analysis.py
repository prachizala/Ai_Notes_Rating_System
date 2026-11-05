"""
Document Analysis endpoints: View Full Academic Evaluation and Trigger Re-analysis.
"""

import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import check_resource_owner, get_current_user
from app.db.models import Document, DocumentAnalysis, User
from app.db.session import get_db
from app.schemas.analysis import DocumentAnalysisReportResponse
from app.workers.jobs import enqueue_document_analysis

router = APIRouter(prefix="/documents", tags=["Analysis"])


@router.get("/{document_id}/analysis", response_model=DocumentAnalysisReportResponse)
async def get_document_analysis(document_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """
    Public: Retrieves the latest structured AI academic evaluation report.
    """
    # Verify document exists
    doc = await db.get(Document, document_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    if doc.status == "processing" or doc.status == "queued":
        raise HTTPException(
            status_code=status.HTTP_202_ACCEPTED,
            detail=f"Analysis is currently in progress (status: {doc.status}). Please check back shortly.",
        )

    if doc.status == "failed":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Analysis could not be generated: {doc.failure_reason or 'Extraction or evaluation failed.'}",
        )

    # Fetch latest analysis version with topics and feedback
    stmt = (
        select(DocumentAnalysis)
        .where(DocumentAnalysis.document_id == document_id)
        .order_by(desc(DocumentAnalysis.version))
        .options(
            selectinload(DocumentAnalysis.topics),
            selectinload(DocumentAnalysis.feedback),
        )
        .limit(1)
    )
    result = await db.execute(stmt)
    analysis = result.scalar_one_or_none()

    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No completed analysis found for this document.",
        )

    return analysis


@router.post("/{document_id}/reanalyse")
async def trigger_reanalyse(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Authenticated: Owner-only re-analysis trigger (only when failed or when rubric updated).
    """
    doc = await db.get(Document, document_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    check_resource_owner(doc.uploader_id, current_user, "document")

    # Set document status back to queued
    doc.status = "queued"
    doc.failure_reason = None
    await db.commit()

    # Enqueue analysis job
    enqueue_document_analysis(str(doc.id))

    return {"message": "Document re-analysis enqueued successfully."}
