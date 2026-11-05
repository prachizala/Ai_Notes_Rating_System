"""
Reviews endpoints: Peer Student & Faculty ratings and comments.
Strict Rule: Student reviews are NEVER merged into AI evaluation scores.
"""

import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user
from app.db.models import Document, Review, User
from app.db.session import get_db
from app.schemas.reviews import ReviewCreateUpdateRequest, ReviewResponse

router = APIRouter(prefix="/documents", tags=["Reviews"])


@router.get("/{document_id}/reviews", response_model=List[ReviewResponse])
async def list_document_reviews(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Public: Returns all student reviews for a given document."""
    doc = await db.get(Document, document_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    stmt = (
        select(Review)
        .where(Review.document_id == document_id)
        .options(selectinload(Review.user))
        .order_by(desc(Review.updated_at))
    )
    result = await db.execute(stmt)
    reviews = result.scalars().all()

    return [
        ReviewResponse(
            id=r.id,
            document_id=r.document_id,
            user_id=r.user_id,
            user_name=r.user.name if r.user else "Anonymous",
            user_role=r.user.role if r.user else "student",
            stars=r.stars,
            comment=r.comment,
            created_at=r.created_at,
            updated_at=r.updated_at,
        )
        for r in reviews
    ]


@router.put("/{document_id}/reviews", response_model=ReviewResponse)
async def submit_or_update_review(
    document_id: uuid.UUID,
    payload: ReviewCreateUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Authenticated: Submit or update a review.
    Enforces strictly ONE review per user per document.
    """
    doc = await db.get(Document, document_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    # Check for existing review by this user on this document
    stmt = select(Review).where(
        Review.document_id == document_id,
        Review.user_id == current_user.id,
    ).options(selectinload(Review.user))
    existing_review = (await db.execute(stmt)).scalar_one_or_none()

    if existing_review:
        # Update existing review
        existing_review.stars = payload.stars
        existing_review.comment = payload.comment.strip() if payload.comment else None
        await db.commit()
        await db.refresh(existing_review)
        review_obj = existing_review
    else:
        # Create new review
        new_review = Review(
            document_id=document_id,
            user_id=current_user.id,
            stars=payload.stars,
            comment=payload.comment.strip() if payload.comment else None,
        )
        db.add(new_review)
        await db.commit()
        await db.refresh(new_review)
        review_obj = new_review

    return ReviewResponse(
        id=review_obj.id,
        document_id=review_obj.document_id,
        user_id=review_obj.user_id,
        user_name=current_user.name,
        user_role=current_user.role,
        stars=review_obj.stars,
        comment=review_obj.comment,
        created_at=review_obj.created_at,
        updated_at=review_obj.updated_at,
    )
