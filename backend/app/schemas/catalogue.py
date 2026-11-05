"""
Catalogue Pydantic Schemas.
"""

import uuid
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class StreamResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str


class SemesterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    number: int
    status: str


class TopicChip(BaseModel):
    id: uuid.UUID
    name: str
    normalized_name: str
    document_count: int = 0


class SubjectWithTopicsResponse(BaseModel):
    id: uuid.UUID
    stream_id: uuid.UUID
    semester_id: uuid.UUID
    name: str
    normalized_name: str
    document_count: int
    topics: List[TopicChip]
