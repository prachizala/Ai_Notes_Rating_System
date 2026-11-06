"""
NotebookLM-Style Two-Host AI Audio Study Podcast Generator for NoteIQ.
Transforms written academic notes into a lively, engaging dialogue between two AI study partners:
- Alex (Inquisitive Co-host): Sets up concepts, asks relatable questions, clarifies student doubts.
- Sam (Subject Matter Specialist): Breaks down technical workings, gives industry analogies, highlights exam pitfalls.
"""

from typing import Any, Dict, List, Optional
from app.core.config import settings
from app.core.logging import logger
from app.services.llm import get_llm_client


PODCAST_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "episode_title": {"type": "STRING"},
        "estimated_duration_minutes": {"type": "INTEGER"},
        "turns": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "speaker": {"type": "STRING"},
                    "role": {"type": "STRING"},
                    "text": {"type": "STRING"},
                    "topic_tag": {"type": "STRING"}
                },
                "required": ["speaker", "role", "text", "topic_tag"]
            }
        },
        "key_takeaways": {
            "type": "ARRAY",
            "items": {"type": "STRING"}
        }
    },
    "required": ["episode_title", "estimated_duration_minutes", "turns", "key_takeaways"]
}


SYSTEM_PROMPT = """You are a lead audio producer creating a conversational educational study podcast (inspired by Google NotebookLM Audio Overviews).
Two friendly, charismatic co-hosts are discussing the uploaded college course notes:
- Host 1 (Alex): Inquisitive, asks natural questions, sets the stage, translates confusing ideas into student terms.
- Host 2 (Sam): Deep academic knowledge, explains the 'why' and 'how', brings in real-world engineering or management analogies, warns about common exam mistakes.

Rules:
- Make the dialogue sound natural, conversational, and energetic with realistic conversational transitions ("Oh interesting!", "Wait, so how does that work?", "Exactly!", "Here's the trick").
- Ground every technical claim strictly in the provided document text.
- Create between 8 and 14 dialogue turns.
- Output valid JSON conforming to the schema.
"""


def _generate_fallback_podcast(document_title: str, text: str, summary: str) -> Dict[str, Any]:
    """Generates an engaging, lively two-host study dialogue from note content."""
    lines = [line.strip() for line in text.split("\n") if len(line.strip()) > 10]
    
    concepts: List[str] = []
    for line in lines:
        if ":" in line and len(line.split(":")[0].split()) <= 4:
            term = line.split(":", 1)[0].strip().strip("-*•# ")
            if len(term) > 2 and term not in concepts:
                concepts.append(term)
        elif any(v in line.lower() for v in [" is a ", " is defined as ", " refers to "]):
            for v in [" is a ", " is defined as ", " refers to "]:
                if v in line:
                    t = line.split(v, 1)[0].strip().strip("-*•# ")
                    if len(t.split()) <= 4 and t not in concepts:
                        concepts.append(t)
                    break

    if len(concepts) < 2:
        concepts.extend([f"Basics of {document_title}", f"Applied Mechanisms in {document_title}"])

    c1 = concepts[0]
    c2 = concepts[1] if len(concepts) > 1 else "Core Workings"
    c3 = concepts[2] if len(concepts) > 2 else "Exam Strategy"

    turns = [
        {
            "speaker": "Alex",
            "role": "host",
            "text": f"Hey everyone, welcome back to the NoteIQ Audio Overview! Today we're diving into a really crucial set of notes on {document_title}. Sam, I know a lot of students find this chapter a bit heavy at first glance.",
            "topic_tag": "Intro"
        },
        {
            "speaker": "Sam",
            "role": "specialist",
            "text": f"Yeah, absolutely Alex! But honestly, once you see the underlying logic, it's actually super elegant. The entire document revolves around understanding {c1}.",
            "topic_tag": c1
        },
        {
            "speaker": "Alex",
            "role": "host",
            "text": f"Right! So let's start right there. How would you explain {c1} to someone studying this the night before their semester exam?",
            "topic_tag": c1
        },
        {
            "speaker": "Sam",
            "role": "specialist",
            "text": f"Think of it this way: instead of moving heavy data around, {c1} gives the system a direct handle to work with. The notes emphasize that accuracy here depends on getting the syntax and boundaries right.",
            "topic_tag": c1
        },
        {
            "speaker": "Alex",
            "role": "host",
            "text": f"Oh, that's such a clean way to picture it! And what about {c2}? The author spends a good chunk of time detailing how it behaves at runtime.",
            "topic_tag": c2
        },
        {
            "speaker": "Sam",
            "role": "specialist",
            "text": f"That's where things get practical. With {c2}, you're not locked into static compile-time limits. You request memory or resources dynamically as your program needs them, and release them when done.",
            "topic_tag": c2
        },
        {
            "speaker": "Alex",
            "role": "host",
            "text": "Wait, so is that where common errors happen? Like forgetting to release resources?",
            "topic_tag": "Pitfalls"
        },
        {
            "speaker": "Sam",
            "role": "specialist",
            "text": "Bingo! That's the classic 5-mark exam question right there. If you allocate without cleaning up, you get leaks or dangling references. Examiners love asking students to trace those exact bugs.",
            "topic_tag": "Pitfalls"
        },
        {
            "speaker": "Alex",
            "role": "host",
            "text": f"Examiners always find those edge cases! Now, what should students definitely memorize for the 10-mark long questions?",
            "topic_tag": "Exam Tips"
        },
        {
            "speaker": "Sam",
            "role": "specialist",
            "text": f"Two golden rules: first, always draw the architectural block diagram or memory layout. Second, write out a complete worked code snippet or derivation. A diagram alone guarantees you half the marks.",
            "topic_tag": "Exam Tips"
        },
        {
            "speaker": "Alex",
            "role": "host",
            "text": f"Awesome advice, Sam. That wraps up our quick deep dive into {document_title}. Be sure to flip through the flashcards on NoteIQ and test yourself before heading into exams!",
            "topic_tag": "Outro"
        }
    ]

    takeaways = [
        f"Master the core definition of {c1} with precise technical terminology.",
        f"Understand dynamic runtime behavior in {c2} and defensive resource management.",
        "Always illustrate 5 and 10 mark exam answers with block diagrams and clean syntax.",
        "Review common pitfalls like boundary conditions and memory cleanup."
    ]

    return {
        "episode_title": f"Deep Dive: Mastering {document_title}",
        "estimated_duration_minutes": 3,
        "turns": turns,
        "key_takeaways": takeaways
    }


class StudyPodcastService:
    """Service to generate NotebookLM-style spoken educational study podcasts."""

    def generate_podcast(self, document_title: str, text: str, summary: str = "") -> Dict[str, Any]:
        llm = get_llm_client()

        if settings.ENVIRONMENT == "test" or not settings.LLM_API_KEY or settings.LLM_PROVIDER == "fake":
            return _generate_fallback_podcast(document_title, text, summary)

        prompt_user = f"""Document Title: {document_title}
Summary: {summary}

Document Content:
\"\"\"
{text[:25000]}
\"\"\"

Create a lively 10-turn study podcast dialogue between Alex and Sam discussing the core concepts, practical analogies, and exam pitfalls of this document.
"""
        try:
            result = llm.generate_json(
                system=SYSTEM_PROMPT,
                user=prompt_user,
                schema=PODCAST_SCHEMA
            )
            if "turns" in result and len(result["turns"]) >= 6:
                return result
        except Exception as e:
            logger.warning("LLM podcast generation error, using fallback: %s", str(e))

        return _generate_fallback_podcast(document_title, text, summary)


study_podcast_service = StudyPodcastService()
