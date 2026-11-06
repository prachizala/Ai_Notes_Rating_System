"""
Test suite for Innovation 2: Exam Question Predictor.
"""

from app.services.exam_predictor import exam_predictor_service, _generate_fallback_predictions


def test_fallback_exam_predictions():
    title = "Database Management Systems: Normalization"
    text = (
        "Functional Dependency: An association between attributes in a relation.\n"
        "First Normal Form (1NF): Requires atomic values with no repeating groups.\n"
        "Second Normal Form (2NF): In 1NF and contains no partial functional dependencies.\n"
        "Third Normal Form (3NF): In 2NF and contains no transitive dependencies.\n"
        "Boyce-Codd Normal Form (BCNF): A stricter version where for every X -> Y, X must be a super key."
    )
    summary = "Covers relational normalization principles from 1NF to BCNF."

    res = _generate_fallback_predictions(title, text, summary)

    assert "questions" in res
    assert "exam_tips" in res
    assert len(res["questions"]) >= 6
    assert len(res["exam_tips"]) >= 3

    # Check question marks distribution (2, 5, 10 marks)
    marks_present = {q["marks"] for q in res["questions"]}
    assert 2 in marks_present
    assert 5 in marks_present
    assert 10 in marks_present

    # Check question attributes
    q = res["questions"][0]
    assert "question" in q
    assert "marks" in q
    assert "probability" in q
    assert "expected_key_points" in q
    assert len(q["expected_key_points"]) >= 1


def test_exam_predictor_service():
    res = exam_predictor_service.predict_questions(
        document_title="C Programming Pointers",
        text="Pointer is a variable storing the address of another variable. malloc allocates memory dynamically.",
        summary="Pointer basics."
    )
    assert len(res["questions"]) >= 6
    assert any(q["marks"] == 2 for q in res["questions"])
    assert any(q["marks"] == 5 for q in res["questions"])
    assert any(q["marks"] == 10 for q in res["questions"])
