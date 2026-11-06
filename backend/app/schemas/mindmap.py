from typing import List, Optional
from pydantic import BaseModel, Field


class MindMapNode(BaseModel):
    id: str
    label: str
    description: str
    category: str = Field(default="subtopic", description="core | subtopic | detail | example")


class MindMapEdge(BaseModel):
    source: str
    target: str
    label: Optional[str] = None


class MindMapResponse(BaseModel):
    document_id: str
    document_title: str
    diagram_type: str = Field(default="flowchart", description="flowchart | mindmap | hierarchy")
    mermaid_code: str
    nodes: List[MindMapNode]
    edges: List[MindMapEdge]
    summary: str
