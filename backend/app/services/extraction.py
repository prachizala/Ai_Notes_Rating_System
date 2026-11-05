"""
Multi-format document text extraction service (PDF with OCR fallback, DOCX, PPTX).
"""

import io
from typing import List, NamedTuple, Tuple
import fitz  # PyMuPDF
import docx
import pptx
from PIL import Image
import pytesseract

from app.core.config import settings
from app.core.logging import logger


class ExtractedUnit(NamedTuple):
    location: str
    text: str
    is_ocr: bool = False


class ExtractionResult(NamedTuple):
    units: List[ExtractedUnit]
    total_clean_chars: int
    truncated: bool
    is_low_confidence: bool
    failure_reason: str = ""


def extract_from_pdf(content: bytes) -> Tuple[List[ExtractedUnit], bool]:
    """
    Extracts text page-by-page. If page has < 30 chars, falls back to Tesseract OCR.
    """
    units: List[ExtractedUnit] = []
    has_low_confidence = False

    doc = fitz.open(stream=content, filetype="pdf")
    for page_num in range(len(doc)):
        page = doc[page_num]
        page_label = f"Page {page_num + 1}"
        text = page.get_text().strip()

        # Check if page text is insufficient and needs OCR fallback
        if len(text) < 30:
            try:
                pix = page.get_pixmap(dpi=150)
                img = Image.open(io.BytesIO(pix.tobytes("png")))
                ocr_text = pytesseract.image_to_string(img).strip()
                if ocr_text:
                    text = ocr_text
                    has_low_confidence = True
                    units.append(ExtractedUnit(location=page_label, text=text, is_ocr=True))
                    continue
            except Exception as e:
                logger.debug(f"OCR fallback on {page_label} failed or unavailable: {e}")

        if text:
            units.append(ExtractedUnit(location=page_label, text=text, is_ocr=False))

    doc.close()
    return units, has_low_confidence


def extract_from_docx(content: bytes) -> List[ExtractedUnit]:
    """
    Extracts headings, paragraphs, and table cells in sequential order.
    """
    units: List[ExtractedUnit] = []
    doc = docx.Document(io.BytesIO(content))

    current_section = "Document Body"
    section_texts: List[str] = []

    for para in doc.paragraphs:
        txt = para.text.strip()
        if not txt:
            continue
        if para.style.name.startswith("Heading"):
            if section_texts:
                units.append(ExtractedUnit(location=current_section, text="\n".join(section_texts)))
                section_texts = []
            current_section = f"Section: {txt}"
        section_texts.append(txt)

    # Process tables
    for t_idx, table in enumerate(doc.tables):
        table_rows = []
        for row in table.rows:
            row_cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
            if row_cells:
                table_rows.append(" | ".join(row_cells))
        if table_rows:
            section_texts.append(f"\n[Table {t_idx + 1}]\n" + "\n".join(table_rows))

    if section_texts:
        units.append(ExtractedUnit(location=current_section, text="\n".join(section_texts)))

    return units


def extract_from_pptx(content: bytes) -> List[ExtractedUnit]:
    """
    Extracts slide title, body shapes, and speaker notes per slide.
    """
    units: List[ExtractedUnit] = []
    prs = pptx.Presentation(io.BytesIO(content))

    for slide_idx, slide in enumerate(prs.slides):
        slide_label = f"Slide {slide_idx + 1}"
        slide_texts = []

        # Slide title
        if slide.shapes.title and slide.shapes.title.text.strip():
            slide_texts.append(f"Title: {slide.shapes.title.text.strip()}")

        # Slide body shapes
        for shape in slide.shapes:
            if shape.has_text_frame and shape != slide.shapes.title:
                for para in shape.text_frame.paragraphs:
                    txt = para.text.strip()
                    if txt:
                        slide_texts.append(txt)

        # Speaker notes
        if slide.has_notes_slide and slide.notes_slide.notes_text_frame:
            notes = slide.notes_slide.notes_text_frame.text.strip()
            if notes:
                slide_texts.append(f"[Speaker Notes]: {notes}")

        if slide_texts:
            units.append(ExtractedUnit(location=slide_label, text="\n".join(slide_texts)))

    return units


def extract_document_text(file_type: str, content: bytes) -> ExtractionResult:
    """
    Extracts structured units from PDF, DOCX, or PPTX.
    Enforces minimum readable text threshold (300 clean characters) and maximum char limit.
    """
    units: List[ExtractedUnit] = []
    is_low_conf = False

    file_type = file_type.lower().strip()
    if file_type == "pdf":
        units, is_low_conf = extract_from_pdf(content)
    elif file_type == "docx":
        units = extract_from_docx(content)
    elif file_type == "pptx":
        units = extract_from_pptx(content)
    else:
        return ExtractionResult(
            units=[],
            total_clean_chars=0,
            truncated=False,
            is_low_confidence=False,
            failure_reason=f"Unsupported format '{file_type}' for extraction.",
        )

    # Calculate total clean characters
    total_clean_chars = sum(len(u.text.strip()) for u in units)

    # Minimum threshold: 300 clean characters
    if total_clean_chars < 300:
        return ExtractionResult(
            units=units,
            total_clean_chars=total_clean_chars,
            truncated=False,
            is_low_confidence=is_low_conf,
            failure_reason="No sufficient readable academic text found in the document (under 300 characters). Cannot evaluate.",
        )

    # Truncation check
    truncated = False
    if total_clean_chars > settings.MAX_ANALYSIS_CHARS:
        truncated = True
        accumulated = 0
        truncated_units: List[ExtractedUnit] = []
        for u in units:
            if accumulated + len(u.text) > settings.MAX_ANALYSIS_CHARS:
                remaining = settings.MAX_ANALYSIS_CHARS - accumulated
                if remaining > 50:
                    truncated_units.append(ExtractedUnit(location=u.location, text=u.text[:remaining]))
                break
            truncated_units.append(u)
            accumulated += len(u.text)
        units = truncated_units
        total_clean_chars = accumulated

    return ExtractionResult(
        units=units,
        total_clean_chars=total_clean_chars,
        truncated=truncated,
        is_low_confidence=is_low_conf,
        failure_reason="",
    )
