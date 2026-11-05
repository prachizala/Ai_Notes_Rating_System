"""
Syllabus Checklist endpoints: Reference topics created and edited by Faculty.
"""

import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.models import Document, Subject, SyllabusTopic, User
from app.db.session import get_db
from app.workers.jobs import enqueue_document_analysis

router = APIRouter(prefix="/subjects", tags=["Syllabus"])


class SyllabusUpdateRequest(BaseModel):
    topics: List[str] = Field(..., description="List of reference syllabus topic names")


class SyllabusResponse(BaseModel):
    subject_id: uuid.UUID
    topics: List[str]


@router.get("/{subject_id}/syllabus", response_model=SyllabusResponse)
async def get_subject_syllabus(
    subject_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Public: Retrieves the reference syllabus topic checklist for a subject."""
    subject = await db.get(Subject, subject_id)
    if not subject:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found.")

    stmt = select(SyllabusTopic.name).where(SyllabusTopic.subject_id == subject_id)
    result = await db.execute(stmt)
    topics = list(result.scalars().all())

    return SyllabusResponse(subject_id=subject_id, topics=topics)


@router.put("/{subject_id}/syllabus", response_model=SyllabusResponse)
async def update_subject_syllabus(
    subject_id: uuid.UUID,
    payload: SyllabusUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Authenticated (Faculty Only): Create or update the reference syllabus checklist.
    Triggers re-analysis for all documents under this subject to recalculate coverage.
    """
    if current_user.role != "faculty" and not current_user.is_moderator:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only faculty members can define or update the reference syllabus checklist.",
        )

    subject = await db.get(Subject, subject_id)
    if not subject:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found.")

    # Delete existing syllabus checklist items
    await db.execute(delete(SyllabusTopic).where(SyllabusTopic.subject_id == subject_id))

    # Add new items
    clean_topics = [t.strip() for t in payload.topics if t.strip()]
    for name in clean_topics:
        db.add(SyllabusTopic(
            id=uuid.uuid4(),
            subject_id=subject_id,
            name=name,
            added_by=current_user.id,
        ))

    await db.commit()

    # Re-queue documents under this subject to update syllabus coverage
    docs_stmt = select(Document.id).where(Document.subject_id == subject_id)
    doc_ids = (await db.execute(docs_stmt)).scalars().all()
    for d_id in doc_ids:
        enqueue_document_analysis(str(d_id))

    return SyllabusResponse(subject_id=subject_id, topics=clean_topics)
