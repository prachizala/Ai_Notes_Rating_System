"""
Exam Question Predictor Service for NoteIQ.
Analyzes academic notes and predicts university examination questions categorized by
2 Marks (Definitions), 5 Marks (Conceptual/Differences), and 10 Marks (In-Depth/Architecture).
"""

from typing import Any, Dict, List
from app.core.config import settings
from app.core.logging import logger
from app.services.llm import get_llm_client


EXAM_PREDICTION_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "questions": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "id": {"type": "INTEGER"},
                    "marks": {"type": "INTEGER"},
                    "category": {"type": "STRING"},
                    "question": {"type": "STRING"},
                    "probability": {"type": "STRING"},
                    "expected_key_points": {
                        "type": "ARRAY",
                        "items": {"type": "STRING"}
                    },
                    "location": {"type": "STRING"},
                    "bloom_level": {"type": "STRING"}
                },
                "required": [
                    "id", "marks", "category", "question", "probability",
                    "expected_key_points", "location", "bloom_level"
                ]
            }
        },
        "exam_tips": {
            "type": "ARRAY",
            "items": {"type": "STRING"}
        }
    },
    "required": ["questions", "exam_tips"]
}


SYSTEM_PROMPT = """You are a senior university examination paper setter and undergraduate moderator.
Analyze the provided notes and predict high-probability university examination questions.
Format your predictions into three tiers:
1. 2 Marks: Precise definitions, syntax, formulas, or 2 key differences. (High recall)
2. 5 Marks: Detailed concepts, algorithms, block diagrams, comparisons, or worked short examples.
3. 10 Marks: Comprehensive architecture, end-to-end lifecycle, complete implementation with code/diagrams.

Rules:
- Questions must be grounded strictly in the provided text.
- Provide 2 to 4 expected bullet points for what the examiner looks for in the model answer.
- Estimate exam probability as "Very High", "High", or "Medium".
- Cite the page/slide location if available in the text.
- Output valid JSON conforming to the schema.
"""


