from typing import List
from pydantic import BaseModel, Field


class PodcastTurn(BaseModel):
    speaker: str = Field(..., description="Alex (Host) | Sam (Specialist)")
    role: str = Field(default="host", description="host | specialist")
    text: str
    topic_tag: str = Field(default="Concept")


class AudioPodcastResponse(BaseModel):
    document_id: str
    document_title: str
    episode_title: str
    estimated_duration_minutes: int = Field(default=4)
    turns: List[PodcastTurn]
    key_takeaways: List[str]
