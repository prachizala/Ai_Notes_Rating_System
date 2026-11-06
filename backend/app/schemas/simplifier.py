from typing import List, Dict, Optional
from pydantic import BaseModel, Field


class JargonItem(BaseModel):
    term: str
    simple_meaning: str


class ConceptExplanation(BaseModel):
    concept_name: str
    eli5_analogy: str
    industry_application: str
    hinglish_breakdown: str
    jargon_busters: List[JargonItem] = Field(default_factory=list)


class SimplificationResponse(BaseModel):
    document_id: str
    document_title: str
    concepts: List[ConceptExplanation]


class CustomSimplifyRequest(BaseModel):
    concept_or_query: str = Field(..., min_length=2, max_length=500)
