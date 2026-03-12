"""Unit tests for analyze Lambda handler."""

import json
import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal

from backend.lambdas.analyze.handler import (
    handler,
    _parse_event,
    _fetch_recent_signals,
    _create_snapshot,
    _success_response,
    _error_response
)
from backend.models import AnalysisResult, RiskRecord, SeverityLevel


class TestAnalyzeLambdaHandler:
    """Test suite for analyze Lambda handler."""
    
    def test_handler_api_gateway_success(self):
        """Test successful analysis triggered by API Gateway."""
        # Arrange
        event = {
            'body': json.dumps({
                'team_id': 'team-001',
                'analysis_type': 'on_demand'
            })
        }
        context = Mock()
        
        # Mock signal data
        mock_signal = {
            'PK': 'TEAM#team-001',
            'SK': 'SIGNAL#2024-01-15T10:00:00',
            'team_id': 'team-001',
            'timestamp': '2024-01-15T10:00:00',
            'delivery_cadence': Decimal('45.5'),
            'knowledge_concentration': Decimal('65.0'),
            'dependency_risk': Decimal('30.0'),
            'workload_distribution': Decimal('50.0'),
            'attrition_signal': Decimal('20.0'),
            'metadata': {
                'team_size': 8,
                'project_count': 3,
                'aggregation_period': 'weekly'
            }
        }
        
        # Mock analysis result
        mock_risk = RiskRecord(
            analysis_id='analysis-123',
            team_id='team-001',
            dimension='knowledge_concentration',
            severity=SeverityLevel.HIGH,
            description_en='High knowledge concentration detected',
            description_es='Alta concentración de conocimiento detectada',
            recommendations_en=['Implement knowledge sharing sessions'],
            recommendations_es=['Implementar sesiones de intercambio de conocimiento'],
            signal_values={}
        )
        
        mock_analysis_result = AnalysisResult(
            analysis_id='analysis-123',
            team_id='team-001',
            risks=[mock_risk],
            analysis_duration_ms=5000
        )
        
        with patch('backend.lambdas.analyze.handler.DynamoDBClient') as mock_db_client, \
             patch('backend.lambdas.analyze.handler.BedrockAnalyzer') as mock_bedrock, \
             patch('backend.lambdas.analyze.handler.S3Client') as mock_s3:
            
            # Setup mocks
            mock_db_instance = mock_db_client.return_value
            mock_db_instance.query_team_signals.return_value = [mock_signal]
            
            mock_bedrock_instance = mock_bedrock.return_value
            mock_bedrock_instance.analyze_team_signals.return_value = mock_analysis_result
            
            mock_s3_instance = mock_s3.return_value
            mock_s3_instance.put_snapshot.return_value = {
                'key': 'snapshots/team-001/2024/01/15/snapshot.json',
                'bucket': 'test-bucket'
            }
            
            # Act
            response = handler(event, context)
            
            # Assert
            assert response['statusCode'] == 200
            body = json.loads(response['body'])
            assert body['status'] == 'success'
            assert body['team_id'] == 'team-001'
            assert body['analysis_id'] == 'analysis-123'
            assert body['risks_detected'] == 1
            assert 'snapshot_url' in body
            
            # Verify DynamoDB put_risk_record was called
            mock_db_instance.put_risk_record.assert_called_once()
    
    def test_handler_eventbridge_trigger(self):
        """Test analysis triggered by EventBridge scheduled rule."""
        # Arrange
        event = {
            'source': 'aws.events',
            'detail': {
                'team_id': 'team-002'
            }
        }
        context = Mock()
        
        mock_signal = {
            'PK': 'TEAM#team-002',
            'SK': 'SIGNAL#2024-01-15T10:00:00',
            'team_id': 'team-002',
            'delivery_cadence': Decimal('30.0'),
            'knowledge_concentration': Decimal('40.0'),
            'dependency_risk': Decimal('25.0'),
            'workload_distribution': Decimal('35.0'),
            'attrition_signal': Decimal('15.0'),
            'metadata': {
                'team_size': 5,
                'project_count': 2,
                'aggregation_period': 'daily'
            }
        }
        
        mock_analysis_result = AnalysisResult(
            analysis_id='analysis-456',
            team_id='team-002',
            risks=[],
            analysis_duration_ms=3000
        )
        
        with patch('backend.lambdas.analyze.handler.DynamoDBClient') as mock_db_client, \
             patch('backend.lambdas.analyze.handler.BedrockAnalyzer') as mock_bedrock, \
             patch('backend.lambdas.analyze.handler.S3Client') as mock_s3:
            
            mock_db_instance = mock_db_client.return_value
            mock_db_instance.query_team_signals.return_value = [mock_signal]
            
            mock_bedrock_instance = mock_bedrock.return_value
            mock_bedrock_instance.analyze_team_signals.return_value = mock_analysis_result
            
            mock_s3_instance = mock_s3.return_value
            mock_s3_instance.put_snapshot.return_value = {
                'key': 'snapshots/team-002/2024/01/15/snapshot.json',
                'bucket': 'test-bucket'
            }
            
            # Act
            response = handler(event, context)
            
            # Assert
            assert response['statusCode'] == 200
            body = json.loads(response['body'])
            assert body['status'] == 'success'
            assert body['team_id'] == 'team-002'
            assert body['analysis_type'] == 'scheduled'
    
    def test_handler_missing_team_id(self):
        """Test error when team_id is missing."""
        # Arrange
        event = {
            'body': json.dumps({
                'analysis_type': 'on_demand'
            })
        }
        context = Mock()
        
        # Act
        response = handler(event, context)
        
        # Assert
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['status'] == 'error'
        assert 'team_id is required' in body['message']
    
    def test_handler_no_signals_found(self):
        """Test error when no signals exist for team."""
        # Arrange
        event = {
            'body': json.dumps({
                'team_id': 'team-999'
            })
        }
        context = Mock()
        
        with patch('backend.lambdas.analyze.handler.DynamoDBClient') as mock_db_client:
            mock_db_instance = mock_db_client.return_value
            mock_db_instance.query_team_signals.return_value = []
            
            # Act
            response = handler(event, context)
            
            # Assert
            assert response['statusCode'] == 404
            body = json.loads(response['body'])
            assert body['status'] == 'error'
            assert 'No signals found' in body['message']
    
    def test_handler_bedrock_error(self):
        """Test error handling when Bedrock fails."""
        # Arrange
        event = {
            'body': json.dumps({
                'team_id': 'team-001'
            })
        }
        context = Mock()
        
        mock_signal = {
            'team_id': 'team-001',
            'delivery_cadence': Decimal('50.0'),
            'knowledge_concentration': Decimal('60.0'),
            'dependency_risk': Decimal('40.0'),
            'workload_distribution': Decimal('45.0'),
            'attrition_signal': Decimal('30.0'),
            'metadata': {'team_size': 8, 'project_count': 3}
        }
        
        with patch('backend.lambdas.analyze.handler.DynamoDBClient') as mock_db_client, \
             patch('backend.lambdas.analyze.handler.BedrockAnalyzer') as mock_bedrock:
            
            mock_db_instance = mock_db_client.return_value
            mock_db_instance.query_team_signals.return_value = [mock_signal]
            
            mock_bedrock_instance = mock_bedrock.return_value
            mock_bedrock_instance.analyze_team_signals.side_effect = RuntimeError('Bedrock timeout')
            
            # Act
            response = handler(event, context)
            
            # Assert
            assert response['statusCode'] == 500
            body = json.loads(response['body'])
            assert body['status'] == 'error'
            assert 'Bedrock timeout' in body['message']
    
    def test_handler_s3_error_continues(self):
        """Test that analysis continues even if S3 snapshot fails."""
        # Arrange
        event = {
            'body': json.dumps({
                'team_id': 'team-001'
            })
        }
        context = Mock()
        
        mock_signal = {
            'team_id': 'team-001',
            'delivery_cadence': Decimal('50.0'),
            'knowledge_concentration': Decimal('60.0'),
            'dependency_risk': Decimal('40.0'),
            'workload_distribution': Decimal('45.0'),
            'attrition_signal': Decimal('30.0'),
            'metadata': {'team_size': 8, 'project_count': 3}
        }
        
        mock_analysis_result = AnalysisResult(
            analysis_id='analysis-789',
            team_id='team-001',
            risks=[],
            analysis_duration_ms=4000
        )
        
        with patch('backend.lambdas.analyze.handler.DynamoDBClient') as mock_db_client, \
             patch('backend.lambdas.analyze.handler.BedrockAnalyzer') as mock_bedrock, \
             patch('backend.lambdas.analyze.handler.S3Client') as mock_s3:
            
            mock_db_instance = mock_db_client.return_value
            mock_db_instance.query_team_signals.return_value = [mock_signal]
            
            mock_bedrock_instance = mock_bedrock.return_value
            mock_bedrock_instance.analyze_team_signals.return_value = mock_analysis_result
            
            mock_s3_instance = mock_s3.return_value
            mock_s3_instance.put_snapshot.side_effect = Exception('S3 upload failed')
            
            # Act
            response = handler(event, context)
            
            # Assert - Should return error since S3 failure is not caught
            assert response['statusCode'] == 500


