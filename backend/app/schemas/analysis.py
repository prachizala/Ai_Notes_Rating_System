"""
Analysis Pydantic Schemas.
"""

import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class AnalysisTopicResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    topic_name: str
    note: Optional[str] = None


class AnalysisFeedbackResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    kind: str  # strength | improvement | missing_concept | error_found
    text: str
    evidence_ref: Optional[str] = None


class DocumentAnalysisReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    document_id: uuid.UUID
    version: int
    rubric_version: str
    model_name: str
    topic_coverage_pct: Optional[float] = None
    accuracy_score: float
    explanation_score: float
    depth_score: float
    examples_score: float
    overall_score_raw: float
    overall_score_display: float
    confidence: str
    confidence_reason: Optional[str] = None
    summary: str
    total_topics: int
    topics: List[AnalysisTopicResponse]
    feedback: List[AnalysisFeedbackResponse]
    created_at: datetime
