import pytest
from app.services.viva import generate_viva_questions, evaluate_viva_answer
from app.schemas.viva import VivaSessionResponse, VivaEvaluationResponse


def test_generate_viva_questions_fallback():
    title = "Database Normalization and BCNF"
    text = (
        "Normalization is the process of structuring a relational database in accordance with a series of normal forms.\n"
        "First Normal Form requires atomic attributes and no repeating groups.\n"
        "Second Normal Form eliminates partial dependency on composite candidate keys.\n"
        "Third Normal Form ensures non-prime attributes are transitively independent of candidate keys.\n"
        "Boyce-Codd Normal Form addresses functional dependencies with overlapping candidate keys.\n"
    )
    result = generate_viva_questions(
        document_id="doc-test-123",
        document_title=title,
        document_text=text,
    )
    assert isinstance(result, VivaSessionResponse)
    assert result.document_id == "doc-test-123"
    assert result.document_title == title
    assert len(result.questions) >= 3
    for q in result.questions:
        assert q.id > 0
        assert len(q.question) > 10
        assert q.difficulty in ["Easy", "Medium", "Hard"]
        assert len(q.examiner_tip) > 5


def test_evaluate_viva_answer_empty():
    res = evaluate_viva_answer(
        question="What is 3NF?",
        student_answer="no idea",
        ideal_answer_key="Third normal form eliminates transitive dependency.",
    )
    assert isinstance(res, VivaEvaluationResponse)
    assert res.score <= 3
    assert "too brief" in res.examiner_verdict.lower() or "unattempted" in res.examiner_verdict.lower()
    assert len(res.missing_key_points) > 0


def test_evaluate_viva_answer_solid():
    res = evaluate_viva_answer(
        question="Explain the difference between 2NF and 3NF.",
        student_answer="2NF deals with removing partial dependencies where non-key attributes depend on part of a composite key. On the other hand, 3NF removes transitive dependencies where a non-prime attribute depends on another non-prime attribute.",
        ideal_answer_key="2NF removes partial dependency on candidate keys. 3NF eliminates transitive dependency between non-prime attributes.",
    )
    assert isinstance(res, VivaEvaluationResponse)
    assert res.score >= 6
    assert res.max_score == 10
    assert len(res.strengths) > 0
    assert len(res.improved_answer) > 10