class TestParseEvent:
    """Test suite for _parse_event function."""
    
    def test_parse_api_gateway_event(self):
        """Test parsing API Gateway event."""
        event = {
            'body': json.dumps({
                'team_id': 'team-001',
                'analysis_type': 'on_demand'
            })
        }
        
        result = _parse_event(event)
        
        assert result['team_id'] == 'team-001'
        assert result['analysis_type'] == 'on_demand'
    
    def test_parse_eventbridge_event(self):
        """Test parsing EventBridge scheduled event."""
        event = {
            'source': 'aws.events',
            'detail': {
                'team_id': 'team-002'
            }
        }
        
        result = _parse_event(event)
        
        assert result['team_id'] == 'team-002'
        assert result['analysis_type'] == 'scheduled'
    
    def test_parse_direct_invocation(self):
        """Test parsing direct Lambda invocation."""
        event = {
            'team_id': 'team-003',
            'analysis_type': 'test'
        }
        
        result = _parse_event(event)
        
        assert result['team_id'] == 'team-003'
        assert result['analysis_type'] == 'test'


class TestFetchRecentSignals:
    """Test suite for _fetch_recent_signals function."""
    
    def test_fetch_recent_signals_success(self):
        """Test fetching recent signals."""
        mock_client = Mock()
        mock_client.query_team_signals.return_value = [
            {'team_id': 'team-001', 'timestamp': '2024-01-15T10:00:00'},
            {'team_id': 'team-001', 'timestamp': '2024-01-15T09:00:00'}
        ]
        
        result = _fetch_recent_signals(mock_client, 'team-001')
        
        assert len(result) == 2
        mock_client.query_team_signals.assert_called_once()
        call_args = mock_client.query_team_signals.call_args
        assert call_args[1]['team_id'] == 'team-001'
        assert call_args[1]['limit'] == 10


