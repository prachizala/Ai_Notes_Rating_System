from typing import List
from pydantic import BaseModel, Field


class QuizQuestion(BaseModel):
    id: int
    question: str
    options: List[str] = Field(..., min_length=4, max_length=4)
    correct_index: int = Field(..., ge=0, le=3)
    explanation: str
    difficulty: str = Field(default="medium", description="easy | medium | hard")


class Flashcard(BaseModel):
    id: int
    front: str
    back: str
    topic: str


class StudyPackResponse(BaseModel):
    document_id: str
    document_title: str
    quiz: List[QuizQuestion]
    flashcards: List[Flashcard]
