"""Unit tests for team signal validation module."""

import pytest
from backend.validation import (
    ValidationResult,
    validate_team_signal,
    detect_individual_identifiers,
    validate_five_dimensions,
    validate_aggregation_metadata,
)


class TestDetectIndividualIdentifiers:
    """Tests for individual identifier detection."""
    
    def test_valid_team_data_no_identifiers(self):
        """Valid team-level data should pass validation."""
        data = {
            "team_id": "team-alpha",
            "signals": {"delivery_cadence": 75.0}
        }
        result = detect_individual_identifiers(data)
        assert result.is_valid
        assert len(result.errors) == 0
        assert len(result.rejected_fields) == 0
    
    def test_detect_user_prefix(self):
        """Should detect 'user_' pattern."""
        data = {"team_id": "user_123"}
        result = detect_individual_identifiers(data)
        assert not result.is_valid
        assert "user_" in result.errors[0].lower()
        assert "team_id" in result.rejected_fields
    
    def test_detect_engineer_prefix(self):
        """Should detect 'engineer_' pattern."""
        data = {"engineer_id": "engineer_john"}
        result = detect_individual_identifiers(data)
        assert not result.is_valid
        assert "engineer_" in result.errors[0].lower()
    
    def test_detect_employee_prefix(self):
        """Should detect 'employee_' pattern."""
        data = {"id": "employee_456"}
        result = detect_individual_identifiers(data)
        assert not result.is_valid
        assert "employee_" in result.errors[0].lower()
    
    def test_detect_email_symbol(self):
        """Should detect '@' symbol indicating email."""
        data = {"contact": "john@example.com"}
        result = detect_individual_identifiers(data)
        assert not result.is_valid
        assert "@" in result.errors[0]
    
    def test_detect_email_keyword(self):
        """Should detect 'email' keyword in values."""
        data = {"contact_info": "email: john.doe"}
        result = detect_individual_identifiers(data)
        assert not result.is_valid
        assert "email" in result.errors[0].lower()
    
    def test_detect_nested_identifiers(self):
        """Should detect identifiers in nested structures."""
        data = {
            "team_id": "team-alpha",
            "metadata": {
                "owner": "user_john"
            }
        }
        result = detect_individual_identifiers(data)
        assert not result.is_valid
        assert "metadata.owner" in result.rejected_fields
    
    def test_detect_identifiers_in_list(self):
        """Should detect identifiers in list items."""
        data = {
            "team_id": "team-alpha",
            "members": ["user_1", "user_2"]
        }
        result = detect_individual_identifiers(data)
        assert not result.is_valid
        assert len(result.errors) >= 1
    
    def test_case_insensitive_detection(self):
        """Should detect patterns case-insensitively."""
        data = {"id": "USER_123"}
        result = detect_individual_identifiers(data)
        assert not result.is_valid
    
    def test_multiple_violations(self):
        """Should detect multiple individual identifier violations."""
        data = {
            "user_id": "user_123",
            "email": "test@example.com"
        }
        result = detect_individual_identifiers(data)
        assert not result.is_valid
        assert len(result.errors) >= 2


