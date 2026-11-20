"""Academic study notes quality, completeness, and structure evaluator."""


class AcademicNoteScorer:
    """Evaluates student notes based on structure, heading hierarchy, and vocabulary density."""

    @staticmethod
    def evaluate_quality_score(word_count: int, heading_count: int, formula_count: int) -> float:
        """Computes comprehensive note quality score on a 0-10 scale."""
        length_score = min(word_count / 500.0 * 4.0, 4.0)
        structure_score = min(heading_count / 5.0 * 3.0, 3.0)
        technical_score = min(formula_count / 3.0 * 3.0, 3.0)

        total_score = length_score + structure_score + technical_score
        return round(min(total_score, 10.0), 2)
