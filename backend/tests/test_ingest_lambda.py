"""Unit tests for the Ingest Lambda handler."""

import json
import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from botocore.exceptions import ClientError

from backend.lambdas.ingest.handler import handler, _determine_error_code, _format_error_message
from backend.validation.team_signal_validator import ValidationResult


@pytest.fixture
def valid_signal_event():
    """Fixture for a valid team signal event."""
    return {
        'body': json.dumps({
            'team_id': 'team-alpha',
            'timestamp': '2024-01-15T10:00:00Z',
            'delivery_cadence': 75.5,
            'knowledge_concentration': 45.0,
            'dependency_risk': 30.0,
            'workload_distribution': 60.0,
            'attrition_signal': 20.0,
            'metadata': {
                'team_size': 8,
                'project_count': 3,
                'aggregation_period': 'weekly'
            }
        })
    }


@pytest.fixture
def invalid_signal_with_individual_data():
    """Fixture for signal with individual identifiers."""
    return {
        'body': json.dumps({
            'team_id': 'team-alpha',
            'timestamp': '2024-01-15T10:00:00Z',
            'delivery_cadence': 75.5,
            'knowledge_concentration': 45.0,
            'dependency_risk': 30.0,
            'workload_distribution': 60.0,
            'attrition_signal': 20.0,
            'notes': 'user_john contributed most',  # Individual identifier in value
            'metadata': {
                'team_size': 8,
                'project_count': 3,
                'aggregation_period': 'weekly'
            }
        })
    }


@pytest.fixture
def signal_missing_dimensions():
    """Fixture for signal missing required dimensions."""
    return {
        'body': json.dumps({
            'team_id': 'team-alpha',
            'timestamp': '2024-01-15T10:00:00Z',
            'delivery_cadence': 75.5,
            'knowledge_concentration': 45.0,
            # Missing: dependency_risk, workload_distribution, attrition_signal
            'metadata': {
                'team_size': 8,
                'project_count': 3,
                'aggregation_period': 'weekly'
            }
        })
    }


@pytest.fixture
def signal_missing_metadata():
    """Fixture for signal with missing metadata."""
    return {
        'body': json.dumps({
            'team_id': 'team-alpha',
            'timestamp': '2024-01-15T10:00:00Z',
            'delivery_cadence': 75.5,
            'knowledge_concentration': 45.0,
            'dependency_risk': 30.0,
            'workload_distribution': 60.0,
            'attrition_signal': 20.0
            # Missing metadata field
        })
    }


@pytest.fixture
def mock_context():
    """Fixture for Lambda context."""
    context = Mock()
    context.function_name = 'ingest-lambda'
    context.request_id = 'test-request-id'
    return context


