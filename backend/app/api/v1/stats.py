"""
Platform statistics endpoint: Live counts of notes, subjects, topics, contributors.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Document, Subject, Topic
from app.db.session import get_db

router = APIRouter(tags=["Stats"])


class PlatformStatsResponse(BaseModel):
    total_notes: int
    total_subjects: int
    total_topics: int
    total_contributors: int
    analysed_notes: int


@router.get("/stats", response_model=PlatformStatsResponse)
async def get_platform_stats(db: AsyncSession = Depends(get_db)):
    """
    Public: Live summary statistics of notes and contributors.
    """
    total_notes = (await db.execute(select(func.count(Document.id)))).scalar() or 0
    total_subjects = (await db.execute(select(func.count(Subject.id)))).scalar() or 0
    total_topics = (await db.execute(select(func.count(Topic.id)))).scalar() or 0
    total_contributors = (await db.execute(select(func.count(func.distinct(Document.uploader_id))))).scalar() or 0
    analysed_notes = (await db.execute(select(func.count(Document.id)).where(Document.status == "complete"))).scalar() or 0

    return PlatformStatsResponse(
        total_notes=total_notes,
        total_subjects=total_subjects,
        total_topics=total_topics,
        total_contributors=total_contributors,
        analysed_notes=analysed_notes,
    )
