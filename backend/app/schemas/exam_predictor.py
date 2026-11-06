from typing import List
from pydantic import BaseModel, Field


class PredictedQuestion(BaseModel):
    id: int
    marks: int = Field(..., description="2, 5, or 10 marks")
    category: str = Field(..., description="2 Marks (Definitions) | 5 Marks (Conceptual) | 10 Marks (In-Depth)")
    question: str
    probability: str = Field(default="High", description="Very High | High | Medium")
    expected_key_points: List[str]
    location: str = Field(default="Page 1", description="Page or Slide reference")
    bloom_level: str = Field(default="Understand", description="Recall | Understand | Apply | Analyze")


class ExamPredictionResponse(BaseModel):
    document_id: str
    document_title: str
    total_predicted: int
    questions: List[PredictedQuestion]
    exam_tips: List[str]