class TestValidateFiveDimensions:
    """Tests for five dimension validation."""
    
    def test_all_dimensions_present_and_valid(self):
        """All five dimensions with valid values should pass."""
        data = {
            "delivery_cadence": 75.0,
            "knowledge_concentration": 50.0,
            "dependency_risk": 30.0,
            "workload_distribution": 60.0,
            "attrition_signal": 20.0,
        }
        result = validate_five_dimensions(data)
        assert result.is_valid
        assert len(result.errors) == 0
    
    def test_missing_single_dimension(self):
        """Missing one dimension should fail."""
        data = {
            "delivery_cadence": 75.0,
            "knowledge_concentration": 50.0,
            "dependency_risk": 30.0,
            "workload_distribution": 60.0,
            # Missing attrition_signal
        }
        result = validate_five_dimensions(data)
        assert not result.is_valid
        assert "attrition_signal" in result.errors[0]
        assert "attrition_signal" in result.rejected_fields
    
    def test_missing_multiple_dimensions(self):
        """Missing multiple dimensions should fail with all listed."""
        data = {
            "delivery_cadence": 75.0,
            # Missing other four dimensions
        }
        result = validate_five_dimensions(data)
        assert not result.is_valid
        assert len(result.errors) == 4
        assert len(result.rejected_fields) == 4
    
    def test_missing_all_dimensions(self):
        """Missing all dimensions should fail."""
        data = {}
        result = validate_five_dimensions(data)
        assert not result.is_valid
        assert len(result.errors) == 5
    
    def test_dimension_value_below_range(self):
        """Dimension value below 0 should fail."""
        data = {
            "delivery_cadence": -10.0,
            "knowledge_concentration": 50.0,
            "dependency_risk": 30.0,
            "workload_distribution": 60.0,
            "attrition_signal": 20.0,
        }
        result = validate_five_dimensions(data)
        assert not result.is_valid
        assert "0 and 100" in result.errors[0]
    
    def test_dimension_value_above_range(self):
        """Dimension value above 100 should fail."""
        data = {
            "delivery_cadence": 75.0,
            "knowledge_concentration": 150.0,
            "dependency_risk": 30.0,
            "workload_distribution": 60.0,
            "attrition_signal": 20.0,
        }
        result = validate_five_dimensions(data)
        assert not result.is_valid
        assert "0 and 100" in result.errors[0]
    
    def test_dimension_non_numeric_value(self):
        """Non-numeric dimension value should fail."""
        data = {
            "delivery_cadence": "high",
            "knowledge_concentration": 50.0,
            "dependency_risk": 30.0,
            "workload_distribution": 60.0,
            "attrition_signal": 20.0,
        }
        result = validate_five_dimensions(data)
        assert not result.is_valid
        assert "numeric" in result.errors[0].lower()
    
    def test_dimension_integer_values_accepted(self):
        """Integer values should be accepted."""
        data = {
            "delivery_cadence": 75,
            "knowledge_concentration": 50,
            "dependency_risk": 30,
            "workload_distribution": 60,
            "attrition_signal": 20,
        }
        result = validate_five_dimensions(data)
        assert result.is_valid
    
    def test_dimension_boundary_values(self):
        """Boundary values 0 and 100 should be valid."""
        data = {
            "delivery_cadence": 0.0,
            "knowledge_concentration": 100.0,
            "dependency_risk": 0,
            "workload_distribution": 100,
            "attrition_signal": 50.0,
        }
        result = validate_five_dimensions(data)
        assert result.is_valid


