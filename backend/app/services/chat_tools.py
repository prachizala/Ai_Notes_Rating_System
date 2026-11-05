"""
Parameterized Read-Only Database Tools for NoteIQ AI Assistant.
Prevents arbitrary SQL generation and enforces strict factual grounding.
"""

from typing import Any, Dict, List, Optional
from sqlalchemy import desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.normalizer import normalize_name
from app.db.models import (
    Document,
    DocumentAnalysis,
    Semester,
    Stream,
    Subject,
    SyllabusTopic,
    Topic,
)
from app.services.retrieval import hybrid_retrieve_chunks


async def tool_count_notes(db: AsyncSession, stream: Optional[str] = None, semester: Optional[int] = None, subject: Optional[str] = None, topic: Optional[str] = None) -> Dict[str, Any]:
    """Tool: Counts available documents matching filters."""
    stmt = (
        select(func.count(Document.id))
        .join(Document.subject)
        .join(Subject.stream)
        .join(Subject.semester)
        .where(Document.status == "complete")
    )
    if stream:
        stmt = stmt.where(or_(Stream.slug == stream.lower().strip(), Stream.name.ilike(f"%{stream.strip()}%")))
    if semester:
        stmt = stmt.where(Semester.number == semester)
    if subject:
        stmt = stmt.where(Subject.normalized_name.ilike(f"%{normalize_name(subject)}%"))
    if topic:
        stmt = stmt.join(Document.topic).where(Topic.normalized_name.ilike(f"%{normalize_name(topic)}%"))

    count = (await db.execute(stmt)).scalar() or 0
    return {"total_matching_notes": count}


