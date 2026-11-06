from typing import List
from pydantic import BaseModel, Field


class CoveredTopicItem(BaseModel):
    topic_name: str
    status: str = Field(default="covered", description="covered | partially_covered")
    depth_percentage: int = Field(default=85, ge=0, le=100)
    location: str = Field(default="Page 1")


class MissingTopicItem(BaseModel):
    topic_name: str
    importance: str = Field(default="High", description="Critical | High | Medium")
    reason: str
    recommended_search_query: str


class SyllabusGapResponse(BaseModel):
    document_id: str
    document_title: str
    subject_name: str
    completeness_percentage: int = Field(..., ge=0, le=100)
    coverage_tier: str = Field(default="Solid", description="Comprehensive | Solid | Needs Supplementary Material")
    covered_topics: List[CoveredTopicItem]
    missing_topics: List[MissingTopicItem]
    study_advice: str
