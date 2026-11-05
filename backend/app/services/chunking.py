"""
Semantic document chunking service.
Splits text into chunks of roughly 500-800 tokens with 80-token overlap,
preserving page/slide boundary metadata.
"""

from typing import List, NamedTuple
from app.services.extraction import ExtractedUnit


class DocumentChunkItem(NamedTuple):
    chunk_index: int
    location: str
    text: str


def approximate_tokens(text: str) -> int:
    """Rough approximation of tokens using word count / 0.75."""
    return max(1, int(len(text.split()) / 0.75))


def chunk_extracted_units(units: List[ExtractedUnit], target_tokens: int = 600, overlap_tokens: int = 80) -> List[DocumentChunkItem]:
    """
    Chunks extracted units into balanced token segments with overlap.
    Preserves location metadata (e.g. Page 1, Slide 3).
    Avoids splitting across page boundaries whenever page text fits target tokens.
    """
    chunks: List[DocumentChunkItem] = []
    chunk_index = 0

    for unit in units:
        text = unit.text.strip()
        unit_tokens = approximate_tokens(text)

        # If unit fits reasonably within chunk limits, keep it whole
        if unit_tokens <= target_tokens + 100:
            chunks.append(DocumentChunkItem(chunk_index=chunk_index, location=unit.location, text=text))
            chunk_index += 1
            continue

        # Otherwise, split paragraphs or sentences with overlap
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        if not paragraphs:
            paragraphs = [p.strip() for p in text.split("\n") if p.strip()]

        current_paras: List[str] = []
        current_tokens = 0

        for para in paragraphs:
            para_tokens = approximate_tokens(para)
            if current_tokens + para_tokens > target_tokens and current_paras:
                # Flush chunk
                chunk_text = "\n\n".join(current_paras)
                chunks.append(DocumentChunkItem(chunk_index=chunk_index, location=unit.location, text=chunk_text))
                chunk_index += 1

                # Retain overlap (last paragraph if possible)
                if para_tokens < target_tokens:
                    current_paras = [current_paras[-1], para] if approximate_tokens(current_paras[-1]) <= overlap_tokens * 2 else [para]
                    current_tokens = sum(approximate_tokens(p) for p in current_paras)
                else:
                    current_paras = []
                    current_tokens = 0
            else:
                current_paras.append(para)
                current_tokens += para_tokens

        if current_paras:
            chunk_text = "\n\n".join(current_paras)
            chunks.append(DocumentChunkItem(chunk_index=chunk_index, location=unit.location, text=chunk_text))
            chunk_index += 1

    return chunks
