"""Property-based tests for team signal validation.

Feature: team-risk-analysis
"""

import pytest
from hypothesis import given, strategies as st, assume
from backend.validation import validate_team_signal, validate_five_dimensions


# Strategy for generating valid dimension values (0-100)
dimension_value = st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False)

# Strategy for generating valid team identifiers (no individual patterns)
valid_team_id = st.text(
    alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='-_'),
    min_size=5,
    max_size=30
).filter(lambda x: not any(
    pattern in x.lower() 
    for pattern in ['user', 'engineer', 'employee', 'developer', 'member', '@', 'email', 'individual', 'person']
))

# Strategy for generating valid aggregation periods
valid_aggregation_period = st.sampled_from(['daily', 'weekly', 'biweekly', 'monthly', 'quarterly'])

# Strategy for generating valid metadata
valid_metadata = st.fixed_dictionaries({
    'team_size': st.integers(min_value=1, max_value=100),
    'project_count': st.integers(min_value=1, max_value=20),
    'aggregation_period': valid_aggregation_period
})

# Strategy for generating valid team signals
valid_team_signal = st.fixed_dictionaries({
    'team_id': valid_team_id,
    'delivery_cadence': dimension_value,
    'knowledge_concentration': dimension_value,
    'dependency_risk': dimension_value,
    'workload_distribution': dimension_value,
    'attrition_signal': dimension_value,
    'metadata': valid_metadata
})

# Strategy for generating individual identifier patterns
individual_identifier_pattern = st.sampled_from([
    'user_', 'user-', 'userid', 'username',
    'engineer_', 'engineerid',
    'employee_', 'employeeid',
    'developer_', 'developerid',
    'member_', 'memberid',
    '@example.com',
    'email:',
])

# Strategy for generating team signals with individual identifiers
team_signal_with_individual_id = st.fixed_dictionaries({
    'team_id': st.text(min_size=1, max_size=20).map(lambda x: f"user_{x}"),
    'delivery_cadence': dimension_value,
    'knowledge_concentration': dimension_value,
    'dependency_risk': dimension_value,
    'workload_distribution': dimension_value,
    'attrition_signal': dimension_value,
    'metadata': valid_metadata
})

# Strategy for generating team signals with missing metadata
team_signal_missing_metadata = st.fixed_dictionaries({
    'team_id': valid_team_id,
    'delivery_cadence': dimension_value,
    'knowledge_concentration': dimension_value,
    'dependency_risk': dimension_value,
    'workload_distribution': dimension_value,
    'attrition_signal': dimension_value,
    # metadata is intentionally missing
})

# Strategy for generating team signals with incomplete metadata
team_signal_incomplete_metadata = st.fixed_dictionaries({
    'team_id': valid_team_id,
    'delivery_cadence': dimension_value,
    'knowledge_concentration': dimension_value,
    'dependency_risk': dimension_value,
    'workload_distribution': dimension_value,
    'attrition_signal': dimension_value,
    'metadata': st.fixed_dictionaries({
        'team_size': st.integers(min_value=1, max_value=100),
        # project_count and aggregation_period are missing
    })
})