class TestIngestLambdaHandler:
    """Test cases for the Ingest Lambda handler."""
    
    @patch('backend.lambdas.ingest.handler.dynamodb_client')
    def test_successful_ingestion(self, mock_db_client, valid_signal_event, mock_context):
        """Test successful signal ingestion flow."""
        # Mock DynamoDB put operation
        mock_db_client.put_team_signal.return_value = {'ResponseMetadata': {'HTTPStatusCode': 200}}
        
        # Call handler
        response = handler(valid_signal_event, mock_context)
        
        # Verify response
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['status'] == 'success'
        assert 'signal_id' in body
        assert body['message'] == 'Team signal successfully ingested'
        
        # Verify DynamoDB was called
        assert mock_db_client.put_team_signal.called
    
    @patch('backend.lambdas.ingest.handler.dynamodb_client')
    def test_reject_individual_data(self, mock_db_client, invalid_signal_with_individual_data, mock_context):
        """Test rejection of data with individual identifiers."""
        # Call handler
        response = handler(invalid_signal_with_individual_data, mock_context)
        
        # Verify error response
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['status'] == 'error'
        assert body['error'] == 'INDIVIDUAL_DATA_REJECTED'
        assert 'Individual engineer data not permitted' in body['message']
        assert 'rejected_fields' in body
        
        # Verify DynamoDB was NOT called
        assert not mock_db_client.put_team_signal.called
    
    @patch('backend.lambdas.ingest.handler.dynamodb_client')
    def test_reject_missing_dimensions(self, mock_db_client, signal_missing_dimensions, mock_context):
        """Test rejection of signal with missing dimensions."""
        # Call handler
        response = handler(signal_missing_dimensions, mock_context)
        
        # Verify error response
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['status'] == 'error'
        assert body['error'] == 'INCOMPLETE_DIMENSIONS'
        assert 'All five risk dimensions required' in body['message']
        
        # Verify DynamoDB was NOT called
        assert not mock_db_client.put_team_signal.called
    
    @patch('backend.lambdas.ingest.handler.dynamodb_client')
    def test_reject_missing_metadata(self, mock_db_client, signal_missing_metadata, mock_context):
        """Test rejection of signal with missing metadata."""
        # Call handler
        response = handler(signal_missing_metadata, mock_context)
        
        # Verify error response
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['status'] == 'error'
        assert body['error'] == 'INVALID_METADATA'
        assert 'metadata' in body['message'].lower()
        
        # Verify DynamoDB was NOT called
        assert not mock_db_client.put_team_signal.called
    
    @patch('backend.lambdas.ingest.handler.dynamodb_client')
    def test_dynamodb_storage_error(self, mock_db_client, valid_signal_event, mock_context):
        """Test handling of DynamoDB storage errors."""
        # Mock DynamoDB error
        mock_db_client.put_team_signal.side_effect = ClientError(
            error_response={'Error': {'Code': 'InternalServerError', 'Message': 'Service error'}},
            operation_name='PutItem'
        )
        
        # Call handler
        response = handler(valid_signal_event, mock_context)
        
        # Verify error response
        assert response['statusCode'] == 500
        body = json.loads(response['body'])
        assert body['status'] == 'error'
        assert body['error'] == 'STORAGE_FAILURE'
        assert 'Failed to store team signal' in body['message']
    
    def test_invalid_json(self, mock_context):
        """Test handling of invalid JSON in request body."""
        event = {'body': 'invalid json {'}
        
        # Call handler
        response = handler(event, mock_context)
        
        # Verify error response
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['status'] == 'error'
        assert body['error'] == 'INVALID_JSON'
    
    @patch('backend.lambdas.ingest.handler.dynamodb_client')
    def test_invalid_dimension_values(self, mock_db_client, mock_context):
        """Test rejection of invalid dimension values (out of range)."""
        event = {
            'body': json.dumps({
                'team_id': 'team-alpha',
                'timestamp': '2024-01-15T10:00:00Z',
                'delivery_cadence': 150.0,  # Invalid: > 100
                'knowledge_concentration': 45.0,
                'dependency_risk': 30.0,
                'workload_distribution': 60.0,
                'attrition_signal': 20.0,
                'metadata': {
                    'team_size': 8,
                    'project_count': 3,
                    'aggregation_period': 'weekly'
                }
            })
        }
        
        # Call handler
        response = handler(event, mock_context)
        
        # Verify error response
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['status'] == 'error'
    
    @patch('backend.lambdas.ingest.handler.dynamodb_client')
    def test_cors_headers_present(self, mock_db_client, valid_signal_event, mock_context):
        """Test that CORS headers are present in response."""
        mock_db_client.put_team_signal.return_value = {'ResponseMetadata': {'HTTPStatusCode': 200}}
        
        # Call handler
        response = handler(valid_signal_event, mock_context)
        
        # Verify CORS headers
        assert 'Access-Control-Allow-Origin' in response['headers']
        assert response['headers']['Access-Control-Allow-Origin'] == '*'
        assert response['headers']['Content-Type'] == 'application/json'


class TestHelperFunctions:
    """Test cases for helper functions."""
    
    def test_determine_error_code_individual_data(self):
        """Test error code determination for individual data."""
        result = ValidationResult(
            is_valid=False,
            errors=['Field contains individual identifier pattern'],
            rejected_fields=['engineer_name']
        )
        
        error_code = _determine_error_code(result)
        assert error_code == 'INDIVIDUAL_DATA_REJECTED'
    
    def test_determine_error_code_missing_dimensions(self):
        """Test error code determination for missing dimensions."""
        result = ValidationResult(
            is_valid=False,
            errors=['Missing required dimension: delivery_cadence'],
            rejected_fields=['delivery_cadence']
        )
        
        error_code = _determine_error_code(result)
        assert error_code == 'INCOMPLETE_DIMENSIONS'
    
    def test_determine_error_code_invalid_metadata(self):
        """Test error code determination for invalid metadata."""
        result = ValidationResult(
            is_valid=False,
            errors=['Missing required metadata field: team_size'],
            rejected_fields=['metadata.team_size']
        )
        
        error_code = _determine_error_code(result)
        assert error_code == 'INVALID_METADATA'
    
    def test_format_error_message_individual_data(self):
        """Test error message formatting for individual data."""
        result = ValidationResult(
            is_valid=False,
            errors=['Field contains individual identifier pattern'],
            rejected_fields=['engineer_name']
        )
        
        message = _format_error_message(result)
        assert 'Individual engineer data not permitted' in message
    
    def test_format_error_message_missing_dimensions(self):
        """Test error message formatting for missing dimensions."""
        result = ValidationResult(
            is_valid=False,
            errors=['Missing required dimension: delivery_cadence'],
            rejected_fields=['delivery_cadence']
        )
        
        message = _format_error_message(result)
        assert 'All five risk dimensions required' in message