class TestValidateAggregationMetadata:
    """Tests for aggregation metadata validation."""
    
    def test_valid_metadata(self):
        """Valid metadata structure should pass."""
        data = {
            "metadata": {
                "team_size": 8,
                "project_count": 3,
                "aggregation_period": "weekly"
            }
        }
        result = validate_aggregation_metadata(data)
        assert result.is_valid
        assert len(result.errors) == 0
    
    def test_missing_metadata_field(self):
        """Missing metadata field should fail."""
        data = {}
        result = validate_aggregation_metadata(data)
        assert not result.is_valid
        assert "metadata" in result.errors[0].lower()
        assert "metadata" in result.rejected_fields
    
    def test_metadata_not_dict(self):
        """Metadata that's not a dictionary should fail."""
        data = {"metadata": "invalid"}
        result = validate_aggregation_metadata(data)
        assert not result.is_valid
        assert "dictionary" in result.errors[0].lower()
    
    def test_missing_team_size(self):
        """Missing team_size should fail."""
        data = {
            "metadata": {
                "project_count": 3,
                "aggregation_period": "weekly"
            }
        }
        result = validate_aggregation_metadata(data)
        assert not result.is_valid
        assert "team_size" in result.errors[0]
    
    def test_missing_project_count(self):
        """Missing project_count should fail."""
        data = {
            "metadata": {
                "team_size": 8,
                "aggregation_period": "weekly"
            }
        }
        result = validate_aggregation_metadata(data)
        assert not result.is_valid
        assert "project_count" in result.errors[0]
    
    def test_missing_aggregation_period(self):
        """Missing aggregation_period should fail."""
        data = {
            "metadata": {
                "team_size": 8,
                "project_count": 3
            }
        }
        result = validate_aggregation_metadata(data)
        assert not result.is_valid
        assert "aggregation_period" in result.errors[0]
    
    def test_team_size_not_integer(self):
        """Non-integer team_size should fail."""
        data = {
            "metadata": {
                "team_size": "eight",
                "project_count": 3,
                "aggregation_period": "weekly"
            }
        }
        result = validate_aggregation_metadata(data)
        assert not result.is_valid
        assert "team_size" in result.errors[0]
        assert "integer" in result.errors[0].lower()
    
    def test_team_size_zero(self):
        """team_size of 0 should fail."""
        data = {
            "metadata": {
                "team_size": 0,
                "project_count": 3,
                "aggregation_period": "weekly"
            }
        }
        result = validate_aggregation_metadata(data)
        assert not result.is_valid
        assert "greater than 0" in result.errors[0]
    
    def test_team_size_negative(self):
        """Negative team_size should fail."""
        data = {
            "metadata": {
                "team_size": -5,
                "project_count": 3,
                "aggregation_period": "weekly"
            }
        }
        result = validate_aggregation_metadata(data)
        assert not result.is_valid
    
    def test_project_count_not_integer(self):
        """Non-integer project_count should fail."""
        data = {
            "metadata": {
                "team_size": 8,
                "project_count": 3.5,
                "aggregation_period": "weekly"
            }
        }
        result = validate_aggregation_metadata(data)
        assert not result.is_valid
        assert "project_count" in result.errors[0]
    
    def test_project_count_zero(self):
        """project_count of 0 should fail."""
        data = {
            "metadata": {
                "team_size": 8,
                "project_count": 0,
                "aggregation_period": "weekly"
            }
        }
        result = validate_aggregation_metadata(data)
        assert not result.is_valid
    
    def test_aggregation_period_not_string(self):
        """Non-string aggregation_period should fail."""
        data = {
            "metadata": {
                "team_size": 8,
                "project_count": 3,
                "aggregation_period": 7
            }
        }
        result = validate_aggregation_metadata(data)
        assert not result.is_valid
        assert "aggregation_period" in result.errors[0]
        assert "string" in result.errors[0].lower()
    
    def test_aggregation_period_empty(self):
        """Empty aggregation_period should fail."""
        data = {
            "metadata": {
                "team_size": 8,
                "project_count": 3,
                "aggregation_period": ""
            }
        }
        result = validate_aggregation_metadata(data)
        assert not result.is_valid
        assert "empty" in result.errors[0].lower()
    
    def test_aggregation_period_whitespace_only(self):
        """Whitespace-only aggregation_period should fail."""
        data = {
            "metadata": {
                "team_size": 8,
                "project_count": 3,
                "aggregation_period": "   "
            }
        }
        result = validate_aggregation_metadata(data)
        assert not result.is_valid


