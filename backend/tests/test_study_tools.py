"""
Test suite for Innovation 1: Study Tools (Interactive Flashcards & Quiz).
"""

import pytest
from app.services.study_tools import study_tools_service, _generate_fallback_study_pack


def test_fallback_study_pack_generation():
    title = "Data Structures: Binary Search Trees"
    text = (
        "Binary Search Tree: A node-based binary tree data structure with sorted properties.\n"
        "Inorder Traversal: Traversal technique that yields sorted order in BST.\n"
        "Height: Maximum distance from root to leaf node.\n"
        "Time Complexity: Searching takes O(log n) time in balanced BST."
    )
    summary = "Covers fundamentals of binary search trees and tree traversal."

    pack = _generate_fallback_study_pack(title, text, summary)

    assert "quiz" in pack
    assert "flashcards" in pack
    assert len(pack["quiz"]) == 5
    assert len(pack["flashcards"]) >= 4

    # Check quiz question structure
    q = pack["quiz"][0]
    assert "question" in q
    assert len(q["options"]) == 4
    assert 0 <= q["correct_index"] <= 3
    assert "explanation" in q

    # Check flashcard structure
    f = pack["flashcards"][0]
    assert "front" in f
    assert "back" in f
    assert "topic" in f


def test_study_tools_service():
    pack = study_tools_service.generate_study_pack(
        document_title="Operating Systems Deadlocks",
        text="Deadlock: A situation where a set of processes are blocked because each process is holding a resource and waiting for another.",
        summary="Deadlock definitions and prevention."
    )
    assert len(pack["quiz"]) == 5
    assert len(pack["flashcards"]) >= 4
