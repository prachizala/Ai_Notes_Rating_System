"""
Scoring formula calculations for NoteIQ academic evaluations.
All mathematical scores are computed in code, never trusted from model hallucinations.
"""

from typing import List, Optional, Tuple


def round_to_nearest_half(val: float) -> float:
    """Rounds float to the nearest 0.5 step (e.g. 4.325 -> 4.5, 4.12 -> 4.0)."""
    return round(val * 2) / 2


def calculate_overall_scores(
    accuracy: float,
    explanation: float,
    depth: float,
    examples: float,
) -> Tuple[float, float]:
    """
    Computes overall raw and display scores.
    Formula:
      overall_raw = 0.30 * accuracy + 0.25 * explanation + 0.25 * depth + 0.20 * examples
      overall_display = overall_raw rounded to nearest 0.5
    Example: (4, 4.5, 4, 5) -> raw: 4.325, display: 4.5
    """
    raw = (
        0.30 * accuracy +
        0.25 * explanation +
        0.25 * depth +
        0.20 * examples
    )
    raw = round(raw, 3)
    display = round_to_nearest_half(raw)
    return raw, display


def calculate_topic_coverage(
    syllabus_items: Optional[List[dict]],
) -> Optional[float]:
    """
    Computes syllabus checklist coverage percentage.
    Formula:
      topic_coverage_pct = (covered + 0.5 * partial) / total checklist items * 100
    Rule: If no checklist is provided, returns None (null).
    """
    if not syllabus_items:
        return None

    total_items = len(syllabus_items)
    if total_items == 0:
        return None

    score_sum = 0.0
    for item in syllabus_items:
        st = item.get("status", "").lower()
        if st == "covered":
            score_sum += 1.0
        elif st == "partial":
            score_sum += 0.5

    pct = round((score_sum / total_items) * 100.0, 1)
    return pct