class TestValidationEdgeCases:
    """Edge case tests for validation - Requirements 1.2, 1.3."""
    
    def test_empty_signal_dict(self):
        """Empty signal dictionary should fail validation."""
        data = {}
        result = validate_team_signal(data)
        assert not result.is_valid
        assert len(result.errors) >= 5  # Missing all dimensions
        assert "metadata" in ' '.join(result.errors).lower()
    
    def test_signal_with_only_team_id(self):
        """Signal with only team_id should fail validation."""
        data = {"team_id": "team-alpha"}
        result = validate_team_signal(data)
        assert not result.is_valid
        assert len(result.errors) >= 6  # 5 dimensions + metadata
    
    def test_signal_with_null_values(self):
        """Signal with null dimension values should fail."""
        data = {
            "team_id": "team-alpha",
            "delivery_cadence": None,
            "knowledge_concentration": None,
            "dependency_risk": None,
            "workload_distribution": None,
            "attrition_signal": None,
            "metadata": {
                "team_size": 8,
                "project_count": 3,
                "aggregation_period": "weekly"
            }
        }
        result = validate_team_signal(data)
        assert not result.is_valid
        assert len(result.errors) >= 5  # All dimensions have invalid values
    
    def test_signal_with_empty_strings(self):
        """Signal with empty string dimension values should fail."""
        data = {
            "team_id": "team-alpha",
            "delivery_cadence": "",
            "knowledge_concentration": 50.0,
            "dependency_risk": 30.0,
            "workload_distribution": 60.0,
            "attrition_signal": 20.0,
            "metadata": {
                "team_size": 8,
                "project_count": 3,
                "aggregation_period": "weekly"
            }
        }
        result = validate_team_signal(data)
        assert not result.is_valid
        assert "delivery_cadence" in ' '.join(result.errors)
    
    def test_missing_all_dimensions(self):
        """Signal missing all five dimensions should fail."""
        data = {
            "team_id": "team-alpha",
            "metadata": {
                "team_size": 8,
                "project_count": 3,
                "aggregation_period": "weekly"
            }
        }
        result = validate_team_signal(data)
        assert not result.is_valid
        assert len(result.errors) == 5
        for dimension in ["delivery_cadence", "knowledge_concentration", 
                         "dependency_risk", "workload_distribution", "attrition_signal"]:
            assert dimension in ' '.join(result.errors)
    
    def test_missing_random_subset_of_dimensions(self):
        """Signal missing 2-3 random dimensions should fail."""
        data = {
            "team_id": "team-alpha",
            "delivery_cadence": 75.0,
            "workload_distribution": 60.0,
            # Missing: knowledge_concentration, dependency_risk, attrition_signal
            "metadata": {
                "team_size": 8,
                "project_count": 3,
                "aggregation_period": "weekly"
            }
        }
        result = validate_team_signal(data)
        assert not result.is_valid
        assert len(result.errors) == 3
        assert "knowledge_concentration" in ' '.join(result.errors)
        assert "dependency_risk" in ' '.join(result.errors)
        assert "attrition_signal" in ' '.join(result.errors)
    
    def test_malformed_metadata_null(self):
        """Signal with null metadata should fail."""
        data = {
            "team_id": "team-alpha",
            "delivery_cadence": 75.0,
            "knowledge_concentration": 50.0,
            "dependency_risk": 30.0,
            "workload_distribution": 60.0,
            "attrition_signal": 20.0,
            "metadata": None
        }
        result = validate_team_signal(data)
        assert not result.is_valid
        assert "metadata" in ' '.join(result.errors).lower()
    
    def test_malformed_metadata_empty_dict(self):
        """Signal with empty metadata dict should fail."""
        data = {
            "team_id": "team-alpha",
            "delivery_cadence": 75.0,
            "knowledge_concentration": 50.0,
            "dependency_risk": 30.0,
            "workload_distribution": 60.0,
            "attrition_signal": 20.0,
            "metadata": {}
        }
        result = validate_team_signal(data)
        assert not result.is_valid
        assert len(result.errors) == 3  # Missing all 3 metadata fields
    
    def test_malformed_metadata_string(self):
        """Signal with string metadata should fail."""
        data = {
            "team_id": "team-alpha",
            "delivery_cadence": 75.0,
            "knowledge_concentration": 50.0,
            "dependency_risk": 30.0,
            "workload_distribution": 60.0,
            "attrition_signal": 20.0,
            "metadata": "invalid metadata"
        }
        result = validate_team_signal(data)
        assert not result.is_valid
        assert "dictionary" in ' '.join(result.errors).lower()
    
    def test_malformed_metadata_list(self):
        """Signal with list metadata should fail."""
        data = {
            "team_id": "team-alpha",
            "delivery_cadence": 75.0,
            "knowledge_concentration": 50.0,
            "dependency_risk": 30.0,
            "workload_distribution": 60.0,
            "attrition_signal": 20.0,
            "metadata": [8, 3, "weekly"]
        }
        result = validate_team_signal(data)
        assert not result.is_valid
        assert "dictionary" in ' '.join(result.errors).lower()
    
    def test_metadata_with_negative_team_size(self):
        """Metadata with negative team_size should fail."""
        data = {
            "team_id": "team-alpha",
            "delivery_cadence": 75.0,
            "knowledge_concentration": 50.0,
            "dependency_risk": 30.0,
            "workload_distribution": 60.0,
            "attrition_signal": 20.0,
            "metadata": {
                "team_size": -5,
                "project_count": 3,
                "aggregation_period": "weekly"
            }
        }
        result = validate_team_signal(data)
        assert not result.is_valid
        assert "team_size" in ' '.join(result.errors)
    
    def test_metadata_with_float_team_size(self):
        """Metadata with float team_size should fail."""
        data = {
            "team_id": "team-alpha",
            "delivery_cadence": 75.0,
            "knowledge_concentration": 50.0,
            "dependency_risk": 30.0,
            "workload_distribution": 60.0,
            "attrition_signal": 20.0,
            "metadata": {
                "team_size": 8.5,
                "project_count": 3,
                "aggregation_period": "weekly"
            }
        }
        result = validate_team_signal(data)
        assert not result.is_valid
        assert "team_size" in ' '.join(result.errors)
        assert "integer" in ' '.join(result.errors).lower()
    
    def test_metadata_with_negative_project_count(self):
        """Metadata with negative project_count should fail."""
        data = {
            "team_id": "team-alpha",
            "delivery_cadence": 75.0,
            "knowledge_concentration": 50.0,
            "dependency_risk": 30.0,
            "workload_distribution": 60.0,
            "attrition_signal": 20.0,
            "metadata": {
                "team_size": 8,
                "project_count": -2,
                "aggregation_period": "weekly"
            }
        }
        result = validate_team_signal(data)
        assert not result.is_valid
        assert "project_count" in ' '.join(result.errors)
    
    def test_individual_identifier_user_dash_pattern(self):
        """Value with 'user-' pattern should be rejected."""
        data = {
            "team_id": "user-12345",
            "delivery_cadence": 75.0,
            "knowledge_concentration": 50.0,
            "dependency_risk": 30.0,
            "workload_distribution": 60.0,
            "attrition_signal": 20.0,
            "metadata": {
                "team_size": 8,
                "project_count": 3,
                "aggregation_period": "weekly"
            }
        }
        result = validate_team_signal(data)
        assert not result.is_valid
        assert "user-" in ' '.join(result.errors).lower()
    
    def test_individual_identifier_engineer_prefix(self):
        """Value with 'engineer_' prefix should be rejected."""
        data = {
            "team_id": "engineer_john_team",
            "delivery_cadence": 75.0,
            "knowledge_concentration": 50.0,
            "dependency_risk": 30.0,
            "workload_distribution": 60.0,
            "attrition_signal": 20.0,
            "metadata": {
                "team_size": 8,
                "project_count": 3,
                "aggregation_period": "weekly"
            }
        }
        result = validate_team_signal(data)
        assert not result.is_valid
        assert "engineer_" in ' '.join(result.errors).lower()
    
    def test_individual_identifier_employee_prefix(self):
        """Value with 'employee_' prefix should be rejected."""
        data = {
            "team_id": "team-alpha",
            "delivery_cadence": 75.0,
            "knowledge_concentration": 50.0,
            "dependency_risk": 30.0,
            "workload_distribution": 60.0,
            "attrition_signal": 20.0,
            "metadata": {
                "team_size": 8,
                "project_count": 3,
                "aggregation_period": "weekly",
                "lead": "employee_456"
            }
        }
        result = validate_team_signal(data)
        assert not result.is_valid
        assert "employee_" in ' '.join(result.errors).lower()
    
    def test_individual_identifier_developer_prefix(self):
        """Value with 'developer_' prefix should be rejected."""
        data = {
            "team_id": "team-alpha",
            "delivery_cadence": 75.0,
            "knowledge_concentration": 50.0,
            "dependency_risk": 30.0,
            "workload_distribution": 60.0,
            "attrition_signal": 20.0,
            "metadata": {
                "team_size": 8,
                "project_count": 3,
                "aggregation_period": "weekly",
                "owner": "developer_alice"
            }
        }
        result = validate_team_signal(data)
        assert not result.is_valid
        assert "developer_" in ' '.join(result.errors).lower()
    
    def test_individual_identifier_member_prefix(self):
        """Value with 'member_' prefix should be rejected."""
        data = {
            "team_id": "team-alpha",
            "delivery_cadence": 75.0,
            "knowledge_concentration": 50.0,
            "dependency_risk": 30.0,
            "workload_distribution": 60.0,
            "attrition_signal": 20.0,
            "metadata": {
                "team_size": 8,
                "project_count": 3,
                "aggregation_period": "weekly",
                "contact": "member_bob"
            }
        }
        result = validate_team_signal(data)
        assert not result.is_valid
        assert "member_" in ' '.join(result.errors).lower()
    
    def test_individual_identifier_email_address(self):
        """Email address should be rejected."""
        data = {
            "team_id": "team-alpha",
            "delivery_cadence": 75.0,
            "knowledge_concentration": 50.0,
            "dependency_risk": 30.0,
            "workload_distribution": 60.0,
            "attrition_signal": 20.0,
            "metadata": {
                "team_size": 8,
                "project_count": 3,
                "aggregation_period": "weekly",
                "contact": "john.doe@example.com"
            }
        }
        result = validate_team_signal(data)
        assert not result.is_valid
        assert "@" in ' '.join(result.errors)
    
    def test_individual_identifier_email_keyword(self):
        """'email' keyword in value should be rejected."""
        data = {
            "team_id": "team-alpha",
            "delivery_cadence": 75.0,
            "knowledge_concentration": 50.0,
            "dependency_risk": 30.0,
            "workload_distribution": 60.0,
            "attrition_signal": 20.0,
            "metadata": {
                "team_size": 8,
                "project_count": 3,
                "aggregation_period": "weekly",
                "contact_info": "email: team-lead"
            }
        }
        result = validate_team_signal(data)
        assert not result.is_valid
        assert "email" in ' '.join(result.errors).lower()
    
    def test_individual_identifier_userid_pattern(self):
        """'userid' pattern should be rejected."""
        data = {
            "team_id": "userid123",
            "delivery_cadence": 75.0,
            "knowledge_concentration": 50.0,
            "dependency_risk": 30.0,
            "workload_distribution": 60.0,
            "attrition_signal": 20.0,
            "metadata": {
                "team_size": 8,
                "project_count": 3,
                "aggregation_period": "weekly"
            }
        }
        result = validate_team_signal(data)
        assert not result.is_valid
        assert "userid" in ' '.join(result.errors).lower()
    
    def test_individual_identifier_username_pattern(self):
        """'username' pattern should be rejected."""
        data = {
            "team_id": "team-alpha",
            "delivery_cadence": 75.0,
            "knowledge_concentration": 50.0,
            "dependency_risk": 30.0,
            "workload_distribution": 60.0,
            "attrition_signal": 20.0,
            "metadata": {
                "team_size": 8,
                "project_count": 3,
                "aggregation_period": "weekly",
                "created_by": "username_alice"
            }
        }
        result = validate_team_signal(data)
        assert not result.is_valid
        assert "username" in ' '.join(result.errors).lower()
    
    def test_individual_identifier_case_insensitive(self):
        """Individual identifier detection should be case-insensitive."""
        data = {
            "team_id": "USER_123",
            "delivery_cadence": 75.0,
            "knowledge_concentration": 50.0,
            "dependency_risk": 30.0,
            "workload_distribution": 60.0,
            "attrition_signal": 20.0,
            "metadata": {
                "team_size": 8,
                "project_count": 3,
                "aggregation_period": "weekly"
            }
        }
        result = validate_team_signal(data)
        assert not result.is_valid
        assert "user_" in ' '.join(result.errors).lower()
    
    def test_individual_identifier_in_nested_list(self):
        """Individual identifier in nested list should be rejected."""
        data = {
            "team_id": "team-alpha",
            "delivery_cadence": 75.0,
            "knowledge_concentration": 50.0,
            "dependency_risk": 30.0,
            "workload_distribution": 60.0,
            "attrition_signal": 20.0,
            "metadata": {
                "team_size": 8,
                "project_count": 3,
                "aggregation_period": "weekly",
                "tags": ["project-a", "user_john", "backend"]
            }
        }
        result = validate_team_signal(data)
        assert not result.is_valid
        assert "user_" in ' '.join(result.errors).lower()
    
    def test_individual_identifier_deeply_nested(self):
        """Individual identifier deeply nested should be rejected."""
        data = {
            "team_id": "team-alpha",
            "delivery_cadence": 75.0,
            "knowledge_concentration": 50.0,
            "dependency_risk": 30.0,
            "workload_distribution": 60.0,
            "attrition_signal": 20.0,
            "metadata": {
                "team_size": 8,
                "project_count": 3,
                "aggregation_period": "weekly",
                "details": {
                    "location": "US",
                    "contact": {
                        "primary": "engineer_alice"
                    }
                }
            }
        }
        result = validate_team_signal(data)
        assert not result.is_valid
        assert "engineer_" in ' '.join(result.errors).lower()


