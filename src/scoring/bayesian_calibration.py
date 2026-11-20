"""Bayesian mean shrinkage estimator for peer-reviewed academic note ratings."""


class BayesianRatingCalibrator:
    """Adjusts raw user review averages to prevent outliers on notes with few reviews."""

    GLOBAL_PRIOR_MEAN = 7.0
    GLOBAL_PRIOR_WEIGHT = 5

    @classmethod
    def compute_calibrated_score(cls, vote_count: int, sample_average: float) -> float:
        """Calculates Bayesian weighted average score: (C * m + sum(reviews)) / (C + n)."""
        weighted_sum = (cls.GLOBAL_PRIOR_WEIGHT * cls.GLOBAL_PRIOR_MEAN) + (vote_count * sample_average)
        calibrated = weighted_sum / (cls.GLOBAL_PRIOR_WEIGHT + vote_count)
        return round(calibrated, 2)
