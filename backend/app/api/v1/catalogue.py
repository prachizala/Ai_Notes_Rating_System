"""
Catalogue endpoints: Streams, Semesters, Dynamic Subjects & Topics.
"""

import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user
from app.db.models import Document, Semester, Stream, Subject, Topic, User
from app.db.session import get_db
from app.schemas.catalogue import (
    SemesterResponse,
    StreamResponse,
    SubjectWithTopicsResponse,
    TopicChip,
)

router = APIRouter(tags=["Catalogue"])


@router.get("/streams", response_model=List[StreamResponse])
async def list_streams(db: AsyncSession = Depends(get_db)):
    """Public: Returns all available streams (BBA, BCA, B.Voc)."""
    stmt = select(Stream).order_by(Stream.name)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/streams/{stream_id}/semesters", response_model=List[SemesterResponse])
async def list_semesters(stream_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Public: Returns semesters (Semesters 1-5 active, Semester 6 coming_soon)."""
    # Verify stream exists
    stream = await db.get(Stream, stream_id)
    if not stream:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stream not found.",
        )
    stmt = select(Semester).order_by(Semester.number)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/subjects", response_model=List[SubjectWithTopicsResponse])
async def list_subjects(
    stream: Optional[str] = Query(None, description="Stream slug or UUID"),
    semester: Optional[int] = Query(None, description="Semester number (1-6)"),
    db: AsyncSession = Depends(get_db),
):
    """
    Public: Returns dynamic subjects with topics and document counts.
    Rule: Only returns subjects that have AT LEAST ONE document.
    """
    # Build query filtering only subjects with count(documents) > 0
    stmt = (
        select(Subject)
        .join(Subject.documents)
        .options(selectinload(Subject.topics), selectinload(Subject.documents))
        .distinct()
    )

    if stream:
        # Check if stream is slug or uuid
        try:
            stream_uuid = uuid.UUID(stream)
            stmt = stmt.where(Subject.stream_id == stream_uuid)
        except ValueError:
            stmt = stmt.join(Subject.stream).where(Stream.slug == stream.lower().strip())

    if semester is not None:
        stmt = stmt.join(Subject.semester).where(Semester.number == semester)

    result = await db.execute(stmt)
    subjects = result.scalars().all()

    response_items: List[SubjectWithTopicsResponse] = []
    for subj in subjects:
        # Get count of documents per subject
        doc_count_stmt = select(func.count(Document.id)).where(Document.subject_id == subj.id)
        doc_count = (await db.execute(doc_count_stmt)).scalar() or 0

        # Topic chips with document count
        topic_chips: List[TopicChip] = []
        for top in subj.topics:
            top_doc_stmt = select(func.count(Document.id)).where(Document.topic_id == top.id)
            top_count = (await db.execute(top_doc_stmt)).scalar() or 0
            if top_count > 0:  # Only show topics that have notes
                topic_chips.append(
                    TopicChip(
                        id=top.id,
                        name=top.name,
                        normalized_name=top.normalized_name,
                        document_count=top_count,
                    )
                )

        response_items.append(
            SubjectWithTopicsResponse(
                id=subj.id,
                stream_id=subj.stream_id,
                semester_id=subj.semester_id,
                name=subj.name,
                normalized_name=subj.normalized_name,
                document_count=doc_count,
                topics=topic_chips,
            )
        )

    return response_items


@router.get("/subjects/suggest", response_model=List[str])
async def suggest_subjects(
    q: str = Query(..., min_length=1, description="Search query prefix or keyword"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Authenticated: Subject suggestions for upload autocomplete.
    Uses ILIKE or trigram matching.
    """
    query_str = f"%{q.strip().lower()}%"
    stmt = (
        select(Subject.name)
        .where(Subject.normalized_name.ilike(query_str))
        .distinct()
        .limit(10)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())