class TestValidateTeamSignal:
    """Tests for comprehensive team signal validation."""
    
    def test_fully_valid_team_signal(self):
        """Fully valid team signal should pass all validations."""
        data = {
            "team_id": "team-alpha",
            "timestamp": "2024-01-15T10:00:00Z",
            "delivery_cadence": 75.0,
            "knowledge_concentration": 50.0,
            "dependency_risk": 30.0,
            "workload_distribution": 60.0,
            "attrition_signal": 20.0,
            "metadata": {
                "team_size": 8,
                "project_count": 3,
                "aggregation_period": "weekly"
            }
        }
        result = validate_team_signal(data)
        assert result.is_valid
        assert len(result.errors) == 0
        assert len(result.rejected_fields) == 0
    
    def test_individual_identifier_violation(self):
        """Individual identifier should cause validation failure."""
        data = {
            "team_id": "user_123",
            "delivery_cadence": 75.0,
            "knowledge_concentration": 50.0,
            "dependency_risk": 30.0,
            "workload_distribution": 60.0,
            "attrition_signal": 20.0,
            "metadata": {
                "team_size": 8,
                "project_count": 3,
                "aggregation_period": "weekly"
            }
        }
        result = validate_team_signal(data)
        assert not result.is_valid
        assert any("user_" in error.lower() for error in result.errors)
    
    def test_missing_dimension_violation(self):
        """Missing dimension should cause validation failure."""
        data = {
            "team_id": "team-alpha",
            "delivery_cadence": 75.0,
            "knowledge_concentration": 50.0,
            "dependency_risk": 30.0,
            "workload_distribution": 60.0,
            # Missing attrition_signal
            "metadata": {
                "team_size": 8,
                "project_count": 3,
                "aggregation_period": "weekly"
            }
        }
        result = validate_team_signal(data)
        assert not result.is_valid
        assert any("attrition_signal" in error for error in result.errors)
    
    def test_invalid_metadata_violation(self):
        """Invalid metadata should cause validation failure."""
        data = {
            "team_id": "team-alpha",
            "delivery_cadence": 75.0,
            "knowledge_concentration": 50.0,
            "dependency_risk": 30.0,
            "workload_distribution": 60.0,
            "attrition_signal": 20.0,
            "metadata": {
                "team_size": 0,  # Invalid
                "project_count": 3,
                "aggregation_period": "weekly"
            }
        }
        result = validate_team_signal(data)
        assert not result.is_valid
        assert any("team_size" in error for error in result.errors)
    
    def test_multiple_violations(self):
        """Multiple violations should all be reported."""
        data = {
            "team_id": "user_123",  # Individual identifier
            "delivery_cadence": 75.0,
            # Missing other dimensions
            "metadata": {
                "team_size": -1,  # Invalid
                "project_count": 3,
                "aggregation_period": "weekly"
            }
        }
        result = validate_team_signal(data)
        assert not result.is_valid
        assert len(result.errors) >= 3  # At least 3 violations
    
    def test_validation_result_boolean_context(self):
        """ValidationResult should work in boolean context."""
        valid_data = {
            "team_id": "team-alpha",
            "delivery_cadence": 75.0,
            "knowledge_concentration": 50.0,
            "dependency_risk": 30.0,
            "workload_distribution": 60.0,
            "attrition_signal": 20.0,
            "metadata": {
                "team_size": 8,
                "project_count": 3,
                "aggregation_period": "weekly"
            }
        }
        result = validate_team_signal(valid_data)
        assert result  # Should be truthy
        
        invalid_data = {"team_id": "user_123"}
        result = validate_team_signal(invalid_data)
        assert not result  # Should be falsy
