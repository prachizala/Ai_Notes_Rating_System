"""
Document Pydantic Schemas.
"""

import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    subject_id: uuid.UUID
    topic_id: uuid.UUID
    uploader_id: uuid.UUID
    uploader_name: str
    uploader_role: str
    stream_name: Optional[str] = None
    semester_number: Optional[int] = None
    subject_name: Optional[str] = None
    topic_name: Optional[str] = None
    title: str
    description: Optional[str] = None
    file_type: str
    file_size: int
    status: str  # queued | processing | complete | failed
    failure_reason: Optional[str] = None
    download_count: int
    overall_rating: Optional[float] = None
    student_rating_avg: Optional[float] = None
    student_rating_count: int = 0
    created_at: datetime


class DocumentListResponse(BaseModel):
    items: List[DocumentResponse]
    total: int
    page: int
    limit: int
    pages: int


class DocumentUpdateRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=2, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)


class DocumentDownloadResponse(BaseModel):
    download_url: str
    filename: str
