"""
Test suite for Innovation 6: NotebookLM-Style AI Audio Study Podcast.
"""

from app.services.podcast import study_podcast_service, _generate_fallback_podcast


def test_fallback_podcast_generation():
    title = "C Programming: Pointers and Memory"
    text = (
        "Pointer: A variable storing address of another variable.\n"
        "malloc: Allocates memory on heap dynamically at runtime.\n"
        "Memory Leak: Failing to free dynamically allocated heap memory."
    )
    summary = "Covers pointer arithmetic and dynamic memory pitfalls."

    res = _generate_fallback_podcast(title, text, summary)

    assert "episode_title" in res
    assert "estimated_duration_minutes" in res
    assert "turns" in res
    assert "key_takeaways" in res

    # Verify turns
    assert len(res["turns"]) >= 8
    speakers = {t["speaker"] for t in res["turns"]}
    assert "Alex" in speakers
    assert "Sam" in speakers

    # Verify dialogue turns have text and topic tags
    t = res["turns"][0]
    assert len(t["text"]) > 10
    assert "topic_tag" in t

    # Verify takeaways
    assert len(res["key_takeaways"]) >= 3


def test_study_podcast_service():
    res = study_podcast_service.generate_podcast(
        document_title="Operating Systems Deadlocks",
        text="Deadlock: Situation where processes are permanently blocked.",
        summary="Deadlock avoidance."
    )
    assert len(res["turns"]) >= 8
    assert res["estimated_duration_minutes"] >= 2
