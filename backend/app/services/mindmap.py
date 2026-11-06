"""
Mind Map & Visual Flowchart Service for NoteIQ.
Transforms linear academic notes into interactive hierarchical concept maps and Mermaid diagrams.
"""

import re
from typing import Any, Dict, List
from app.core.config import settings
from app.core.logging import logger
from app.services.llm import get_llm_client


MINDMAP_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "diagram_type": {"type": "STRING"},
        "mermaid_code": {"type": "STRING"},
        "nodes": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "id": {"type": "STRING"},
                    "label": {"type": "STRING"},
                    "description": {"type": "STRING"},
                    "category": {"type": "STRING"}
                },
                "required": ["id", "label", "description", "category"]
            }
        },
        "edges": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "source": {"type": "STRING"},
                    "target": {"type": "STRING"},
                    "label": {"type": "STRING"}
                },
                "required": ["source", "target"]
            }
        },
        "summary": {"type": "STRING"}
    },
    "required": ["diagram_type", "mermaid_code", "nodes", "edges", "summary"]
}


SYSTEM_PROMPT = """You are an expert educational knowledge graph and diagram engineer.
Your task is to convert academic course notes into a structured Concept Mind Map and Flowchart.
1. Generate valid Mermaid.js graph code (e.g. `graph TD` with quotes around node labels: `A["Label"] --> B["Label"]`).
2. Extract the nodes (with id, clean short label, 1-2 sentence description, category: core | subtopic | detail | example).
3. Extract directed relationships (edges) connecting parent concepts to child concepts.

Rules:
- NEVER use syntax that breaks Mermaid (always put quotes around labels: `id["Node Text"]`).
- Avoid parentheses or special symbols inside unquoted node names.
- Output valid JSON conforming to the schema.
"""


def _clean_mermaid_label(text: str) -> str:
    """Strips quotes and characters that could break mermaid rendering."""
    clean = re.sub(r'["\(\)\[\]\{\}]', '', text).strip()
    return clean[:35] if clean else "Concept"


def _generate_fallback_mindmap(document_title: str, text: str, summary: str) -> Dict[str, Any]:
    """Deterministically extracts hierarchical concept nodes and generates a valid Mermaid diagram."""
    lines = [line.strip() for line in text.split("\n") if len(line.strip()) > 8]

    # Extract terms
    subtopics: List[Dict[str, str]] = []
    for line in lines:
        if ":" in line and len(line.split(":")[0].split()) <= 4:
            parts = line.split(":", 1)
            term = parts[0].strip().strip("-*•# ")
            desc = parts[1].strip()
            if len(term) > 2 and len(desc) > 8:
                subtopics.append({"name": term, "desc": desc})
        elif any(verb in line.lower() for verb in [" is a ", " is defined as ", " refers to "]):
            for verb in [" is a ", " is defined as ", " refers to "]:
                if verb in line:
                    parts = line.split(verb, 1)
                    term = parts[0].strip().strip("-*•# ")
                    if len(term.split()) <= 4:
                        subtopics.append({"name": term, "desc": f"{term} {verb} {parts[1].strip()}"})
                    break

    # If few subtopics, extract based on line segments
    if len(subtopics) < 3:
        for line in lines[:5]:
            words = line.split()
            if len(words) >= 4:
                term = " ".join(words[:3]).strip("-*•# ")
                subtopics.append({"name": term, "desc": line})

    # Deduplicate
    seen = set()
    unique_subtopics = []
    for s in subtopics:
        norm = s["name"].lower()
        if norm not in seen:
            seen.add(norm)
            unique_subtopics.append(s)

    if len(unique_subtopics) < 3:
        unique_subtopics.extend([
            {"name": "Core Principles", "desc": f"Foundational theoretical rules of {document_title}."},
            {"name": "Key Mechanisms", "desc": f"Execution workflows and operations in {document_title}."},
            {"name": "Worked Examples", "desc": f"Illustrative implementation code and problem sets."},
            {"name": "Exam Key Points", "desc": f"Essential points to remember for semester exams."}
        ])

    root_label = _clean_mermaid_label(document_title)
    nodes: List[Dict[str, Any]] = [
        {
            "id": "root",
            "label": root_label,
            "description": summary or f"Foundational study document: {document_title}",
            "category": "core"
        }
    ]
    edges: List[Dict[str, Any]] = []

    mermaid_lines = [
        "graph TD",
        f'  root["{root_label}"]:::coreClass'
    ]

    for idx, s in enumerate(unique_subtopics[:5], 1):
        node_id = f"sub_{idx}"
        clean_name = _clean_mermaid_label(s["name"])
        nodes.append({
            "id": node_id,
            "label": clean_name,
            "description": s["desc"][:200],
            "category": "subtopic"
        })
        edges.append({
            "source": "root",
            "target": node_id,
            "label": "includes"
        })
        mermaid_lines.append(f'  root -->|includes| {node_id}["{clean_name}"]')

        # Add a leaf detail
        detail_id = f"det_{idx}"
        detail_words = s["desc"].split()
        detail_label = _clean_mermaid_label(" ".join(detail_words[:3])) if len(detail_words) >= 3 else f"{clean_name} Detail"
        nodes.append({
            "id": detail_id,
            "label": detail_label,
            "description": s["desc"][:250],
            "category": "detail"
        })
        edges.append({
            "source": node_id,
            "target": detail_id,
            "label": "detail"
        })
        mermaid_lines.append(f'  {node_id} --> {detail_id}["{detail_label}"]')

    mermaid_lines.append("  classDef coreClass fill:#4f46e5,stroke:#3730a3,stroke-width:2px,color:#fff,font-weight:bold")
    mermaid_lines.append("  classDef default fill:#f8fafc,stroke:#cbd5e1,stroke-width:1px,color:#0f172a")

    mermaid_code = "\n".join(mermaid_lines)

    return {
        "diagram_type": "hierarchy",
        "mermaid_code": mermaid_code,
        "nodes": nodes,
        "edges": edges,
        "summary": f"Interactive structural concept hierarchy mapped across {len(nodes)} distinct nodes from {document_title}."
    }


class MindMapService:
    """Service to generate mind maps and flowcharts from notes."""

    def generate_mindmap(self, document_title: str, text: str, summary: str = "") -> Dict[str, Any]:
        llm = get_llm_client()

        if settings.ENVIRONMENT == "test" or not settings.LLM_API_KEY or settings.LLM_PROVIDER == "fake":
            return _generate_fallback_mindmap(document_title, text, summary)

        prompt_user = f"""Document Title: {document_title}
Summary: {summary}

Document Content:
\"\"\"
{text[:25000]}
\"\"\"

Create a clean, comprehensive Mermaid.js Mind Map / Flowchart representing the concepts in this note.
Include 6 to 10 nodes with directed edges connecting parent concepts to details and examples.
"""
        try:
            result = llm.generate_json(
                system=SYSTEM_PROMPT,
                user=prompt_user,
                schema=MINDMAP_SCHEMA
            )
            if "mermaid_code" in result and "nodes" in result and len(result["nodes"]) >= 3:
                return result
        except Exception as e:
            logger.warning("LLM mindmap generation error, using fallback: %s", str(e))

        return _generate_fallback_mindmap(document_title, text, summary)


mindmap_service = MindMapService()
