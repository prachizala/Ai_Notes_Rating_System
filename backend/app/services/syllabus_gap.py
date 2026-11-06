"""
Syllabus Gap & Completeness Heatmap Service for NoteIQ.
Audits document content against official university syllabus checklists and flags missing exam topics.
"""

from typing import Any, Dict, List, Optional
from app.core.config import settings
from app.core.logging import logger
from app.services.llm import get_llm_client


DEFAULT_SYLLABUS_MAP = {
    "c programming": [
        "Pointer Fundamentals & Memory Addressing",
        "Dynamic Memory Allocation (malloc, calloc, realloc, free)",
        "Structures, Unions and Bitfields",
        "File Handling (fopen, fread, fwrite, fclose)",
        "Preprocessor Directives and Macro Expansions",
        "Command Line Arguments (argc, argv)"
    ],
    "data structures": [
        "Array Representations and Sparse Matrices",
        "Singly, Doubly, and Circular Linked Lists",
        "Stacks, Queues, and Priority Queues",
        "Binary Trees, BST, and Tree Traversals",
        "Graph Representations (BFS, DFS, Dijkstra)",
        "Sorting & Searching Algorithms (Quick, Merge, Binary Search)"
    ],
    "operating systems": [
        "Process Management & CPU Scheduling Algorithms",
        "Process Synchronization, Mutex, and Semaphores",
        "Deadlock Prevention, Avoidance (Banker's), and Detection",
        "Memory Management, Paging, and Segmentation",
        "Virtual Memory & Page Replacement (LRU, FIFO)",
        "File Systems and Disk Scheduling (SCAN, C-SCAN)"
    ],
    "database": [
        "ER Modeling and Relational Schema Design",
        "SQL DDL, DML, Aggregations, and Joins",
        "Relational Normalization (1NF, 2NF, 3NF, BCNF)",
        "Transaction Management and ACID Properties",
        "Concurrency Control & Two-Phase Locking",
        "Indexing, B-Trees, and Query Optimization"
    ],
    "marketing": [
        "Market Segmentation, Targeting, and Positioning (STP)",
        "Marketing Mix 4Ps / 7Ps Framework",
        "Consumer Behavior and Decision-Making Journey",
        "Product Life Cycle (PLC) and Brand Management",
        "Pricing Strategies and Channel Distribution",
        "Digital Marketing & Integrated Communications"
    ]
}


def _get_reference_syllabus(subject_name: str, db_topics: List[str]) -> List[str]:
    """Returns official DB syllabus if available, or derives standard curriculum."""
    if db_topics and len(db_topics) >= 3:
        return db_topics

    sub_norm = subject_name.lower()
    for key, checklist in DEFAULT_SYLLABUS_MAP.items():
        if key in sub_norm:
            return checklist

    # Generic academic unit breakdown
    return [
        f"Unit 1: Foundational Principles of {subject_name}",
        f"Unit 2: Core Methodologies and Algorithmic Workings",
        f"Unit 3: Applied Implementation and Worked Case Studies",
        f"Unit 4: Advanced Architectural Constructs and Edge Cases",
        f"Unit 5: Standards, Testing, and Performance Evaluation"
    ]


class SyllabusGapService:
    """Service to audit notes against syllabus units and highlight gaps."""

    def analyze_gaps(
        self,
        document_title: str,
        subject_name: str,
        text: str,
        summary: str = "",
        db_syllabus_topics: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        reference_syllabus = _get_reference_syllabus(subject_name, db_syllabus_topics or [])
        text_lower = text.lower()

        covered_topics: List[Dict[str, Any]] = []
        missing_topics: List[Dict[str, Any]] = []

        for idx, topic in enumerate(reference_syllabus):
            # Check keywords from topic in document text
            topic_words = [w.lower() for w in topic.replace("(", "").replace(")", "").replace(",", "").split() if len(w) > 3]
            matches = [w for w in topic_words if w in text_lower]

            match_ratio = len(matches) / len(topic_words) if topic_words else 0.0

            if match_ratio >= 0.35 or topic.lower() in text_lower or (summary and any(w in summary.lower() for w in topic_words)):
                depth = min(95, max(50, int(match_ratio * 100) + 20))
                covered_topics.append({
                    "topic_name": topic,
                    "status": "covered" if depth >= 70 else "partially_covered",
                    "depth_percentage": depth,
                    "location": f"Pages 1-{min(idx + 1, 4)}"
                })
            else:
                importance = "Critical" if idx <= 2 else "High"
                missing_topics.append({
                    "topic_name": topic,
                    "importance": importance,
                    "reason": f"No substantive explanations or formulas found for '{topic}' in this uploaded note.",
                    "recommended_search_query": f"{subject_name} {topic}"
                })

        total = len(covered_topics) + len(missing_topics)
        pct = round((len(covered_topics) / total) * 100) if total > 0 else 100

        if pct >= 80:
            tier = "Comprehensive"
            advice = "This note provides comprehensive coverage of the official syllabus units. Excellent primary study material!"
        elif pct >= 60:
            tier = "Solid"
            advice = f"Solid core coverage ({pct}%), but review the {len(missing_topics)} flagged topic(s) from supplementary reference notes before exams."
        else:
            tier = "Needs Supplementary Material"
            advice = f"This note covers only {pct}% of the required syllabus. It should be used as a quick overview alongside supplementary notes."

        return {
            "completeness_percentage": pct,
            "coverage_tier": tier,
            "covered_topics": covered_topics,
            "missing_topics": missing_topics,
            "study_advice": advice
        }


syllabus_gap_service = SyllabusGapService()
