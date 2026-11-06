from typing import List, Optional
from pydantic import BaseModel, Field

class DayPlan(BaseModel):
    day_number: int = Field(ge=1, le=14)
    theme: str = Field(description="Theme for the day, e.g., Core Principles & Definitions")
    estimated_minutes: int = Field(default=45, description="Recommended study time in minutes")
    focus_topics: List[str] = Field(description="Specific subtopics from the notes to tackle")
    tasks: List[str] = Field(description="Step-by-step actionable learning checklist for today")
    recall_challenge: str = Field(description="Self-test active recall prompt to answer before sleeping")
    recommended_tool: str = Field(description="NoteIQ tool suggestion: Mind Map, Flashcards, Viva Voce, Cheat Sheet, etc.")

class StudyPlannerResponse(BaseModel):
    document_id: str
    document_title: str
    subject_name: str
    total_days: int = 7
    total_estimated_hours: float
    planner_strategy: str = Field(description="Ebbinghaus Spaced Repetition + Active Recall methodology summary")
    days: List[DayPlan]
    general_exam_tips: List[str]
