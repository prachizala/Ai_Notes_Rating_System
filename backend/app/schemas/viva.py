from typing import List, Optional
from pydantic import BaseModel, Field

class VivaQuestion(BaseModel):
    id: int
    question: str
    difficulty: str = Field(default="Medium", description="Easy | Medium | Hard")
    examiner_tip: str = Field(description="Tip from the professor on how to answer effectively")
    ideal_answer_key: str = Field(description="Core points examiner is looking for")
    follow_up_hint: str = Field(description="A teaser follow-up if answered well")

class VivaSessionResponse(BaseModel):
    document_id: str
    document_title: str
    total_questions: int
    questions: List[VivaQuestion]

class VivaEvaluationRequest(BaseModel):
    question: str
    student_answer: str
    ideal_answer_key: Optional[str] = None
    difficulty: Optional[str] = "Medium"

class VivaEvaluationResponse(BaseModel):
    score: int = Field(ge=0, le=10, description="Marks out of 10 awarded by examiner")
    max_score: int = 10
    examiner_verdict: str = Field(description="e.g. Excellent / Satisfactory / Incomplete / Off-track")
    feedback: str
    strengths: List[str]
    missing_key_points: List[str]
    improved_answer: str