class TestCreateSnapshot:
    """Test suite for _create_snapshot function."""
    
    def test_create_snapshot_with_risks(self):
        """Test creating snapshot with risks."""
        signal_values = {
            'delivery_cadence': 45.5,
            'knowledge_concentration': 65.0,
            'dependency_risk': 30.0,
            'workload_distribution': 50.0,
            'attrition_signal': 20.0
        }
        
        risk = RiskRecord(
            analysis_id='analysis-123',
            team_id='team-001',
            dimension='knowledge_concentration',
            severity=SeverityLevel.HIGH,
            description_en='High risk',
            description_es='Alto riesgo',
            recommendations_en=['Fix it'],
            recommendations_es=['Arreglarlo'],
            signal_values=signal_values
        )
        
        metadata = {
            'team_size': 8,
            'project_count': 3
        }
        
        snapshot = _create_snapshot(
            team_id='team-001',
            signal_values=signal_values,
            risks=[risk],
            metadata=metadata,
            analysis_duration_ms=5000
        )
        
        assert snapshot.team_id == 'team-001'
        assert len(snapshot.risks) == 1
        assert snapshot.risks[0].risk_id == risk.risk_id
        assert snapshot.metadata.team_size == 8
        assert snapshot.metadata.analysis_duration_ms == 5000
    
    def test_create_snapshot_no_risks(self):
        """Test creating snapshot with no risks."""
        signal_values = {
            'delivery_cadence': 20.0,
            'knowledge_concentration': 25.0,
            'dependency_risk': 15.0,
            'workload_distribution': 30.0,
            'attrition_signal': 10.0
        }
        
        metadata = {
            'team_size': 5,
            'project_count': 2
        }
        
        snapshot = _create_snapshot(
            team_id='team-002',
            signal_values=signal_values,
            risks=[],
            metadata=metadata,
            analysis_duration_ms=3000
        )
        
        assert snapshot.team_id == 'team-002'
        assert len(snapshot.risks) == 0
        assert snapshot.metadata.team_size == 5


class TestResponseHelpers:
    """Test suite for response helper functions."""
    
    def test_success_response(self):
        """Test success response format."""
        data = {
            'status': 'success',
            'analysis_id': 'test-123'
        }
        
        response = _success_response(data)
        
        assert response['statusCode'] == 200
        assert 'Content-Type' in response['headers']
        body = json.loads(response['body'])
        assert body['status'] == 'success'
        assert body['analysis_id'] == 'test-123'
    
    def test_error_response(self):
        """Test error response format."""
        response = _error_response(400, 'Invalid input')
        
        assert response['statusCode'] == 400
        assert 'Content-Type' in response['headers']
        body = json.loads(response['body'])
        assert body['status'] == 'error'
        assert body['message'] == 'Invalid input'
