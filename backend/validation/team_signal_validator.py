"""Validation functions for team signal input data."""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """Result of validation with success status and error details."""
    
    is_valid: bool
    errors: List[str]
    rejected_fields: List[str]
    
    def __bool__(self) -> bool:
        """Allow using ValidationResult in boolean context."""
        return self.is_valid


# Individual identifier patterns to detect
INDIVIDUAL_IDENTIFIER_PATTERNS = [
    'user_', 'user-', 'userid', 'user.', 'username',
    'engineer_', 'engineer-', 'engineerid',
    'employee_', 'employee-', 'employeeid',
    'developer_', 'developer-', 'developerid',
    'member_', 'member-', 'memberid',
    '@',  # Email addresses
    'email',
    'name:', 'name=',  # Name fields
    'individual', 'person',
]

# Required risk dimensions
REQUIRED_DIMENSIONS = [
    'delivery_cadence',
    'knowledge_concentration',
    'dependency_risk',
    'workload_distribution',
    'attrition_signal',
]

# Required metadata fields
REQUIRED_METADATA_FIELDS = [
    'team_size',
    'project_count',
    'aggregation_period',
]


def detect_individual_identifiers(data: Dict[str, Any]) -> ValidationResult:
    """
    Detect individual engineer identifiers in the data.
    
    Args:
        data: Input data dictionary to validate
        
    Returns:
        ValidationResult indicating if individual identifiers were found
    """
    errors = []
    rejected_fields = []
    
    def check_value(key: str, value: Any, path: str = "") -> None:
        """Recursively check values for individual identifier patterns."""
        current_path = f"{path}.{key}" if path else key
        
        if isinstance(value, str):
            value_lower = value.lower()
            for pattern in INDIVIDUAL_IDENTIFIER_PATTERNS:
                if pattern in value_lower:
                    errors.append(
                        f"Field '{current_path}' contains individual identifier pattern: '{pattern}'"
                    )
                    rejected_fields.append(current_path)
                    return
        elif isinstance(value, dict):
            for k, v in value.items():
                check_value(k, v, current_path)
        elif isinstance(value, list):
            for i, item in enumerate(value):
                check_value(f"[{i}]", item, current_path)
    
    # Check all fields in the data
    for key, value in data.items():
        check_value(key, value)
    
    if errors:
        return ValidationResult(
            is_valid=False,
            errors=errors,
            rejected_fields=rejected_fields
        )
    
    return ValidationResult(is_valid=True, errors=[], rejected_fields=[])


def validate_five_dimensions(data: Dict[str, Any]) -> ValidationResult:
    """
    Validate that all five risk dimensions are present with valid values.
    
    Args:
        data: Input data dictionary to validate
        
    Returns:
        ValidationResult indicating if all dimensions are present and valid
    """
    errors = []
    missing_dimensions = []
    
    # Check for presence of all required dimensions
    for dimension in REQUIRED_DIMENSIONS:
        if dimension not in data:
            missing_dimensions.append(dimension)
            errors.append(f"Missing required dimension: '{dimension}'")
    
    # Validate dimension values (must be numeric and in range 0-100)
    for dimension in REQUIRED_DIMENSIONS:
        if dimension in data:
            value = data[dimension]
            
            # Check if value is numeric
            if not isinstance(value, (int, float)):
                errors.append(
                    f"Dimension '{dimension}' must be numeric, got {type(value).__name__}"
                )
                continue
            
            # Check if value is in valid range
            if not (0 <= value <= 100):
                errors.append(
                    f"Dimension '{dimension}' must be between 0 and 100, got {value}"
                )
    
    if errors:
        return ValidationResult(
            is_valid=False,
            errors=errors,
            rejected_fields=missing_dimensions
        )
    
    return ValidationResult(is_valid=True, errors=[], rejected_fields=[])


def validate_aggregation_metadata(data: Dict[str, Any]) -> ValidationResult:
    """
    Validate that aggregation metadata is present and properly structured.
    
    Args:
        data: Input data dictionary to validate
        
    Returns:
        ValidationResult indicating if metadata is valid
    """
    errors = []
    rejected_fields = []
    
    # Check if metadata field exists
    if 'metadata' not in data:
        return ValidationResult(
            is_valid=False,
            errors=["Missing required 'metadata' field"],
            rejected_fields=['metadata']
        )
    
    metadata = data['metadata']
    
    # Check if metadata is a dictionary
    if not isinstance(metadata, dict):
        return ValidationResult(
            is_valid=False,
            errors=[f"'metadata' must be a dictionary, got {type(metadata).__name__}"],
            rejected_fields=['metadata']
        )
    
    # Check for required metadata fields
    for field in REQUIRED_METADATA_FIELDS:
        if field not in metadata:
            errors.append(f"Missing required metadata field: '{field}'")
            rejected_fields.append(f"metadata.{field}")
    
    # Validate team_size
    if 'team_size' in metadata:
        team_size = metadata['team_size']
        if not isinstance(team_size, int):
            errors.append(f"'team_size' must be an integer, got {type(team_size).__name__}")
        elif team_size <= 0:
            errors.append(f"'team_size' must be greater than 0, got {team_size}")
    
    # Validate project_count
    if 'project_count' in metadata:
        project_count = metadata['project_count']
        if not isinstance(project_count, int):
            errors.append(f"'project_count' must be an integer, got {type(project_count).__name__}")
        elif project_count <= 0:
            errors.append(f"'project_count' must be greater than 0, got {project_count}")
    
    # Validate aggregation_period
    if 'aggregation_period' in metadata:
        aggregation_period = metadata['aggregation_period']
        if not isinstance(aggregation_period, str):
            errors.append(f"'aggregation_period' must be a string, got {type(aggregation_period).__name__}")
        elif not aggregation_period.strip():
            errors.append("'aggregation_period' cannot be empty")
    
    if errors:
        return ValidationResult(
            is_valid=False,
            errors=errors,
            rejected_fields=rejected_fields
        )
    
    return ValidationResult(is_valid=True, errors=[], rejected_fields=[])


def validate_team_signal(data: Dict[str, Any]) -> ValidationResult:
    """
    Comprehensive validation of team signal data.
    
    Validates:
    - No individual identifiers present
    - All five risk dimensions present and valid
    - Aggregation metadata properly structured
    
    Args:
        data: Input data dictionary to validate
        
    Returns:
        ValidationResult with combined validation results
    """
    all_errors = []
    all_rejected_fields = []
    
    # Run all validations
    individual_check = detect_individual_identifiers(data)
    if not individual_check.is_valid:
        all_errors.extend(individual_check.errors)
        all_rejected_fields.extend(individual_check.rejected_fields)
    
    dimensions_check = validate_five_dimensions(data)
    if not dimensions_check.is_valid:
        all_errors.extend(dimensions_check.errors)
        all_rejected_fields.extend(dimensions_check.rejected_fields)
    
    metadata_check = validate_aggregation_metadata(data)
    if not metadata_check.is_valid:
        all_errors.extend(metadata_check.errors)
        all_rejected_fields.extend(metadata_check.rejected_fields)
    
    if all_errors:
        return ValidationResult(
            is_valid=False,
            errors=all_errors,
            rejected_fields=all_rejected_fields
        )
    
    return ValidationResult(is_valid=True, errors=[], rejected_fields=[])
