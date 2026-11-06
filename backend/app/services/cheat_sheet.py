"""
Printable 1-Page Exam Cheat Sheet & Formula Card Service for NoteIQ.
Distills dense course notes into a high-density, printable A4 quick-revision summary.
"""

from typing import Any, Dict, List, Optional
from app.core.config import settings
from app.core.logging import logger
from app.services.llm import get_llm_client


CHEAT_SHEET_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "summary_capsule": {"type": "STRING"},
        "formulas_and_syntax": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "title": {"type": "STRING"},
                    "syntax_or_formula": {"type": "STRING"},
                    "note": {"type": "STRING"}
                },
                "required": ["title", "syntax_or_formula", "note"]
            }
        },
        "key_definitions": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "term": {"type": "STRING"},
                    "definition": {"type": "STRING"}
                },
                "required": ["term", "definition"]
            }
        },
        "distinctions_table": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "parameter": {"type": "STRING"},
                    "concept_a": {"type": "STRING"},
                    "concept_b": {"type": "STRING"}
                },
                "required": ["parameter", "concept_a", "concept_b"]
            }
        },
        "exam_traps": {
            "type": "ARRAY",
            "items": {"type": "STRING"}
        },
        "rapid_mnemonics": {
            "type": "ARRAY",
            "items": {"type": "STRING"}
        }
    },
    "required": [
        "summary_capsule", "formulas_and_syntax", "key_definitions",
        "distinctions_table", "exam_traps", "rapid_mnemonics"
    ]
}


SYSTEM_PROMPT = """You are an elite academic tutor creating a 1-page condensed exam cheat sheet and formula card for college examinations.
Extract the highest-yield, most critical elements:
1. summary_capsule: 2 sentences explaining the core foundation.
2. formulas_and_syntax: 3-4 formulas, code signatures, or syntax declarations.
3. key_definitions: 4 concise definitions guaranteed to fetch full marks.
4. distinctions_table: 3 comparison rows contrasting two core concepts.
5. exam_traps: 3 common student mistakes to avoid.
6. rapid_mnemonics: 2 catchy memory aids.

Rules:
- Strict technical accuracy based only on the provided note.
- Output valid JSON conforming to the schema.
"""