def _generate_fallback_predictions(document_title: str, text: str, summary: str) -> Dict[str, Any]:
    """Generates high-yield university exam questions from notes."""
    lines = [line.strip() for line in text.split("\n") if len(line.strip()) > 10]
    
    # Extract terms and concepts
    key_terms: List[str] = []
    for line in lines:
        if ":" in line and len(line.split(":")[0].split()) <= 4:
            term = line.split(":", 1)[0].strip().strip("-*•# ")
            if len(term) > 2 and term not in key_terms:
                key_terms.append(term)
        elif any(verb in line.lower() for verb in [" is defined as ", " is a ", " refers to "]):
            for verb in [" is defined as ", " is a ", " refers to "]:
                if verb in line:
                    t = line.split(verb, 1)[0].strip().strip("-*•# ")
                    if len(t.split()) <= 4 and t not in key_terms:
                        key_terms.append(t)
                    break

    if len(key_terms) < 3:
        key_terms.extend([f"Basics of {document_title}", f"Core Methods in {document_title}", f"Applications of {document_title}"])

    questions: List[Dict[str, Any]] = [
        # --- 2 Marks ---
        {
            "id": 1,
            "marks": 2,
            "category": "2 Marks (Definitions)",
            "question": f"Define {key_terms[0]}. State its primary purpose in {document_title}.",
            "probability": "Very High",
            "expected_key_points": [
                f"Precise one-sentence definition of {key_terms[0]}.",
                "Standard syntax or fundamental formula.",
                "One valid use-case or real-world example."
            ],
            "location": "Page 1",
            "bloom_level": "Recall"
        },
        {
            "id": 2,
            "marks": 2,
            "category": "2 Marks (Definitions)",
            "question": f"What is the significance of {key_terms[1] if len(key_terms) > 1 else 'Memory Allocation'}?",
            "probability": "High",
            "expected_key_points": [
                f"Definition and role of {key_terms[1] if len(key_terms) > 1 else 'Memory Allocation'}.",
                "Why it is preferred over alternative static constructs."
            ],
            "location": "Page 1",
            "bloom_level": "Understand"
        },
        {
            "id": 3,
            "marks": 2,
            "category": "2 Marks (Definitions)",
            "question": f"List two major differences between static and dynamic handling in {document_title}.",
            "probability": "Very High",
            "expected_key_points": [
                "Point 1: Compile-time vs Run-time binding.",
                "Point 2: Memory overhead and flexibility trade-offs."
            ],
            "location": "Page 2",
            "bloom_level": "Analyze"
        },

        # --- 5 Marks ---
        {
            "id": 4,
            "marks": 5,
            "category": "5 Marks (Conceptual)",
            "question": f"Explain the working principle of {key_terms[0]} with a suitable illustrative diagram or code snippet.",
            "probability": "Very High",
            "expected_key_points": [
                "Conceptual overview and working mechanism.",
                "Neat block diagram or commented code implementation.",
                "Step-by-step execution trace.",
                "Common syntax errors and handling techniques."
            ],
            "location": "Page 2",
            "bloom_level": "Apply"
        },
        {
            "id": 5,
            "marks": 5,
            "category": "5 Marks (Conceptual)",
            "question": f"Compare and contrast {key_terms[0]} with {key_terms[1] if len(key_terms) > 1 else 'Alternative Approach'} using tabular form.",
            "probability": "High",
            "expected_key_points": [
                "Tabular format with at least 4 distinct comparison parameters.",
                "Differences in memory efficiency, execution speed, and syntax complexity.",
                "Specific scenario recommendation for undergraduate lab assignments."
            ],
            "location": "Page 2",
            "bloom_level": "Analyze"
        },
        {
            "id": 6,
            "marks": 5,
            "category": "5 Marks (Conceptual)",
            "question": f"Discuss the common pitfalls and edge cases encountered when implementing {document_title}.",
            "probability": "Medium",
            "expected_key_points": [
                "Identification of at least two runtime or logic vulnerabilities.",
                "Demonstration of error resolution using defensive programming practices."
            ],
            "location": "Page 3",
            "bloom_level": "Evaluate"
        },

        # --- 10 Marks ---
        {
            "id": 7,
            "marks": 10,
            "category": "10 Marks (In-Depth)",
            "question": f"Describe the comprehensive architecture and complete lifecycle of {document_title}. Provide a complete end-to-end worked example.",
            "probability": "Very High",
            "expected_key_points": [
                "Detailed introduction with theoretical background and standards.",
                "Full architectural flow diagram with label descriptions.",
                "Complete syntax, compilation/execution steps, and sample input/output.",
                "Time and space complexity analysis under varying problem constraints.",
                "Critical summary of industry and semester curriculum relevance."
            ],
            "location": "Pages 1-4",
            "bloom_level": "Synthesize"
        },
        {
            "id": 8,
            "marks": 10,
            "category": "10 Marks (In-Depth)",
            "question": f"Design and implement a structured solution for {key_terms[0]}, discussing internal data structures and error handling strategies in detail.",
            "probability": "High",
            "expected_key_points": [
                "Problem definition and modular design breakdown.",
                "Clean, compilable code implementation with meaningful variable names.",
                "Boundary condition handling and validation checks.",
                "Comparison against alternative algorithmic solutions."
            ],
            "location": "Pages 2-4",
            "bloom_level": "Apply"
        }
    ]

    exam_tips = [
        "Definitions (2 Marks): Never skip the technical keyword; examiners look for exact terminology.",
        "5 Marks Questions: Always include a diagram or 4-point comparison table to secure full marks.",
        "10 Marks Questions: Start with a brief 3-line overview, draw the architectural diagram, write clean code/steps, and end with time/space complexity.",
        "Presentation: Underline keywords with a pen to catch the examiner's eye during speed grading."
    ]

    return {"questions": questions, "exam_tips": exam_tips}


class ExamPredictorService:
    """Service to predict semester university examination questions."""

    def predict_questions(self, document_title: str, text: str, summary: str = "") -> Dict[str, Any]:
        llm = get_llm_client()

        if settings.ENVIRONMENT == "test" or not settings.LLM_API_KEY or settings.LLM_PROVIDER == "fake":
            return _generate_fallback_predictions(document_title, text, summary)

        prompt_user = f"""Document Title: {document_title}
Summary: {summary}

Document Content:
\"\"\"
{text[:25000]}
\"\"\"

Generate 8 high-probability university examination questions:
- 3 questions of 2 Marks each (definitions, fundamental differences)
- 3 questions of 5 Marks each (conceptual diagrams, comparisons, workings)
- 2 questions of 10 Marks each (in-depth architecture, comprehensive lifecycle)
Include 3-4 golden exam presentation tips for undergraduate students.
"""
        try:
            result = llm.generate_json(
                system=SYSTEM_PROMPT,
                user=prompt_user,
                schema=EXAM_PREDICTION_SCHEMA
            )
            if "questions" in result and len(result["questions"]) >= 5:
                return result
        except Exception as e:
            logger.warning("LLM exam prediction error, using fallback: %s", str(e))

        return _generate_fallback_predictions(document_title, text, summary)


exam_predictor_service = ExamPredictorService()
