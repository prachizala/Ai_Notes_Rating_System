"""
Test suite for 1-Page Exam Cheat Sheet & Formula Card Generator.
"""

from app.services.cheat_sheet import cheat_sheet_service, _generate_fallback_cheat_sheet


def test_fallback_cheat_sheet_generation():
    title = "C Programming: Pointers & Memory"
    text = (
        "Pointer: Variable holding memory address of another variable.\n"
        "malloc: Allocates memory dynamically from heap.\n"
        "calloc: Allocates memory and clears all bits to zero."
    )
    summary = "Pointers and dynamic memory management."
    subject = "C Programming"

    res = _generate_fallback_cheat_sheet(title, text, summary, subject)

    assert "summary_capsule" in res
    assert "formulas_and_syntax" in res
    assert "key_definitions" in res
    assert "distinctions_table" in res
    assert "exam_traps" in res
    assert "rapid_mnemonics" in res

    # Check formulas and syntax
    assert len(res["formulas_and_syntax"]) >= 3
    f = res["formulas_and_syntax"][0]
    assert "title" in f
    assert "syntax_or_formula" in f

    # Check definitions
    assert len(res["key_definitions"]) >= 3

    # Check distinctions table
    assert len(res["distinctions_table"]) >= 2
    row = res["distinctions_table"][0]
    assert "parameter" in row
    assert "concept_a" in row
    assert "concept_b" in row

    # Check traps and mnemonics
    assert len(res["exam_traps"]) >= 2
    assert len(res["rapid_mnemonics"]) >= 1


def test_cheat_sheet_service():
    res = cheat_sheet_service.generate_cheat_sheet(
        document_title="Database Management Normalization",
        text="1NF: Atomic values. 2NF: No partial dependency. 3NF: No transitive dependency.",
        summary="Normalization levels."
    )
    assert len(res["formulas_and_syntax"]) >= 2
    assert len(res["key_definitions"]) >= 3
    assert len(res["distinctions_table"]) >= 2
