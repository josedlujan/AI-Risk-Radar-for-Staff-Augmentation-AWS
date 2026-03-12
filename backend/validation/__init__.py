"""Input validation module for team signals."""

from .team_signal_validator import (
    ValidationResult,
    validate_team_signal,
    detect_individual_identifiers,
    validate_five_dimensions,
    validate_aggregation_metadata,
)

__all__ = [
    "ValidationResult",
    "validate_team_signal",
    "detect_individual_identifiers",
    "validate_five_dimensions",
    "validate_aggregation_metadata",
]
