from typing import List, Optional
from pydantic import BaseModel, Field

class DocumentReaderChunk(BaseModel):
    chunk_index: int
    location: str
    text: str

class DocumentReaderResponse(BaseModel):
    document_id: str
    document_title: str
    total_chunks: int
    chunks: List[DocumentReaderChunk]

class InlineExplainRequest(BaseModel):
    selected_text: str = Field(description="The highlighted phrase, formula, or sentence from the note")
    context: Optional[str] = Field(default=None, description="Surrounding paragraph or section for context")
    mode: str = Field(default="eli5", description="eli5 | hinglish | exam_trap | academic")

class InlineExplainResponse(BaseModel):
    selected_text: str
    mode: str
    explanation: str
    key_takeaways: List[str]
    mnemonic_or_analogy: Optional[str] = None
