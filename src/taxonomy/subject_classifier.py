"""Academic notes curriculum domain and discipline classifier."""


class AcademicSubjectClassifier:
    """Categorizes study notes into STEM, Humanities, and Commerce curriculum domains."""

    SUBJECT_TAXONOMY = {
        "COMPUTER_SCIENCE": ["algorithm", "data structure", "database", "recursion", "compiler"],
        "MATHEMATICS": ["calculus", "derivative", "integral", "matrix", "linear algebra"],
        "PHYSICS": ["thermodynamics", "quantum", "electromagnetism", "velocity", "force"],
        "ECONOMICS": ["inflation", "gdp", "macroeconomics", "supply and demand", "fiscal"],
    }

    @classmethod
    def classify_domain(cls, text_content: str) -> str:
        """Matches content keywords to determine primary academic discipline."""
        lowered = text_content.lower()
        counts = {}
        for subject, keywords in cls.SUBJECT_TAXONOMY.items():
            counts[subject] = sum(1 for kw in keywords if kw in lowered)

        best_match = max(counts, key=counts.get)
        return best_match if counts[best_match] > 0 else "GENERAL_STUDIES"