def _generate_fallback_cheat_sheet(document_title: str, text: str, summary: str, subject_name: str) -> Dict[str, Any]:
    """Generates a structured, high-density exam revision cheat sheet."""
    lines = [line.strip() for line in text.split("\n") if len(line.strip()) > 8]

    # Extract terms
    terms: List[Dict[str, str]] = []
    for line in lines:
        if ":" in line and len(line.split(":")[0].split()) <= 4:
            parts = line.split(":", 1)
            term = parts[0].strip().strip("-*•# ")
            defi = parts[1].strip()
            if len(term) > 2 and len(defi) > 8:
                terms.append({"term": term, "definition": defi})
        elif any(v in line.lower() for v in [" is a ", " is defined as ", " refers to "]):
            for v in [" is a ", " is defined as ", " refers to "]:
                if v in line:
                    parts = line.split(v, 1)
                    t = parts[0].strip().strip("-*•# ")
                    if len(t.split()) <= 4:
                        terms.append({"term": t, "definition": f"{t} {v} {parts[1].strip()}"})
                    break

    if len(terms) < 4:
        terms.extend([
            {"term": "Core Foundation", "definition": f"Standard theoretical principles underlying {document_title}."},
            {"term": "Dynamic Allocation", "definition": "Allocation of resource blocks during program runtime on heap memory."},
            {"term": "Boundary Check", "definition": "Validating limits to prevent memory overflow or out-of-bounds corruption."},
            {"term": "Deallocation", "definition": "Releasing acquired system resources back to the pool to prevent leaks."}
        ])

    is_c_programming = "pointer" in text.lower() or "c prog" in document_title.lower() or "malloc" in text.lower()

    if is_c_programming:
        formulas = [
            {"title": "Pointer Declaration", "syntax_or_formula": "int *ptr = &var;", "note": "Stores memory address of var"},
            {"title": "malloc() Syntax", "syntax_or_formula": "ptr = (int*) malloc(n * sizeof(int));", "note": "Allocates contiguous bytes on heap"},
            {"title": "free() Memory Release", "syntax_or_formula": "free(ptr); ptr = NULL;", "note": "Prevents memory leaks and dangling pointer"},
            {"title": "Pointer Dereference", "syntax_or_formula": "*ptr = 50;", "note": "Modifies value at referenced address"}
        ]
        distinctions = [
            {"parameter": "Initialization", "concept_a": "malloc(): Leaves garbage values", "concept_b": "calloc(): Initializes bytes to 0"},
            {"parameter": "Speed", "concept_a": "malloc(): Faster allocation", "concept_b": "calloc(): Slightly slower due to zeroing"},
            {"parameter": "Arguments", "concept_a": "malloc(size_t size)", "concept_b": "calloc(size_t n, size_t size)"}
        ]
        traps = [
            "Forgetting to check if malloc returned NULL (leads to segmentation faults).",
            "Freeing memory and still accessing ptr (Dangling Pointer trap).",
            "Confusing pointer variable address (&ptr) with target address (ptr)."
        ]
        mnemonics = [
            "& = Address-of ('At where?'), * = Value-at ('What is inside?')",
            "Free Then Null: Always set ptr = NULL right after free(ptr)"
        ]
    else:
        formulas = [
            {"title": "Standard Declaration / Syntax", "syntax_or_formula": f"{terms[0]['term']} = evaluate(input)", "note": "Primary execution construct"},
            {"title": "Resource Allocation", "syntax_or_formula": "allocate(resource_spec, capacity)", "note": "Assigns runtime operational block"},
            {"title": "Cleanup Rule", "syntax_or_formula": "release(handle);", "note": "Restores system state after completion"}
        ]
        distinctions = [
            {"parameter": "Scope", "concept_a": f"Static {document_title}: Fixed at setup", "concept_b": f"Dynamic {document_title}: Scalable at runtime"},
            {"parameter": "Overhead", "concept_a": "Lower initial complexity", "concept_b": "Higher flexibility with management checks"},
            {"parameter": "Failure Mode", "concept_a": "Hard limits reached early", "concept_b": "Requires explicit defensive validation"}
        ]
        traps = [
            "Omitting technical keywords in 2-mark definition answers.",
            "Drawing block diagrams without proper directional arrow annotations.",
            "Failing to discuss runtime trade-offs and error states."
        ]
        mnemonics = [
            "Define -> Draw -> Derive: Follow this 3-D rule for 5 and 10 mark answers.",
            "K-I-S-S: Keep It Structured and Specific to secure full rubric marks."
        ]

    return {
        "summary_capsule": summary or f"Essential study capsule covering {document_title} for undergraduate examinations.",
        "formulas_and_syntax": formulas,
        "key_definitions": terms[:4],
        "distinctions_table": distinctions,
        "exam_traps": traps,
        "rapid_mnemonics": mnemonics
    }


class CheatSheetService:
    """Service to create condensed printable exam formula cheat sheets."""

    def generate_cheat_sheet(
        self,
        document_title: str,
        text: str,
        summary: str = "",
        subject_name: str = ""
    ) -> Dict[str, Any]:
        llm = get_llm_client()

        if settings.ENVIRONMENT == "test" or not settings.LLM_API_KEY or settings.LLM_PROVIDER == "fake":
            return _generate_fallback_cheat_sheet(document_title, text, summary, subject_name)

        prompt_user = f"""Document Title: {document_title}
Subject: {subject_name}
Summary: {summary}

Document Content:
\"\"\"
{text[:25000]}
\"\"\"

Create a 1-page condensed college examination cheat sheet with:
- summary_capsule (2 sentences)
- formulas_and_syntax (3-4 code/formula items)
- key_definitions (4 high-yield definitions)
- distinctions_table (3 comparison parameters)
- exam_traps (3 common exam mistakes to avoid)
- rapid_mnemonics (2 memory aids)
"""
        try:
            result = llm.generate_json(
                system=SYSTEM_PROMPT,
                user=prompt_user,
                schema=CHEAT_SHEET_SCHEMA
            )
            if "formulas_and_syntax" in result and "key_definitions" in result:
                return result
        except Exception as e:
            logger.warning("LLM cheat sheet generation error, using fallback: %s", str(e))

        return _generate_fallback_cheat_sheet(document_title, text, summary, subject_name)


cheat_sheet_service = CheatSheetService()
