"""
Test suite for Innovation 5: Syllabus Gap & Completeness Heatmap.
"""

from app.services.syllabus_gap import syllabus_gap_service, _get_reference_syllabus


def test_reference_syllabus_retrieval():
    syllabus = _get_reference_syllabus("C Programming & Problem Solving", [])
    assert len(syllabus) >= 4
    assert any("pointer" in s.lower() for s in syllabus)


def test_syllabus_gap_analysis():
    title = "Pointer Fundamentals in C"
    subject = "C Programming & Problem Solving"
    text = (
        "Pointer: A variable storing address of another variable.\n"
        "Dynamic Memory: malloc and free allow run-time heap allocation."
    )

    res = syllabus_gap_service.analyze_gaps(title, subject, text)

    assert "completeness_percentage" in res
    assert "coverage_tier" in res
    assert "covered_topics" in res
    assert "missing_topics" in res
    assert "study_advice" in res

    # Should detect covered topics and missing topics
    assert len(res["covered_topics"]) >= 1
    assert len(res["missing_topics"]) >= 1

    # Check missing topic schema
    m = res["missing_topics"][0]
    assert "topic_name" in m
    assert "importance" in m
    assert "reason" in m
    assert "recommended_search_query" in m
