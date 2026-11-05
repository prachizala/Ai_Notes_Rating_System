"""
Hybrid Document Retrieval Service (pgvector + full-text search with Reciprocal Rank Fusion).
"""

import math
from typing import Any, Dict, List, Optional
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import Document, DocumentChunk, Subject
from app.services.embeddings import embedding_service


def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)


async def hybrid_retrieve_chunks(
    query: str,
    db: AsyncSession,
    subject_id: Optional[str] = None,
    limit: int = 8,
) -> List[Dict[str, Any]]:
    """
    Executes hybrid retrieval:
    1. Semantic similarity using vector embedding.
    2. Keyword/Full-text search.
    3. Merges via Reciprocal Rank Fusion (RRF: 1 / (60 + rank)).
    Returns top ranked chunks with document title, location, and uploader.
    """
    query_emb = embedding_service.embed_query(query)
    query_terms = [t.lower() for t in query.split() if len(t) > 2]

    # Fetch candidate chunks
    stmt = (
        select(DocumentChunk)
        .join(DocumentChunk.document)
        .where(Document.status == "complete")
        .options(
            selectinload(DocumentChunk.document).selectinload(Document.uploader),
            selectinload(DocumentChunk.document).selectinload(Document.subject),
        )
    )

    if subject_id:
        stmt = stmt.where(Document.subject_id == subject_id)

    result = await db.execute(stmt)
    chunks = result.scalars().all()

    if not chunks:
        return []

    # 1. Rank by vector similarity
    vector_scores = []
    for c in chunks:
        score = 0.0
        if isinstance(c.embedding, list):
            score = cosine_similarity(query_emb, c.embedding)
        vector_scores.append((c, score))
    vector_scores.sort(key=lambda x: x[1], reverse=True)

    # 2. Rank by text keyword match
    text_scores = []
    for c in chunks:
        c_text = c.text.lower()
        match_count = sum(1 for term in query_terms if term in c_text)
        text_scores.append((c, match_count))
    text_scores.sort(key=lambda x: x[1], reverse=True)

    # 3. Reciprocal Rank Fusion (k = 60)
    rrf_scores: Dict[str, float] = {}
    chunk_map: Dict[str, DocumentChunk] = {}

    for rank, (c, _) in enumerate(vector_scores):
        cid = str(c.id)
        chunk_map[cid] = c
        rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (60.0 + rank + 1.0))

    for rank, (c, _) in enumerate(text_scores):
        cid = str(c.id)
        chunk_map[cid] = c
        rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (60.0 + rank + 1.0))

    sorted_chunk_ids = sorted(rrf_scores.keys(), key=lambda cid: rrf_scores[cid], reverse=True)[:limit]

    output = []
    for cid in sorted_chunk_ids:
        chunk = chunk_map[cid]
        doc = chunk.document
        output.append({
            "chunk_id": str(chunk.id),
            "document_id": str(doc.id),
            "document_title": doc.title,
            "uploader_name": doc.uploader.name if doc.uploader else "Anonymous",
            "subject_name": doc.subject.name if doc.subject else "",
            "location": chunk.location,
            "text": chunk.text,
            "score": round(rrf_scores[cid], 4),
        })

    return output
