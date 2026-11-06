"""
Interactive AI Viva Voce (Oral Exam Simulator) Service for NoteIQ.
Generates oral exam questions with examiner personas and grades student responses in real-time.
"""

from typing import Any, Dict, List, Optional
import json
import re
from app.core.config import settings
from app.core.logging import logger
from app.services.llm import get_llm_client
from app.schemas.viva import VivaQuestion, VivaSessionResponse, VivaEvaluationResponse


VIVA_QUESTIONS_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "questions": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "id": {"type": "INTEGER"},
                    "question": {"type": "STRING"},
                    "difficulty": {"type": "STRING"},
                    "examiner_tip": {"type": "STRING"},
                    "ideal_answer_key": {"type": "STRING"},
                    "follow_up_hint": {"type": "STRING"}
                },
                "required": ["id", "question", "difficulty", "examiner_tip", "ideal_answer_key", "follow_up_hint"]
            }
        }
    },
    "required": ["questions"]
}

VIVA_EVALUATION_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "score": {"type": "INTEGER"},
        "examiner_verdict": {"type": "STRING"},
        "feedback": {"type": "STRING"},
        "strengths": {"type": "ARRAY", "items": {"type": "STRING"}},
        "missing_key_points": {"type": "ARRAY", "items": {"type": "STRING"}},
        "improved_answer": {"type": "STRING"}
    },
    "required": ["score", "examiner_verdict", "feedback", "strengths", "missing_key_points", "improved_answer"]
}


def _generate_fallback_viva_questions(title: str, text: str) -> List[Dict[str, Any]]:
    """Heuristic fallback viva questions if LLM is unavailable."""
    lines = [line.strip() for line in text.split("\n") if len(line.strip()) > 25 and not line.strip().startswith("#")]
    sample_topics = [re.sub(r'^[0-9\.\-\*\s]+', '', l) for l in lines[:6]] if lines else []
    
    q1_topic = sample_topics[0] if sample_topics else f"{title} fundamentals"
    q2_topic = sample_topics[1] if len(sample_topics) > 1 else f"working mechanism of {title}"
    q3_topic = sample_topics[2] if len(sample_topics) > 2 else f"practical applications of {title}"

    return [
        {
            "id": 1,
            "question": f"Can you define the core principle of {q1_topic[:50]} and explain why it is essential in this subject?",
            "difficulty": "Easy",
            "examiner_tip": "Start with a direct definition in 1-2 clear sentences before elaborating on practical relevance.",
            "ideal_answer_key": f"Defines {q1_topic[:40]} precisely, states the primary purpose, and mentions its role in system design or theory.",
            "follow_up_hint": "Be prepared if asked how this differs from traditional alternatives."
        },
        {
            "id": 2,
            "question": f"Walk me through the key process or architecture involved in {q2_topic[:50]}. How do components interact?",
            "difficulty": "Medium",
            "examiner_tip": "Break your answer into step-by-step phases (e.g. Input -> Processing -> Output).",
            "ideal_answer_key": f"Describes structural components, information flow, and critical dependencies accurately.",
            "follow_up_hint": "What happens if one of these intermediate steps encounters an error or bottleneck?"
        },
        {
            "id": 3,
            "question": f"In a real-world scenario or project, where would you choose to apply {q3_topic[:50]} over competing approaches?",
            "difficulty": "Hard",
            "examiner_tip": "Compare trade-offs like performance, cost, simplicity, or scalability.",
            "ideal_answer_key": f"Clear rationale with comparative trade-offs, advantages, and constraints.",
            "follow_up_hint": "Mention any edge cases or limitations where this method might fail."
        },
        {
            "id": 4,
            "question": f"What common misconception or frequent pitfall do students encounter when implementing or analyzing {title}?",
            "difficulty": "Medium",
            "examiner_tip": "Highlight edge cases, syntax nuances, or theoretical limits.",
            "ideal_answer_key": "Identifies realistic edge cases, assumptions that break, or frequent exam calculation traps.",
            "follow_up_hint": "How would you debug or prevent that pitfall in practice?"
        }
    ]


def generate_viva_questions(
    document_id: str,
    document_title: str,
    document_text: str
) -> VivaSessionResponse:
    """Generate viva voce examination questions for a document."""
    client = get_llm_client()
    questions_data: Optional[List[Dict[str, Any]]] = None

    if client and getattr(settings, "GEMINI_API_KEY", None):
        truncated_text = document_text[:5000]
        prompt = f"""
You are a distinguished university professor conducting an oral viva voce examination on:
Document Title: {document_title}

Content Extract:
{truncated_text}

Generate 4 realistic viva voce questions ranging from fundamental definitions to architectural mechanisms and real-world trade-offs:
1. Question 1 (Easy / Fundamental Concept definition)
2. Question 2 (Medium / Architecture / Working mechanism)
3. Question 3 (Hard / Real-world trade-off / Comparative evaluation)
4. Question 4 (Medium-Hard / Critical edge case, pitfall, or application scenario)

For each question provide:
- id: 1, 2, 3, 4
- question: Clear, conversational oral exam question as an external examiner would ask
- difficulty: Easy, Medium, or Hard
- examiner_tip: Advice for the student on how an examiner expects them to structure their verbal answer
- ideal_answer_key: 2-3 sentence summary of the key keywords, concepts, and points the student MUST mention
- follow_up_hint: What the examiner will probe if the student answers well
"""
        try:
            response = client.generate_content(
                model=getattr(settings, "GEMINI_MODEL", "gemini-2.5-flash"),
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": VIVA_QUESTIONS_SCHEMA,
                    "temperature": 0.3,
                }
            )
            raw = json.loads(response.text)
            if "questions" in raw and len(raw["questions"]) >= 3:
                questions_data = raw["questions"]
        except Exception as e:
            logger.warning(f"Gemini viva generation failed, falling back to heuristic: {e}")

    if not questions_data:
        questions_data = _generate_fallback_viva_questions(document_title, document_text)

    # Convert to schema objects
    viva_questions = [
        VivaQuestion(
            id=idx + 1,
            question=q.get("question", ""),
            difficulty=q.get("difficulty", "Medium"),
            examiner_tip=q.get("examiner_tip", "Answer clearly and concisely."),
            ideal_answer_key=q.get("ideal_answer_key", ""),
            follow_up_hint=q.get("follow_up_hint", "Be ready for follow-up details.")
        )
        for idx, q in enumerate(questions_data)
    ]

    return VivaSessionResponse(
        document_id=document_id,
        document_title=document_title,
        total_questions=len(viva_questions),
        questions=viva_questions
    )


