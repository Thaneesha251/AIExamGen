"""Centralized thresholds and configuration constants for Question Quality Analysis."""

# Difficulty Index Thresholds (Normalized Average Percentage 0.0 - 100.0)
QUESTION_DIFFICULTY_EASY_THRESHOLD = 75.0      # >= 75% -> EASY
QUESTION_DIFFICULTY_MODERATE_THRESHOLD = 40.0  # >= 40% and < 75% -> MODERATE
                                                # < 40% -> DIFFICULT

# Discrimination Index Thresholds (-1.0 to +1.0)
DISCRIMINATION_STRONG_THRESHOLD = 0.40      # >= 0.40 -> STRONG
DISCRIMINATION_ACCEPTABLE_THRESHOLD = 0.20  # >= 0.20 and < 0.40 -> ACCEPTABLE
DISCRIMINATION_WEAK_THRESHOLD = 0.00        # >= 0.00 and < 0.20 -> WEAK
                                            # < 0.00 -> NEGATIVE

# Cohort Size Requirements for Discrimination Analysis
MINIMUM_COHORT_SIZE_FOR_DISCRIMINATION = 4
DISCRIMINATION_TOP_BOTTOM_PERCENTILE = 0.27  # 27% top and 27% bottom

# Blueprint Variance Tolerance
BLUEPRINT_VARIANCE_TOLERANCE = 5.0  # Max variance (+/- 5.0%) before flagging REVIEW_VARIANCE
