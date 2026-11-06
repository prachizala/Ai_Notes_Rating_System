"""
7-Day Spaced Repetition Exam Study Planner Service for NoteIQ.
Transforms course notes into a science-backed, day-by-day revision schedule.
"""

from typing import Any, Dict, List, Optional
import json
import re
from app.core.config import settings
from app.core.logging import logger
from app.services.llm import get_llm_client
from app.schemas.study_planner import DayPlan, StudyPlannerResponse


STUDY_PLANNER_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "planner_strategy": {"type": "STRING"},
        "days": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "day_number": {"type": "INTEGER"},
                    "theme": {"type": "STRING"},
                    "estimated_minutes": {"type": "INTEGER"},
                    "focus_topics": {"type": "ARRAY", "items": {"type": "STRING"}},
                    "tasks": {"type": "ARRAY", "items": {"type": "STRING"}},
                    "recall_challenge": {"type": "STRING"},
                    "recommended_tool": {"type": "STRING"}
                },
                "required": [
                    "day_number",
                    "theme",
                    "estimated_minutes",
                    "focus_topics",
                    "tasks",
                    "recall_challenge",
                    "recommended_tool"
                ]
            }
        },
        "general_exam_tips": {
            "type": "ARRAY",
            "items": {"type": "STRING"}
        }
    },
    "required": ["planner_strategy", "days", "general_exam_tips"]
}


def _generate_fallback_study_plan(title: str, text: str, subject_name: str) -> Dict[str, Any]:
    """Heuristic fallback study plan based on Ebbinghaus spaced repetition."""
    lines = [line.strip() for line in text.split("\n") if len(line.strip()) > 20 and not line.strip().startswith("#")]
    topics = [re.sub(r'^[0-9\.\-\*\s]+', '', l) for l in lines[:6]] if lines else []
    
    t1 = topics[0] if topics else f"{title} Basics"
    t2 = topics[1] if len(topics) > 1 else f"{title} Core Concepts"
    t3 = topics[2] if len(topics) > 2 else f"{title} Architectural Flow"
    t4 = topics[3] if len(topics) > 3 else f"{title} Advanced Topics"

    days = [
        {
            "day_number": 1,
            "theme": "Foundation & Core Terminology",
            "estimated_minutes": 45,
            "focus_topics": [t1[:45], "Essential Vocabulary", "Scope & Definitions"],
            "tasks": [
                f"Read the introductory notes on {t1[:40]}.",
                "Write down verbatim definitions of the 5 primary keywords in your notebook.",
                "Draw a high-level mind map connecting the subject foundations."
            ],
            "recall_challenge": f"Close your eyes: Can you explain {t1[:30]} in 2 sentences without looking at the notes?",
            "recommended_tool": "Mind Map & Flashcards"
        },
        {
            "day_number": 2,
            "theme": "Deep-Dive Mechanisms & Working Principles",
            "estimated_minutes": 50,
            "focus_topics": [t2[:45], "Component Interactions", "Algorithmic / Logical Flow"],
            "tasks": [
                f"Study how {t2[:35]} operates step-by-step.",
                "Annotate diagrams and trace data flow between sub-components.",
                "Note down differences between standard cases and edge conditions."
            ],
            "recall_challenge": f"What are the sequential steps in the process of {t2[:30]}?",
            "recommended_tool": "Concept Simplifier (ELI5)"
        },
        {
            "day_number": 3,
            "theme": "Comparative Analysis & Real-World Examples",
            "estimated_minutes": 45,
            "focus_topics": [t3[:45], "Case Studies", "Comparison Tables"],
            "tasks": [
                f"Analyze practical applications and sample problems in {t3[:35]}.",
                "Construct a side-by-side distinction table between key concepts.",
                "Solve 2 practice questions from previous university papers."
            ],
            "recall_challenge": "What is the single biggest real-world advantage of this approach over older alternatives?",
            "recommended_tool": "1-Page Cheat Sheet"
        },
        {
            "day_number": 4,
            "theme": "1st Spaced Review & Active Recall Quiz",
            "estimated_minutes": 40,
            "focus_topics": ["Review Days 1-3", "Retention Self-Check", "Knowledge Gap Identification"],
            "tasks": [
                "Complete the NoteIQ Flashcard Deck with spaced repetition active recall.",
                "Attempt the 10-question Active Recall Quiz without referring to notes.",
                "Mark any concepts scored below 70% for targeted revision."
            ],
            "recall_challenge": "Explain the concept you found hardest on Day 2 in simple Hinglish or conversational terms.",
            "recommended_tool": "Flashcards & Quiz"
        },
        {
            "day_number": 5,
            "theme": "High-Weightage & University 10-Mark Questions",
            "estimated_minutes": 60,
            "focus_topics": [t4[:45], "10-Mark Descriptive Questions", "Structured Answer Formatting"],
            "tasks": [
                "Review the Predicted Exam Questions (5M and 10M tier).",
                "Write a complete 10-mark answer on paper using headers, bullet points, and a diagram.",
                "Time yourself: Limit long answers to 12 minutes max."
            ],
            "recall_challenge": "What are the 3 mandatory diagrams or formulas required to secure full 10/10 marks?",
            "recommended_tool": "Exam Questions (2/5/10M)"
        },
        {
            "day_number": 6,
            "theme": "2nd Spaced Review & Oral Viva Simulation",
            "estimated_minutes": 45,
            "focus_topics": ["Edge Cases", "Common Student Misconceptions", "Oral Articulation"],
            "tasks": [
                "Review the Exam Traps & Pitfalls section on the 1-Page Cheat Sheet.",
                "Simulate a real viva examination: Answer 4 oral exam questions verbally using the mic.",
                "Refine missing key points highlighted by the AI Examiner."
            ],
            "recall_challenge": "What frequent misconception do students make during calculations or code traces in this topic?",
            "recommended_tool": "AI Viva Voce (Oral Exam)"
        },
        {
            "day_number": 7,
            "theme": "Mock Sprint & Final Rapid Revision",
            "estimated_minutes": 35,
            "focus_topics": ["Formula & Syntax Cramming", "Rapid Recall Mnemonics", "Exam Day Strategy"],
            "tasks": [
                "Print out or review the 1-Page Exam Cheat Sheet one last time.",
                "Listen to the 3-minute Audio Study Podcast during your morning walk or commute.",
                "Sleep early! Good cognitive sleep improves memory consolidation by 30%."
            ],
            "recall_challenge": "Recite all rapid mnemonics and core formulas in under 2 minutes.",
            "recommended_tool": "1-Page Cheat Sheet & Audio Podcast"
        }
    ]

    return {
        "planner_strategy": "Ebbinghaus Spaced Repetition (Days 1-3 Learning, Day 4 Active Recall Review, Day 5 Deep Problem Solving, Day 6 Oral Viva Stress-Test, Day 7 Final Mock Consolidation).",
        "days": days,
        "general_exam_tips": [
            "Always allocate 5 minutes at the beginning of the exam to read all questions and prioritize high-mark questions.",
            "Draw clear, labeled flowcharts and diagrams — university evaluators award up to 40% marks for structured illustrations.",
            "Use standard bullet points with underlined keywords rather than long unbroken essay paragraphs."
        ]
    }