async def tool_list_notes(db: AsyncSession, stream: Optional[str] = None, semester: Optional[int] = None, subject: Optional[str] = None, topic: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
    """Tool: Lists notes metadata."""
    stmt = (
        select(Document)
        .join(Document.subject)
        .join(Subject.stream)
        .join(Subject.semester)
        .join(Document.topic)
        .where(Document.status == "complete")
        .options(
            selectinload(Document.uploader),
            selectinload(Document.subject).selectinload(Subject.stream),
            selectinload(Document.subject).selectinload(Subject.semester),
            selectinload(Document.topic),
            selectinload(Document.analyses),
        )
        .limit(limit)
    )
    if stream:
        stmt = stmt.where(or_(Stream.slug == stream.lower().strip(), Stream.name.ilike(f"%{stream.strip()}%")))
    if semester:
        stmt = stmt.where(Semester.number == semester)
    if subject:
        stmt = stmt.where(Subject.normalized_name.ilike(f"%{normalize_name(subject)}%"))
    if topic:
        stmt = stmt.where(Topic.normalized_name.ilike(f"%{normalize_name(topic)}%"))

    docs = (await db.execute(stmt)).scalars().all()
    results = []
    for d in docs:
        ai_rating = d.analyses[0].overall_score_display if d.analyses else None
        results.append({
            "id": str(d.id),
            "title": d.title,
            "stream": d.subject.stream.name if d.subject and d.subject.stream else "",
            "semester": d.subject.semester.number if d.subject and d.subject.semester else 0,
            "subject": d.subject.name if d.subject else "",
            "topic": d.topic.name if d.topic else "",
            "uploader": d.uploader.name if d.uploader else "Anonymous",
            "overall_rating": ai_rating,
        })
    return results


async def tool_list_subjects(db: AsyncSession, stream: Optional[str] = None, semester: Optional[int] = None) -> List[Dict[str, Any]]:
    """Tool: Lists subjects that have at least one note."""
    stmt = (
        select(Subject)
        .join(Subject.documents)
        .where(Document.status == "complete")
        .options(
            selectinload(Subject.stream),
            selectinload(Subject.semester),
            selectinload(Subject.topics),
        )
        .distinct()
    )
    if stream:
        stmt = stmt.join(Subject.stream).where(or_(Stream.slug == stream.lower().strip(), Stream.name.ilike(f"%{stream.strip()}%")))
    if semester:
        stmt = stmt.join(Subject.semester).where(Semester.number == semester)

    subjects = (await db.execute(stmt)).scalars().all()
    return [
        {
            "id": str(s.id),
            "name": s.name,
            "stream": s.stream.name if s.stream else "",
            "semester": s.semester.number if s.semester else 0,
            "topics": [t.name for t in s.topics],
        }
        for s in subjects
    ]


async def tool_check_topic_availability(db: AsyncSession, query: str) -> Dict[str, Any]:
    """Tool: Checks if notes are available for a given topic query."""
    norm_query = normalize_name(query)
    stmt = (
        select(Document)
        .join(Document.topic)
        .join(Document.subject)
        .where(
            Document.status == "complete",
            or_(
                Topic.normalized_name.ilike(f"%{norm_query}%"),
                Document.title.ilike(f"%{query}%"),
            ),
        )
        .options(
            selectinload(Document.topic),
            selectinload(Document.subject),
            selectinload(Document.uploader),
            selectinload(Document.analyses),
        )
        .limit(5)
    )
    docs = (await db.execute(stmt)).scalars().all()
    if not docs:
        return {"available": False, "message": f"No notes found covering '{query}'."}

    return {
        "available": True,
        "matching_notes": [
            {
                "id": str(d.id),
                "title": d.title,
                "subject": d.subject.name if d.subject else "",
                "topic": d.topic.name if d.topic else "",
                "rating": d.analyses[0].overall_score_display if d.analyses else None,
            }
            for d in docs
        ],
    }


async def tool_top_rated_notes(db: AsyncSession, stream: Optional[str] = None, semester: Optional[int] = None, subject: Optional[str] = None, limit: int = 5) -> List[Dict[str, Any]]:
    """Tool: Retrieves highest rated notes according to AI academic evaluations."""
    stmt = (
        select(Document, DocumentAnalysis.overall_score_display)
        .join(Document.analyses)
        .join(Document.subject)
        .join(Subject.stream)
        .join(Subject.semester)
        .where(Document.status == "complete")
        .options(
            selectinload(Document.uploader),
            selectinload(Document.subject),
            selectinload(Document.topic),
        )
        .order_by(desc(DocumentAnalysis.overall_score_display), desc(Document.download_count))
        .limit(limit)
    )
    if stream:
        stmt = stmt.where(or_(Stream.slug == stream.lower().strip(), Stream.name.ilike(f"%{stream.strip()}%")))
    if semester:
        stmt = stmt.where(Semester.number == semester)
    if subject:
        stmt = stmt.where(Subject.normalized_name.ilike(f"%{normalize_name(subject)}%"))

    results = (await db.execute(stmt)).all()
    output = []
    for doc, rating in results:
        output.append({
            "id": str(doc.id),
            "title": doc.title,
            "subject": doc.subject.name if doc.subject else "",
            "topic": doc.topic.name if doc.topic else "",
            "rating": rating,
            "uploader": doc.uploader.name if doc.uploader else "Anonymous",
        })
    return output


async def tool_topics_without_notes(db: AsyncSession, subject: str) -> Dict[str, Any]:
    """
    Tool: Compares subject's reference syllabus checklist with uploaded topics.
    Returns clear notice if no checklist exists.
    """
    norm_subj = normalize_name(subject)
    subj_stmt = (
        select(Subject)
        .where(Subject.normalized_name.ilike(f"%{norm_subj}%"))
        .options(selectinload(Subject.syllabus_topics), selectinload(Subject.topics))
    )
    subject_row = (await db.execute(subj_stmt)).scalars().first()
    if not subject_row:
        return {"status": "not_found", "message": f"Subject '{subject}' not found."}

    if not subject_row.syllabus_topics:
        return {
            "status": "no_checklist",
            "message": f"No reference syllabus checklist exists for subject '{subject_row.name}'. Missing topics cannot be evaluated without an official faculty checklist.",
        }

    existing_topic_norms = {t.normalized_name for t in subject_row.topics}
    missing = [st.name for st in subject_row.syllabus_topics if normalize_name(st.name) not in existing_topic_norms]

    return {
        "status": "ok",
        "subject": subject_row.name,
        "total_syllabus_topics": len(subject_row.syllabus_topics),
        "uncovered_topics": missing,
    }


async def tool_search_note_content(db: AsyncSession, query: str, subject: Optional[str] = None, limit: int = 8) -> List[Dict[str, Any]]:
    """Tool: Hybrid RAG retrieval across extracted document chunks."""
    subject_id = None
    if subject:
        s_stmt = select(Subject.id).where(Subject.normalized_name.ilike(f"%{normalize_name(subject)}%"))
        subject_id = (await db.execute(s_stmt)).scalar_one_or_none()

    return await hybrid_retrieve_chunks(query=query, db=db, subject_id=str(subject_id) if subject_id else None, limit=limit)
