"""
Multi-Level Concept Simplifier Service for NoteIQ.
Provides:
1. ELI5 (Explain Like I'm 5 / Everyday real-world metaphor)
2. Industry Real-World Application (Tech company / corporate usage)
3. Hinglish Conversational Breakdown (Easy Indian college student slang)
4. Jargon Busters (Demystifying dense academic terminology)
"""

from typing import Any, Dict, List, Optional
from app.core.config import settings
from app.core.logging import logger
from app.services.llm import get_llm_client


SIMPLIFY_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "concepts": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "concept_name": {"type": "STRING"},
                    "eli5_analogy": {"type": "STRING"},
                    "industry_application": {"type": "STRING"},
                    "hinglish_breakdown": {"type": "STRING"},
                    "jargon_busters": {
                        "type": "ARRAY",
                        "items": {
                            "type": "OBJECT",
                            "properties": {
                                "term": {"type": "STRING"},
                                "simple_meaning": {"type": "STRING"}
                            },
                            "required": ["term", "simple_meaning"]
                        }
                    }
                },
                "required": [
                    "concept_name", "eli5_analogy", "industry_application",
                    "hinglish_breakdown", "jargon_busters"
                ]
            }
        }
    },
    "required": ["concepts"]
}


SYSTEM_PROMPT = """You are an engaging, world-class educator known for breaking down complex academic concepts so simply that even a complete beginner or a 5-year-old can instantly grasp them.
For the academic concepts in the provided note, generate:
1. ELI5 Analogy: An intuitive, unforgettable real-world metaphor (e.g., ordering food, postal mail, school lockers, traffic signals).
2. Industry Application: How top companies (Google, Netflix, Amazon, Banks) use this principle in real life.
3. Hinglish Breakdown: Natural, conversational Indian student phrasing ("Bhai simple si baat hai...") explaining the core logic without academic jargon.
4. Jargon Busters: 2-3 technical terms translated into plain, relatable English.

Rules:
- Never use condescending tone; keep it intellectually empowering and fun.
- Output strictly in valid JSON matching the schema.
"""


def _generate_fallback_simplification(document_title: str, text: str, custom_query: Optional[str] = None) -> Dict[str, Any]:
    """Generates rich multi-level explanations and analogies from notes."""
    lines = [line.strip() for line in text.split("\n") if len(line.strip()) > 8]

    # Candidate terms
    terms: List[str] = []
    if custom_query:
        terms.append(custom_query.strip())

    for line in lines:
        if ":" in line and len(line.split(":")[0].split()) <= 4:
            t = line.split(":", 1)[0].strip().strip("-*•# ")
            if len(t) > 2 and t not in terms:
                terms.append(t)
        elif any(verb in line.lower() for verb in [" is a ", " is defined as ", " refers to "]):
            for verb in [" is a ", " is defined as ", " refers to "]:
                if verb in line:
                    t = line.split(verb, 1)[0].strip().strip("-*•# ")
                    if len(t.split()) <= 4 and t not in terms:
                        terms.append(t)
                    break

    if len(terms) < 3:
        terms.extend([
            f"Core Mechanism of {document_title}",
            f"Dynamic Execution in {document_title}",
            f"Resource Lifecycle in {document_title}"
        ])

    concepts: List[Dict[str, Any]] = []

    for idx, term in enumerate(terms[:4]):
        if "pointer" in term.lower() or "address" in term.lower():
            eli5 = "Think of a Pointer like a GPS location or house address written on a sticky note. Instead of carrying the entire house in your pocket, you just carry the slip with the address on it!"
            industry = "Used in Operating Systems (Linux Kernel) and High-Frequency Trading systems to access gigabytes of memory instantaneously without copying heavy data packets."
            hinglish = "Bhai simple si baat hai: Pointer koi data khud store nahi karta, bas batata hai ki wo data RAM ke kis ghar (memory address) me baitha hai."
            jargon = [
                {"term": "Dereferencing (*p)", "simple_meaning": "Ghar ke address par jakar darwaza kholna aur andar ka saman dekhna."},
                {"term": "Memory Leak", "simple_meaning": "Hotel room book karke chabi phenk dena aur checkout karna bhool jana."}
            ]
        elif "malloc" in term.lower() or "memory" in term.lower() or "allocation" in term.lower():
            eli5 = "Imagine an empty parking lot. When your car arrives, the security guard marks a parking slot for you. When you leave, you must inform them so another car can park."
            industry = "Game engines (like Unreal Engine) use dynamic memory allocation so that 3D characters and explosions only consume RAM when they appear on your screen."
            hinglish = "Program run hote waqt jitni memory chahiye utni maangna (Dynamic). Pehle se fix karke RAM waste na karna."
            jargon = [
                {"term": "Heap Memory", "simple_meaning": "Khula maidan jahan jab chahe zameen maang sakte ho aur kaam khatam hone par wapas karni hoti hai."},
                {"term": "Dangling Pointer", "simple_meaning": "Us ghar ka address jo tod diya gaya hai, par address abhi bhi aapke note par likha hai."}
            ]
        else:
            eli5 = f"Imagine '{term}' like a universal remote control. Instead of standing up and pressing buttons on 5 different machines, it gives you a clean single interface to handle everything effortlessly."
            industry = f"Netflix and Amazon use the architecture behind '{term}' to serve millions of simultaneous video streams without crashing their cloud servers."
            hinglish = f"Bhai concept ekdam seedha hai: '{term}' ka matlab hai complicated kaam ko chhote modular steps me todna taaki system fast aur error-free chale."
            jargon = [
                {"term": "Optimization", "simple_meaning": "Kam petrol aur kam time me manzil tak pahunchna."},
                {"term": "Scalability", "simple_meaning": "10 log aaye ya 10 lakh log aaye, website ka smoothly chalna."}
            ]

        concepts.append({
            "concept_name": term,
            "eli5_analogy": eli5,
            "industry_application": industry,
            "hinglish_breakdown": hinglish,
            "jargon_busters": jargon
        })

    return {"concepts": concepts}


class ConceptSimplifierService:
    """Service to demystify complex academic notes into accessible beginner analogies."""

    def explain_concepts(self, document_title: str, text: str, custom_query: Optional[str] = None) -> Dict[str, Any]:
        llm = get_llm_client()

        if settings.ENVIRONMENT == "test" or not settings.LLM_API_KEY or settings.LLM_PROVIDER == "fake":
            return _generate_fallback_simplification(document_title, text, custom_query)

        query_prompt = f"Target Specific Query: {custom_query}" if custom_query else "Select 3-4 central foundational concepts."

        prompt_user = f"""Document Title: {document_title}
{query_prompt}

Document Content:
\"\"\"
{text[:25000]}
\"\"\"

For each concept, provide:
1. ELI5 everyday metaphor
2. Real-world industry application (how Google/Netflix/Banks use it)
3. Conversational Hinglish explanation
4. Jargon busters (2 technical terms simplified)
"""
        try:
            result = llm.generate_json(
                system=SYSTEM_PROMPT,
                user=prompt_user,
                schema=SIMPLIFY_SCHEMA
            )
            if "concepts" in result and len(result["concepts"]) >= 1:
                return result
        except Exception as e:
            logger.warning("LLM simplifier error, falling back: %s", str(e))

        return _generate_fallback_simplification(document_title, text, custom_query)


concept_simplifier_service = ConceptSimplifierService()
