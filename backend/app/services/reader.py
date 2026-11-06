"""
Interactive Note Reader & In-Text Highlight Explanation Service for NoteIQ.
Provides real-time contextual explanations for student text selections.
"""

from typing import Any, Dict, List, Optional
import json
import re
from app.core.config import settings
from app.core.logging import logger
from app.services.llm import get_llm_client
from app.schemas.reader import InlineExplainResponse


READER_EXPLAIN_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "explanation": {"type": "STRING"},
        "key_takeaways": {
            "type": "ARRAY",
            "items": {"type": "STRING"}
        },
        "mnemonic_or_analogy": {"type": "STRING"}
    },
    "required": ["explanation", "key_takeaways", "mnemonic_or_analogy"]
}


def _fallback_explanation(selected_text: str, mode: str) -> Dict[str, Any]:
    """Heuristic fallback when Gemini is unavailable."""
    words = selected_text.strip().split()
    first_few = " ".join(words[:5])

    if mode == "hinglish":
        return {
            "explanation": f"Iska basic matlab yeh hai ki {first_few}... yeh concept system ya theory me ek specific task automate ya optimize karne ke liye use hota hai. Simple shabdon me, jab multiple elements ek sath kaam karte hain toh yeh ensure karta hai ki koi conflict ya error na ho.",
            "key_takeaways": [
                "Yeh fundamental concept exam me 2-mark ya 5-mark question me frequently pucha jata hai.",
                "Iska primary benefit efficiency aur consistency maintain karna hai."
            ],
            "mnemonic_or_analogy": "Socho jaise traffic signal road par gaadiyon ka flow regulate karta hai bina accident ke."
        }
    elif mode == "exam_trap":
        return {
            "explanation": f"Students often confuse '{first_few}' with related theoretical concepts or forget edge cases. In university exams, examiners look for exact keywords and structural diagrams rather than casual explanations.",
            "key_takeaways": [
                "Common Trap: Mixing up the primary definition with its secondary application.",
                "Always state the prerequisite conditions before writing the formula or mechanism."
            ],
            "mnemonic_or_analogy": "Remember: Input Validation comes before Processing; never invert the order."
        }
    elif mode == "academic":
        return {
            "explanation": f"From an academic standpoint, {selected_text.strip()} denotes a standard operational paradigm. It adheres to established principles and functions as a governing constraint within this domain.",
            "key_takeaways": [
                "Defined by formal literature and standard university syllabi.",
                "Serves as a prerequisite building block for advanced topics."
            ],
            "mnemonic_or_analogy": "Fundamental building block paradigm."
        }
    else:  # default eli5
        return {
            "explanation": f"Imagine you have a puzzle or a recipe: '{first_few}' is like the secret ingredient that keeps everything glued together so it doesn't fall apart when things get busy.",
            "key_takeaways": [
                "Breaks down complex terminology into everyday language.",
                "Explains why this particular step or definition actually matters."
            ],
            "mnemonic_or_analogy": "Think of it like a smartphone autocorrect: it quietly fixes misunderstandings behind the scenes."
        }


def explain_inline_snippet(
    selected_text: str,
    context: Optional[str] = None,
    mode: str = "eli5"
) -> InlineExplainResponse:
    """Explains a highlighted snippet in the requested mode (eli5, hinglish, exam_trap, academic)."""
    client = get_llm_client()
    clean_text = selected_text.strip()
    result_data: Optional[Dict[str, Any]] = None

    if client and getattr(settings, "GEMINI_API_KEY", None):
        mode_instructions = {
            "eli5": "Explain this in simple 5th-grade terms using an intuitive real-world analogy. Avoid heavy jargon.",
            "hinglish": "Explain this in fluent, conversational college Hinglish (Hindi + English blend) as an Indian engineering/management senior would explain to a junior before an exam.",
            "exam_trap": "Identify the common misconception, exam calculation trap, or frequent mistake students make regarding this concept in university exams.",
            "academic": "Provide a precise, rigorous academic definition with formal terminology and theoretical depth."
        }.get(mode, "Explain clearly with intuitive analogies.")

        prompt = f"""
You are an expert university teaching assistant helping a student reading academic course notes.

Highlighted Text:
"{clean_text}"

Surrounding Section Context:
"{context[:1000] if context else 'General academic notes'}"

Requested Explanation Mode: {mode.upper()}
Mode Guideline: {mode_instructions}

Return JSON with:
- explanation: 2-3 clear sentences explaining the highlighted text directly in the requested mode.
- key_takeaways: 2 bullet points emphasizing practical relevance or exam tips.
- mnemonic_or_analogy: 1 punchy mental image, mnemonic, or real-world comparison.
"""
        try:
            response = client.generate_content(
                model=getattr(settings, "GEMINI_MODEL", "gemini-2.5-flash"),
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": READER_EXPLAIN_SCHEMA,
                    "temperature": 0.3,
                }
            )
            raw = json.loads(response.text)
            if "explanation" in raw and "key_takeaways" in raw:
                result_data = raw
        except Exception as e:
            logger.warning(f"Gemini reader explain failed, falling back: {e}")

    if not result_data:
        result_data = _fallback_explanation(clean_text, mode)

    return InlineExplainResponse(
        selected_text=clean_text,
        mode=mode,
        explanation=result_data.get("explanation", ""),
        key_takeaways=result_data.get("key_takeaways", []),
        mnemonic_or_analogy=result_data.get("mnemonic_or_analogy")
    )
