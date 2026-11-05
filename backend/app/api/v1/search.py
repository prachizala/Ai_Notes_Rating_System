"""
Search endpoint: Grouped search across Subjects, Topics, and Documents.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.v1.documents import format_document_response
from app.db.models import Document, Subject, Topic
from app.db.session import get_db
from app.schemas.catalogue import SubjectWithTopicsResponse, TopicChip
from app.schemas.document import DocumentResponse

router = APIRouter(tags=["Search"])


class TopicSearchResult(BaseModel):
    id: str
    name: str
    subject_name: str


class GroupedSearchResponse(BaseModel):
    documents: List[DocumentResponse]
    subjects: List[SubjectWithTopicsResponse]
    topics: List[TopicSearchResult]


@router.get("/search", response_model=GroupedSearchResponse)
async def search_catalogue(
    q: str = Query(..., min_length=1, description="Search keyword"),
    db: AsyncSession = Depends(get_db),
):
    """
    Public: Grouped search across documents, subjects, and topics.
    """
    keyword = f"%{q.strip().lower()}%"

    # 1. Search Documents (title, description)
    doc_stmt = (
        select(Document)
        .where(
            or_(
                Document.title.ilike(keyword),
                Document.description.ilike(keyword),
            )
        )
        .options(
            selectinload(Document.uploader),
            selectinload(Document.subject).selectinload(Subject.stream),
            selectinload(Document.subject).selectinload(Subject.semester),
            selectinload(Document.topic),
        )
        .limit(10)
    )
    docs = (await db.execute(doc_stmt)).scalars().all()
    formatted_docs = [await format_document_response(d, db) for d in docs]

    # 2. Search Subjects (name, normalized_name)
    subj_stmt = (
        select(Subject)
        .where(
            or_(
                Subject.name.ilike(keyword),
                Subject.normalized_name.ilike(keyword),
            )
        )
        .options(selectinload(Subject.topics))
        .limit(10)
    )
    subjects = (await db.execute(subj_stmt)).scalars().all()
    formatted_subjects = [
        SubjectWithTopicsResponse(
            id=s.id,
            stream_id=s.stream_id,
            semester_id=s.semester_id,
            name=s.name,
            normalized_name=s.normalized_name,
            document_count=len(s.topics),
            topics=[TopicChip(id=t.id, name=t.name, normalized_name=t.normalized_name, document_count=0) for t in s.topics],
        )
        for s in subjects
    ]

    # 3. Search Topics
    topic_stmt = (
        select(Topic)
        .where(
            or_(
                Topic.name.ilike(keyword),
                Topic.normalized_name.ilike(keyword),
            )
        )
        .options(selectinload(Topic.subject))
        .limit(10)
    )
    topics = (await db.execute(topic_stmt)).scalars().all()
    formatted_topics = [
        TopicSearchResult(
            id=str(t.id),
            name=t.name,
            subject_name=t.subject.name if t.subject else "General",
        )
        for t in topics
    ]

    return GroupedSearchResponse(
        documents=formatted_docs,
        subjects=formatted_subjects,
        topics=formatted_topics,
    )
