"""Integration tests for the Ingest Lambda handler with real validation and models."""

import json
import pytest
from datetime import datetime
from unittest.mock import Mock, patch

from backend.lambdas.ingest.handler import handler


@pytest.fixture
def mock_context():
    """Fixture for Lambda context."""
    context = Mock()
    context.function_name = 'ingest-lambda'
    context.request_id = 'test-request-id'
    return context


class TestIngestIntegration:
    """Integration tests for the complete ingestion flow."""
    
    @patch('backend.lambdas.ingest.handler.dynamodb_client')
    def test_complete_valid_ingestion_flow(self, mock_db_client, mock_context):
        """Test complete flow with valid data through all validation layers."""
        mock_db_client.put_team_signal.return_value = {'ResponseMetadata': {'HTTPStatusCode': 200}}
        
        event = {
            'body': json.dumps({
                'team_id': 'engineering-team-1',
                'timestamp': '2024-01-15T10:00:00Z',
                'delivery_cadence': 85.0,
                'knowledge_concentration': 42.5,
                'dependency_risk': 35.0,
                'workload_distribution': 70.0,
                'attrition_signal': 15.0,
                'metadata': {
                    'team_size': 8,
                    'project_count': 3,
                    'aggregation_period': 'weekly'
                }
            })
        }
        
        response = handler(event, mock_context)
        
        # Verify successful response
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['status'] == 'success'
        assert 'signal_id' in body
        assert 'engineering-team-1' in body['signal_id']
        
        # Verify DynamoDB was called with correct data
        assert mock_db_client.put_team_signal.called
        call_args = mock_db_client.put_team_signal.call_args[0][0]
        assert call_args.team_id == 'engineering-team-1'
        assert call_args.delivery_cadence == 85.0
        assert call_args.metadata.team_size == 8
    
    @patch('backend.lambdas.ingest.handler.dynamodb_client')
    def test_validation_catches_privacy_violation(self, mock_db_client, mock_context):
        """Test that privacy validation catches individual identifiers."""
        event = {
            'body': json.dumps({
                'team_id': 'engineering-team-1',
                'timestamp': '2024-01-15T10:00:00Z',
                'delivery_cadence': 85.0,
                'knowledge_concentration': 42.5,
                'dependency_risk': 35.0,
                'workload_distribution': 70.0,
                'attrition_signal': 15.0,
                'comment': 'engineer_john needs help',  # Privacy violation
                'metadata': {
                    'team_size': 8,
                    'project_count': 3,
                    'aggregation_period': 'weekly'
                }
            })
        }
        
        response = handler(event, mock_context)
        
        # Verify rejection
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['status'] == 'error'
        assert body['error'] == 'INDIVIDUAL_DATA_REJECTED'
        assert 'comment' in body['rejected_fields']
        
        # Verify DynamoDB was NOT called
        assert not mock_db_client.put_team_signal.called
    
    @patch('backend.lambdas.ingest.handler.dynamodb_client')
    def test_all_five_dimensions_validated(self, mock_db_client, mock_context):
        """Test that all five risk dimensions are required."""
        # Missing attrition_signal
        event = {
            'body': json.dumps({
                'team_id': 'engineering-team-1',
                'timestamp': '2024-01-15T10:00:00Z',
                'delivery_cadence': 85.0,
                'knowledge_concentration': 42.5,
                'dependency_risk': 35.0,
                'workload_distribution': 70.0,
                # Missing: attrition_signal
                'metadata': {
                    'team_size': 8,
                    'project_count': 3,
                    'aggregation_period': 'weekly'
                }
            })
        }
        
        response = handler(event, mock_context)
        
        # Verify rejection
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['error'] == 'INCOMPLETE_DIMENSIONS'
        assert 'attrition_signal' in str(body['errors'])
        
        # Verify DynamoDB was NOT called
        assert not mock_db_client.put_team_signal.called
    
    @patch('backend.lambdas.ingest.handler.dynamodb_client')
    def test_dimension_range_validation(self, mock_db_client, mock_context):
        """Test that dimension values must be in 0-100 range."""
        event = {
            'body': json.dumps({
                'team_id': 'engineering-team-1',
                'timestamp': '2024-01-15T10:00:00Z',
                'delivery_cadence': -5.0,  # Invalid: negative
                'knowledge_concentration': 42.5,
                'dependency_risk': 35.0,
                'workload_distribution': 70.0,
                'attrition_signal': 15.0,
                'metadata': {
                    'team_size': 8,
                    'project_count': 3,
                    'aggregation_period': 'weekly'
                }
            })
        }
        
        response = handler(event, mock_context)
        
        # Verify rejection
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['status'] == 'error'
        
        # Verify DynamoDB was NOT called
        assert not mock_db_client.put_team_signal.called
    
    @patch('backend.lambdas.ingest.handler.dynamodb_client')
    def test_metadata_structure_validation(self, mock_db_client, mock_context):
        """Test that metadata structure is properly validated."""
        event = {
            'body': json.dumps({
                'team_id': 'engineering-team-1',
                'timestamp': '2024-01-15T10:00:00Z',
                'delivery_cadence': 85.0,
                'knowledge_concentration': 42.5,
                'dependency_risk': 35.0,
                'workload_distribution': 70.0,
                'attrition_signal': 15.0,
                'metadata': {
                    'team_size': 8,
                    # Missing: project_count and aggregation_period
                }
            })
        }
        
        response = handler(event, mock_context)
        
        # Verify rejection
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['error'] == 'INVALID_METADATA'
        
        # Verify DynamoDB was NOT called
        assert not mock_db_client.put_team_signal.called