def generate_study_plan(
    document_id: str,
    document_title: str,
    document_text: str,
    subject_name: str = "Academic Course"
) -> StudyPlannerResponse:
    """Generates a customized 7-Day Spaced Repetition Study Planner."""
    client = get_llm_client()
    plan_data: Optional[Dict[str, Any]] = None

    if client and getattr(settings, "GEMINI_API_KEY", None):
        truncated_text = document_text[:5000]
        prompt = f"""
You are an expert academic mentor and study strategist designing a 7-Day Spaced Repetition Exam Revision Plan for university students.

Course Subject: {subject_name}
Document Title: {document_title}

Content Extract:
{truncated_text}

Design a rigorous, highly actionable 7-Day Revision Timetable following cognitive science & Ebbinghaus Spaced Repetition:
- Day 1: Foundation & Core Terminology (40-45 mins)
- Day 2: Deep-Dive Mechanisms & Working Principles (45-55 mins)
- Day 3: Comparative Analysis, Examples & Diagrams (40-50 mins)
- Day 4: 1st Spaced Review & Active Recall Testing (35-45 mins)
- Day 5: High-Weightage & 10-Mark Question Mastery (55-65 mins)
- Day 6: 2nd Spaced Review, Exam Traps & Oral Viva Voce Prep (40-45 mins)
- Day 7: Final Mock Sprint & Rapid Formula/Mnemonic Cramming (30-40 mins)

For each day, specify:
- day_number: 1 to 7
- theme: Punchy day theme
- estimated_minutes: Integer minutes (30 to 65)
- focus_topics: 2-3 specific topics or subconcepts from this document
- tasks: 3 specific, actionable learning steps for the student
- recall_challenge: 1 powerful active-recall question to test themselves before bed
- recommended_tool: Recommended NoteIQ tool (e.g. "Mind Map", "Flashcards & Quiz", "ELI5 Simplifier", "AI Viva Voce", "1-Page Cheat Sheet", "Audio Podcast")

Also include:
- planner_strategy: 1-2 sentence overview of the pedagogical strategy
- general_exam_tips: 3 high-impact exam hall writing tips for university scoring
"""
        try:
            response = client.generate_content(
                model=getattr(settings, "GEMINI_MODEL", "gemini-2.5-flash"),
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": STUDY_PLANNER_SCHEMA,
                    "temperature": 0.3,
                }
            )
            raw = json.loads(response.text)
            if "days" in raw and len(raw["days"]) == 7:
                plan_data = raw
        except Exception as e:
            logger.warning(f"Gemini study planner generation failed, using fallback: {e}")

    if not plan_data:
        plan_data = _generate_fallback_study_plan(document_title, document_text, subject_name)

    day_objects = [
        DayPlan(
            day_number=d.get("day_number", i + 1),
            theme=d.get("theme", f"Day {i+1} Revision"),
            estimated_minutes=d.get("estimated_minutes", 45),
            focus_topics=d.get("focus_topics", []),
            tasks=d.get("tasks", []),
            recall_challenge=d.get("recall_challenge", "Summarize what you learned today."),
            recommended_tool=d.get("recommended_tool", "Flashcards & Quiz")
        )
        for i, d in enumerate(plan_data.get("days", []))
    ]

    total_mins = sum(d.estimated_minutes for d in day_objects)
    total_hours = round(total_mins / 60.0, 1)

    return StudyPlannerResponse(
        document_id=document_id,
        document_title=document_title,
        subject_name=subject_name,
        total_days=len(day_objects),
        total_estimated_hours=total_hours,
        planner_strategy=plan_data.get("planner_strategy", "Spaced Repetition & Active Recall"),
        days=day_objects,
        general_exam_tips=plan_data.get("general_exam_tips", [
            "Organize answers using headings and bullet points.",
            "Support theoretical answers with illustrative diagrams.",
            "Keep 10 minutes at the end for checking question numbering."
        ])
    )
