"""
Test suite for Innovation 4: Multi-Level Concept Simplifier (ELI5, Industry, Hinglish).
"""

from app.services.simplifier import concept_simplifier_service, _generate_fallback_simplification


def test_fallback_simplification():
    title = "Operating Systems: Process Synchronization"
    text = (
        "Mutex: A mutual exclusion locking mechanism.\n"
        "Semaphore: A signaling mechanism used to control access to shared resources.\n"
        "Critical Section: The segment of code where shared resources are accessed."
    )

    res = _generate_fallback_simplification(title, text)

    assert "concepts" in res
    assert len(res["concepts"]) >= 3

    c = res["concepts"][0]
    assert "concept_name" in c
    assert "eli5_analogy" in c
    assert "industry_application" in c
    assert "hinglish_breakdown" in c
    assert "jargon_busters" in c
    assert len(c["jargon_busters"]) >= 1


def test_custom_query_simplification():
    title = "C Programming"
    text = "Pointer Dereferencing: Accessing the value stored at the memory address."

    res = concept_simplifier_service.explain_concepts(title, text, custom_query="Dangling Pointer")

    assert len(res["concepts"]) >= 1
    assert res["concepts"][0]["concept_name"] == "Dangling Pointer"
    assert len(res["concepts"][0]["eli5_analogy"]) > 10