@pytest.mark.property_test
class TestPropertyAggregatedDataValidation:
    """Property 1: Aggregated Data Validation
    
    **Validates: Requirements 1.1, 1.2, 1.3, 10.1, 10.2**
    
    For any data submission to the ingestion endpoint, if the submission contains 
    individual engineer identifiers or lacks aggregation metadata, then the system 
    should reject it with an error; otherwise, it should accept and store the 
    team-level signals.
    """
    
    @given(team_signal=valid_team_signal)
    def test_valid_aggregated_data_accepted(self, team_signal):
        """Property: Valid team-level aggregated data should always be accepted.
        
        For any team signal that:
        - Contains no individual identifiers
        - Has all five risk dimensions
        - Has complete aggregation metadata
        
        The validation should succeed.
        """
        result = validate_team_signal(team_signal)
        
        assert result.is_valid, (
            f"Valid team signal was rejected. Errors: {result.errors}, "
            f"Rejected fields: {result.rejected_fields}"
        )
        assert len(result.errors) == 0
        assert len(result.rejected_fields) == 0
    
    @given(team_signal=team_signal_with_individual_id)
    def test_individual_identifiers_rejected(self, team_signal):
        """Property: Data with individual identifiers should always be rejected.
        
        For any team signal that contains individual engineer identifiers
        (user_, engineer_, employee_, etc.), the validation should fail.
        """
        result = validate_team_signal(team_signal)
        
        assert not result.is_valid, (
            f"Team signal with individual identifier was accepted: {team_signal['team_id']}"
        )
        assert len(result.errors) > 0
        assert len(result.rejected_fields) > 0
        
        # Verify error message mentions individual identifiers
        error_text = ' '.join(result.errors).lower()
        assert any(
            pattern in error_text 
            for pattern in ['user_', 'engineer_', 'employee_', 'individual', 'identifier']
        ), f"Error message should mention individual identifiers: {result.errors}"
    
    @given(team_signal=team_signal_missing_metadata)
    def test_missing_metadata_rejected(self, team_signal):
        """Property: Data without metadata should always be rejected.
        
        For any team signal that lacks the metadata field, the validation 
        should fail.
        """
        result = validate_team_signal(team_signal)
        
        assert not result.is_valid, (
            "Team signal without metadata was accepted"
        )
        assert len(result.errors) > 0
        
        # Verify error message mentions metadata
        error_text = ' '.join(result.errors).lower()
        assert 'metadata' in error_text, (
            f"Error message should mention metadata: {result.errors}"
        )
    
    @given(team_signal=team_signal_incomplete_metadata)
    def test_incomplete_metadata_rejected(self, team_signal):
        """Property: Data with incomplete metadata should always be rejected.
        
        For any team signal that has metadata but is missing required fields
        (team_size, project_count, aggregation_period), the validation should fail.
        """
        result = validate_team_signal(team_signal)
        
        assert not result.is_valid, (
            "Team signal with incomplete metadata was accepted"
        )
        assert len(result.errors) > 0
        
        # Verify error mentions missing metadata fields
        error_text = ' '.join(result.errors).lower()
        assert any(
            field in error_text 
            for field in ['project_count', 'aggregation_period']
        ), f"Error should mention missing metadata fields: {result.errors}"
    
    @given(
        team_signal=valid_team_signal,
        individual_pattern=individual_identifier_pattern
    )
    def test_nested_individual_identifiers_rejected(self, team_signal, individual_pattern):
        """Property: Individual identifiers in nested fields should be rejected.
        
        For any valid team signal, if we inject an individual identifier pattern
        into a nested field (like metadata), the validation should fail.
        """
        # Inject individual identifier into a nested field
        team_signal_copy = team_signal.copy()
        team_signal_copy['metadata'] = team_signal['metadata'].copy()
        team_signal_copy['metadata']['owner'] = individual_pattern
        
        result = validate_team_signal(team_signal_copy)
        
        assert not result.is_valid, (
            f"Team signal with nested individual identifier was accepted: {individual_pattern}"
        )
        assert len(result.errors) > 0
    
    @given(team_signal=valid_team_signal)
    def test_validation_idempotent(self, team_signal):
        """Property: Validation should be idempotent.
        
        For any team signal, validating it multiple times should produce
        the same result.
        """
        result1 = validate_team_signal(team_signal)
        result2 = validate_team_signal(team_signal)
        
        assert result1.is_valid == result2.is_valid
        assert result1.errors == result2.errors
        assert result1.rejected_fields == result2.rejected_fields
    
    @given(
        team_signal=valid_team_signal,
        dimension_to_remove=st.sampled_from([
            'delivery_cadence',
            'knowledge_concentration',
            'dependency_risk',
            'workload_distribution',
            'attrition_signal'
        ])
    )
    def test_missing_dimension_rejected(self, team_signal, dimension_to_remove):
        """Property: Missing any risk dimension should cause rejection.
        
        For any valid team signal, if we remove one of the five required
        risk dimensions, the validation should fail.
        """
        team_signal_copy = team_signal.copy()
        del team_signal_copy[dimension_to_remove]
        
        result = validate_team_signal(team_signal_copy)
        
        assert not result.is_valid, (
            f"Team signal missing '{dimension_to_remove}' was accepted"
        )
        assert len(result.errors) > 0
        
        # Verify error mentions the missing dimension
        error_text = ' '.join(result.errors).lower()
        assert dimension_to_remove in error_text, (
            f"Error should mention missing dimension '{dimension_to_remove}': {result.errors}"
        )