def evaluate_viva_answer(
    question: str,
    student_answer: str,
    ideal_answer_key: Optional[str] = None,
    difficulty: str = "Medium"
) -> VivaEvaluationResponse:
    """Evaluates a student's verbal/written answer to a viva voce question."""
    answer_clean = student_answer.strip()
    word_count = len(answer_clean.split())

    # Quick rejection if answer is practically empty
    if word_count < 3:
        return VivaEvaluationResponse(
            score=1,
            max_score=10,
            examiner_verdict="Answer too brief or unattempted",
            feedback="The examiner noticed you barely attempted the question. In an oral exam, always state the definition or basic terms even if uncertain.",
            strengths=[],
            missing_key_points=["Basic technical definition", "Elaboration with example or keywords"],
            improved_answer=ideal_answer_key or "A comprehensive answer should start with the core term definition followed by 1 practical application."
        )

    client = get_llm_client()
    if client and getattr(settings, "GEMINI_API_KEY", None):
        prompt = f"""
You are an experienced university viva voce external examiner evaluating a student's oral response.

Question: {question}
Difficulty: {difficulty}
Target Answer Key: {ideal_answer_key or "Accurate technical terminology and conceptual clarity"}

Student's Answer:
"{answer_clean}"

Evaluate objectively:
1. Score out of 10 (integer between 0 and 10 based on accuracy, completeness, and clarity).
2. Examiner verdict: Single punchy title like "Outstanding & Articulate", "Solid Understanding", "Partially Correct - Lacks Depth", or "Vague / Off-Track".
3. Feedback: 2-3 sentences of constructive examiner feedback as spoken in a viva.
4. Strengths: 1-2 specific points the student articulated well.
5. Missing Key Points: 1-3 specific critical concepts, keywords, or nuances the student missed or glossed over.
6. Improved Answer: An ideal, articulate 3-4 sentence response that would score full 10/10 marks in a university viva.
"""
        try:
            response = client.generate_content(
                model=getattr(settings, "GEMINI_MODEL", "gemini-2.5-flash"),
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": VIVA_EVALUATION_SCHEMA,
                    "temperature": 0.2,
                }
            )
            raw = json.loads(response.text)
            return VivaEvaluationResponse(
                score=max(0, min(10, int(raw.get("score", 7)))),
                max_score=10,
                examiner_verdict=raw.get("examiner_verdict", "Good Effort"),
                feedback=raw.get("feedback", "Good explanation with reasonable conceptual clarity."),
                strengths=raw.get("strengths", ["Identified core terminology"]),
                missing_key_points=raw.get("missing_key_points", ["Could include more specific examples"]),
                improved_answer=raw.get("improved_answer", ideal_answer_key or "Clear definitions and examples.")
            )
        except Exception as e:
            logger.warning(f"Gemini viva evaluation failed, falling back to heuristic: {e}")

    # Heuristic evaluation fallback
    key_words_target = set(re.findall(r'\b[a-zA-Z]{4,}\b', (ideal_answer_key or question).lower()))
    student_words = set(re.findall(r'\b[a-zA-Z]{4,}\b', answer_clean.lower()))
    matches = key_words_target.intersection(student_words)
    overlap_ratio = len(matches) / max(len(key_words_target), 1)

    base_score = 5
    if word_count > 30 and overlap_ratio > 0.25:
        base_score = 8
        verdict = "Strong & Well-Articulated"
        feedback = "You demonstrated good command over the subject and explained the concept logically."
    elif word_count > 15 and overlap_ratio > 0.15:
        base_score = 7
        verdict = "Solid Answer"
        feedback = "You covered the main idea accurately. Adding more specific technical terminology would yield full marks."
    elif word_count > 8:
        base_score = 5
        verdict = "Partially Correct"
        feedback = "You have an intuitive grasp, but the response needs more structural rigor and technical depth."
    else:
        base_score = 3
        verdict = "Needs More Elaboration"
        feedback = "Your answer touched on the concept, but was too brief for an examiner to award full marks."

    strengths = ["Communicated the concept with confidence"]
    if matches:
        strengths.append(f"Correctly referenced key concepts: {', '.join(list(matches)[:2])}")

    missing = ["Provide an explicit real-world example or edge case to solidify the answer"]
    if len(matches) < 2:
        missing.append("Incorporate standard textbook terminology to make your answer sound authoritative")

    return VivaEvaluationResponse(
        score=base_score,
        max_score=10,
        examiner_verdict=verdict,
        feedback=feedback,
        strengths=strengths,
        missing_key_points=missing,
        improved_answer=ideal_answer_key or f"To achieve 10/10, start by directly stating what it is, then highlight its key components and 1 real-world use case."
    )
