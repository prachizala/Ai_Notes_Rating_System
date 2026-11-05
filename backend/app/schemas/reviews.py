"""
Reviews Pydantic Schemas.
"""

import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class ReviewCreateUpdateRequest(BaseModel):
    stars: int = Field(..., ge=1, le=5, description="Star rating from 1 to 5")
    comment: Optional[str] = Field(None, max_length=500, description="Optional qualitative feedback up to 500 chars")


class ReviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    document_id: uuid.UUID
    user_id: uuid.UUID
    user_name: str
    user_role: str
    stars: int
    comment: Optional[str] = None
    created_at: datetime
    updated_at: datetime