@pytest.mark.property_test
class TestPropertyFiveDimensionCompleteness:
    """Property 2: Five Dimension Completeness
    
    **Validates: Requirements 1.5, 2.5, 5.3, 8.2**
    
    For any team signal submission or risk analysis output, all five risk dimensions 
    (Delivery Cadence, Knowledge Concentration, Dependency Risk, Workload Distribution, 
    Attrition Signal) should be present and have valid numeric values.
    """
    
    @given(team_signal=valid_team_signal)
    def test_all_five_dimensions_present(self, team_signal):
        """Property: All five risk dimensions must be present in valid team signals.
        
        For any valid team signal, it should contain exactly five risk dimensions:
        - delivery_cadence
        - knowledge_concentration
        - dependency_risk
        - workload_distribution
        - attrition_signal
        """
        required_dimensions = [
            'delivery_cadence',
            'knowledge_concentration',
            'dependency_risk',
            'workload_distribution',
            'attrition_signal'
        ]
        
        # Check all dimensions are present
        for dimension in required_dimensions:
            assert dimension in team_signal, (
                f"Missing required dimension: {dimension}"
            )
        
        # Verify exactly 5 dimensions (excluding metadata and team_id)
        dimension_keys = [k for k in team_signal.keys() 
                         if k not in ['team_id', 'metadata', 'timestamp']]
        assert len(dimension_keys) == 5, (
            f"Expected exactly 5 dimensions, found {len(dimension_keys)}: {dimension_keys}"
        )
    
    @given(team_signal=valid_team_signal)
    def test_all_dimensions_have_numeric_values(self, team_signal):
        """Property: All five dimensions must have numeric values.
        
        For any valid team signal, each of the five risk dimensions should
        have a numeric value (int or float).
        """
        required_dimensions = [
            'delivery_cadence',
            'knowledge_concentration',
            'dependency_risk',
            'workload_distribution',
            'attrition_signal'
        ]
        
        for dimension in required_dimensions:
            value = team_signal[dimension]
            assert isinstance(value, (int, float)), (
                f"Dimension '{dimension}' must be numeric, got {type(value).__name__}: {value}"
            )
            # Ensure it's not NaN or infinity
            assert not (isinstance(value, float) and (value != value or abs(value) == float('inf'))), (
                f"Dimension '{dimension}' has invalid numeric value: {value}"
            )
    
    @given(team_signal=valid_team_signal)
    def test_all_dimensions_in_valid_range(self, team_signal):
        """Property: All five dimensions must have values in range [0, 100].
        
        For any valid team signal, each dimension value should be between
        0 and 100 inclusive.
        """
        required_dimensions = [
            'delivery_cadence',
            'knowledge_concentration',
            'dependency_risk',
            'workload_distribution',
            'attrition_signal'
        ]
        
        for dimension in required_dimensions:
            value = team_signal[dimension]
            assert 0 <= value <= 100, (
                f"Dimension '{dimension}' must be in range [0, 100], got {value}"
            )
    
    @given(
        team_signal=valid_team_signal,
        dimension_to_test=st.sampled_from([
            'delivery_cadence',
            'knowledge_concentration',
            'dependency_risk',
            'workload_distribution',
            'attrition_signal'
        ])
    )
    def test_removing_any_dimension_causes_validation_failure(self, team_signal, dimension_to_test):
        """Property: Removing any dimension should cause validation to fail.
        
        For any valid team signal, if we remove any of the five required
        dimensions, the validation should fail.
        """
        team_signal_copy = team_signal.copy()
        del team_signal_copy[dimension_to_test]
        
        result = validate_team_signal(team_signal_copy)
        
        assert not result.is_valid, (
            f"Validation should fail when '{dimension_to_test}' is missing"
        )
        assert any(dimension_to_test in error for error in result.errors), (
            f"Error message should mention missing dimension '{dimension_to_test}'"
        )
    
    @given(
        team_signal=valid_team_signal,
        dimension_to_test=st.sampled_from([
            'delivery_cadence',
            'knowledge_concentration',
            'dependency_risk',
            'workload_distribution',
            'attrition_signal'
        ]),
        invalid_value=st.one_of(
            st.floats(min_value=-1000, max_value=-0.01),  # Below range
            st.floats(min_value=100.01, max_value=1000),  # Above range
        )
    )
    def test_out_of_range_values_cause_validation_failure(self, team_signal, dimension_to_test, invalid_value):
        """Property: Values outside [0, 100] should cause validation to fail.
        
        For any valid team signal, if we set any dimension to a value
        outside the valid range [0, 100], validation should fail.
        """
        team_signal_copy = team_signal.copy()
        team_signal_copy[dimension_to_test] = invalid_value
        
        result = validate_team_signal(team_signal_copy)
        
        assert not result.is_valid, (
            f"Validation should fail when '{dimension_to_test}' = {invalid_value}"
        )
        assert any(
            dimension_to_test in error and ('0' in error or '100' in error)
            for error in result.errors
        ), (
            f"Error message should mention dimension '{dimension_to_test}' and valid range"
        )
    
    @given(
        team_signal=valid_team_signal,
        dimension_to_test=st.sampled_from([
            'delivery_cadence',
            'knowledge_concentration',
            'dependency_risk',
            'workload_distribution',
            'attrition_signal'
        ]),
        non_numeric_value=st.one_of(
            st.text(min_size=1, max_size=20),
            st.none(),
            st.booleans(),
            st.lists(st.integers()),
        )
    )
    def test_non_numeric_values_cause_validation_failure(self, team_signal, dimension_to_test, non_numeric_value):
        """Property: Non-numeric values should cause validation to fail.
        
        For any valid team signal, if we set any dimension to a non-numeric
        value (string, None, boolean, list, etc.), validation should fail.
        """
        # Skip if the value happens to be numeric
        assume(not isinstance(non_numeric_value, (int, float)))
        
        team_signal_copy = team_signal.copy()
        team_signal_copy[dimension_to_test] = non_numeric_value
        
        result = validate_team_signal(team_signal_copy)
        
        assert not result.is_valid, (
            f"Validation should fail when '{dimension_to_test}' = {non_numeric_value} "
            f"(type: {type(non_numeric_value).__name__})"
        )
    
    @given(team_signal=valid_team_signal)
    def test_dimension_completeness_is_independent_of_other_validations(self, team_signal):
        """Property: Five dimension check should be independent.
        
        For any valid team signal with all five dimensions present and valid,
        the five dimension validation should pass regardless of other fields.
        """
        # Validate just the five dimensions
        result = validate_five_dimensions(team_signal)
        
        assert result.is_valid, (
            f"Five dimension validation should pass for valid dimensions. "
            f"Errors: {result.errors}"
        )
        assert len(result.errors) == 0
        assert len(result.rejected_fields) == 0
