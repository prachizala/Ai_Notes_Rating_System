"""
Chat Assistant Endpoints: Interactive grounded conversation backed by database tools and RAG.
"""

import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.rate_limit import check_rate_limit
from app.db.models import ChatMessage, ChatSession, User
from app.db.session import get_db
from app.services.chat import run_chat_turn

router = APIRouter(prefix="/chat", tags=["Chat Assistant"])


class ChatMessageRequest(BaseModel):
    session_id: Optional[uuid.UUID] = None
    message: str = Field(..., min_length=1, max_length=2000, description="User question or query")


class ChatSourceResponse(BaseModel):
    document_id: str
    title: str
    uploader_name: str
    overall_rating: Optional[float] = None
    location: Optional[str] = None
    snippet: Optional[str] = None


class ChatMessageResponse(BaseModel):
    id: uuid.UUID
    role: str
    content: str
    sources: Optional[List[ChatSourceResponse]] = None
    created_at: str


class ChatTurnResponse(BaseModel):
    session_id: uuid.UUID
    message: ChatMessageResponse


class ChatSessionDetailResponse(BaseModel):
    session_id: uuid.UUID
    title: str
    messages: List[ChatMessageResponse]


@router.post("", response_model=ChatTurnResponse)
async def send_chat_message(
    payload: ChatMessageRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Authenticated: Ask a question to NoteIQ AI Assistant.
    Enforces CHAT_RATE_LIMIT_PER_HOUR.
    """
    # 1. Enforce hourly chat rate limit per user
    rate_key = f"rl:chat:{current_user.id}"
    if not check_rate_limit(rate_key, limit=settings.CHAT_RATE_LIMIT_PER_HOUR, window_seconds=3600):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Chat rate limit reached ({settings.CHAT_RATE_LIMIT_PER_HOUR} messages/hour). Please wait a while before sending more messages.",
        )

    # 2. Get or create session
    session_obj: Optional[ChatSession] = None
    if payload.session_id:
        session_obj = await db.get(ChatSession, payload.session_id)
        if session_obj and session_obj.user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this chat session.")

    if not session_obj:
        # Create new session with title based on first query
        session_title = payload.message[:40] + ("..." if len(payload.message) > 40 else "")
        session_obj = ChatSession(
            id=uuid.uuid4(),
            user_id=current_user.id,
            title=session_title,
        )
        db.add(session_obj)
        await db.flush()

    # 3. Save User message
    user_msg = ChatMessage(
        id=uuid.uuid4(),
        session_id=session_obj.id,
        role="user",
        content=payload.message.strip(),
    )
    db.add(user_msg)
    await db.flush()

    # 4. Run Grounded Assistant Turn
    turn_output = await run_chat_turn(message=payload.message.strip(), db=db)

    # 5. Save Assistant message
    assistant_msg = ChatMessage(
        id=uuid.uuid4(),
        session_id=session_obj.id,
        role="assistant",
        content=turn_output["answer"],
        sources_json={"sources": turn_output["sources"]},
    )
    db.add(assistant_msg)
    await db.commit()
    await db.refresh(assistant_msg)

    sources_list = [ChatSourceResponse(**s) for s in turn_output["sources"]]

    return ChatTurnResponse(
        session_id=session_obj.id,
        message=ChatMessageResponse(
            id=assistant_msg.id,
            role="assistant",
            content=assistant_msg.content,
            sources=sources_list,
            created_at=assistant_msg.created_at.isoformat(),
        ),
    )


@router.get("/sessions/{session_id}", response_model=ChatSessionDetailResponse)
async def get_chat_session(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Authenticated: Returns full conversation history for a given session.
    """
    session_obj = await db.get(ChatSession, session_id)
    if not session_obj or session_obj.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found.")

    stmt = (
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
    )
    result = await db.execute(stmt)
    messages = result.scalars().all()

    formatted_msgs = []
    for m in messages:
        sources = None
        if m.sources_json and "sources" in m.sources_json:
            sources = [ChatSourceResponse(**s) for s in m.sources_json["sources"]]
        formatted_msgs.append(
            ChatMessageResponse(
                id=m.id,
                role=m.role,
                content=m.content,
                sources=sources,
                created_at=m.created_at.isoformat(),
            )
        )

    return ChatSessionDetailResponse(
        session_id=session_obj.id,
        title=session_obj.title,
        messages=formatted_msgs,
    )
