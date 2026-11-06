import pytest
from app.services.reader import explain_inline_snippet
from app.schemas.reader import InlineExplainResponse


def test_explain_inline_snippet_modes():
    modes = ["eli5", "hinglish", "exam_trap", "academic"]
    sample_text = "Deadlock occurs when four conditions are met: Mutual Exclusion, Hold and Wait, No Preemption, Circular Wait."

    for mode in modes:
        res = explain_inline_snippet(
            selected_text=sample_text,
            context="Operating Systems Chapter on Concurrency and Deadlocks",
            mode=mode,
        )
        assert isinstance(res, InlineExplainResponse)
        assert res.mode == mode
        assert len(res.explanation) > 15
        assert len(res.key_takeaways) >= 1
        assert res.mnemonic_or_analogy is not None
