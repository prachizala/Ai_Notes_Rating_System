"""
Moderation endpoints: Community flagging and Moderator actions.
"""

import uuid
from typing import List, Literal
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user, require_moderator
from app.db.models import Document, Flag, User
from app.db.session import get_db
from app.services.storage import storage_service

router = APIRouter(tags=["Moderation"])


class FlagCreateRequest(BaseModel):
    reason: str = Field(..., min_length=5, max_length=1000, description="Reason for flagging document")


class FlagActionRequest(BaseModel):
    action: Literal["dismiss", "delete_document"] = Field(...)


class FlagItemResponse(BaseModel):
    id: uuid.UUID
    document_id: uuid.UUID
    document_title: str
    reason: str
    status: str
    reporter_name: str
    created_at: str


@router.post("/documents/{document_id}/flag")
async def flag_document(
    document_id: uuid.UUID,
    payload: FlagCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Authenticated: Flag a document for moderation review.
    """
    doc = await db.get(Document, document_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    flag = Flag(
        id=uuid.uuid4(),
        document_id=document_id,
        reporter_id=current_user.id,
        reason=payload.reason.strip(),
        status="pending",
    )
    db.add(flag)
    await db.commit()

    return {"message": "Thank you. This note has been reported for moderation review."}


@router.get("/moderation/flags")
async def list_moderation_flags(
    current_moderator: User = Depends(require_moderator),
    db: AsyncSession = Depends(get_db),
):
    """
    Moderator Only: Lists pending and recent flags.
    """
    stmt = (
        select(Flag)
        .options(selectinload(Flag.document), selectinload(Flag.reporter))
        .order_by(desc(Flag.created_at))
    )
    result = await db.execute(stmt)
    flags = result.scalars().all()

    return {
        "items": [
            {
                "id": str(f.id),
                "document_id": str(f.document_id),
                "document_title": f.document.title if f.document else "[Deleted Document]",
                "reason": f.reason,
                "status": f.status,
                "reporter_name": f.reporter.name if f.reporter else "Anonymous",
                "created_at": f.created_at.isoformat(),
            }
            for f in flags
        ]
    }


@router.post("/moderation/flags/{flag_id}")
async def handle_moderation_flag(
    flag_id: uuid.UUID,
    payload: FlagActionRequest,
    current_moderator: User = Depends(require_moderator),
    db: AsyncSession = Depends(get_db),
):
    """
    Moderator Only: Resolve flag by either dismissing or deleting the offending document.
    """
    flag = await db.get(Flag, flag_id)
    if not flag:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Flag not found.")

    if payload.action == "dismiss":
        flag.status = "dismissed"
        await db.commit()
        return {"message": "Flag dismissed successfully."}

    elif payload.action == "delete_document":
        doc = await db.get(Document, flag.document_id)
        if doc:
            storage_service.delete_file(doc.file_key)
            await db.delete(doc)
        flag.status = "resolved"
        await db.commit()
        return {"message": "Document removed and flag resolved."}
