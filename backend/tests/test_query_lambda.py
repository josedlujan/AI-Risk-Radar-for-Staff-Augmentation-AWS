"""Unit tests for Query Lambda handler."""

import json
import pytest
from unittest.mock import Mock, patch
from decimal import Decimal
from datetime import datetime

from backend.lambdas.query.handler import handler, _format_risks, _convert_decimals


@pytest.fixture
def mock_dynamodb_client():
    """Mock DynamoDB client."""
    with patch('backend.lambdas.query.handler.DynamoDBClient') as mock:
        yield mock


@pytest.fixture
def sample_risk_items():
    """Sample risk items from DynamoDB."""
    return [
        {
            'risk_id': 'risk-001',
            'analysis_id': 'analysis-001',
            'team_id': 'team-001',
            'dimension': 'knowledge_concentration',
            'severity': 'high',
            'detected_at': '2024-01-15T10:30:00Z',
            'description_en': 'Knowledge is concentrated in few team members',
            'description_es': 'El conocimiento está concentrado en pocos miembros del equipo',
            'recommendations_en': ['Implement pair programming', 'Create documentation'],
            'recommendations_es': ['Implementar programación en parejas', 'Crear documentación'],
            'signal_values': {
                'delivery_cadence': Decimal('45.5'),
                'knowledge_concentration': Decimal('72.3'),
                'dependency_risk': Decimal('38.1'),
                'workload_distribution': Decimal('55.0'),
                'attrition_signal': Decimal('28.7')
            }
        },
        {
            'risk_id': 'risk-002',
            'analysis_id': 'analysis-001',
            'team_id': 'team-001',
            'dimension': 'workload_distribution',
            'severity': 'medium',
            'detected_at': '2024-01-15T10:30:00Z',
            'description_en': 'Workload is unevenly distributed',
            'description_es': 'La carga de trabajo está distribuida de manera desigual',
            'recommendations_en': ['Balance task assignments', 'Monitor workload metrics'],
            'recommendations_es': ['Equilibrar asignaciones de tareas', 'Monitorear métricas de carga'],
            'signal_values': {
                'delivery_cadence': Decimal('45.5'),
                'knowledge_concentration': Decimal('72.3'),
                'dependency_risk': Decimal('38.1'),
                'workload_distribution': Decimal('55.0'),
                'attrition_signal': Decimal('28.7')
            }
        }
    ]


class TestQueryLambdaHandler:
    """Tests for Query Lambda handler function."""
    
    def test_successful_query_english(self, mock_dynamodb_client, sample_risk_items):
        """Test successful query with English language."""
        # Setup mock
        mock_client_instance = Mock()
        mock_client_instance.query_risk_records.return_value = sample_risk_items
        mock_dynamodb_client.return_value = mock_client_instance
        
        # Create event
        event = {
            'queryStringParameters': {
                'team_id': 'team-001',
                'language': 'en'
            }
        }
        
        # Execute handler
        response = handler(event, None)
        
        # Verify response
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        
        assert body['team_id'] == 'team-001'
        assert body['last_analysis'] == '2024-01-15T10:30:00Z'
        assert body['risk_dimensions']['knowledge_concentration'] == 72.3
        assert len(body['risks']) == 2
        
        # Verify English content
        first_risk = body['risks'][0]
        assert first_risk['description'] == 'Knowledge is concentrated in few team members'
        assert first_risk['recommendations'] == ['Implement pair programming', 'Create documentation']
    
    def test_successful_query_spanish(self, mock_dynamodb_client, sample_risk_items):
        """Test successful query with Spanish language."""
        # Setup mock
        mock_client_instance = Mock()
        mock_client_instance.query_risk_records.return_value = sample_risk_items
        mock_dynamodb_client.return_value = mock_client_instance
        
        # Create event
        event = {
            'queryStringParameters': {
                'team_id': 'team-001',
                'language': 'es'
            }
        }
        
        # Execute handler
        response = handler(event, None)
        
        # Verify response
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        
        # Verify Spanish content
        first_risk = body['risks'][0]
        assert first_risk['description'] == 'El conocimiento está concentrado en pocos miembros del equipo'
        assert first_risk['recommendations'] == ['Implementar programación en parejas', 'Crear documentación']
    
    def test_default_language_english(self, mock_dynamodb_client, sample_risk_items):
        """Test that language defaults to English when not specified."""
        # Setup mock
        mock_client_instance = Mock()
        mock_client_instance.query_risk_records.return_value = sample_risk_items
        mock_dynamodb_client.return_value = mock_client_instance
        
        # Create event without language parameter
        event = {
            'queryStringParameters': {
                'team_id': 'team-001'
            }
        }
        
        # Execute handler
        response = handler(event, None)
        
        # Verify English is used by default
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        first_risk = body['risks'][0]
        assert first_risk['description'] == 'Knowledge is concentrated in few team members'
    
    def test_missing_team_id(self, mock_dynamodb_client):
        """Test error when team_id is missing."""
        event = {
            'queryStringParameters': {
                'language': 'en'
            }
        }
        
        response = handler(event, None)
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['status'] == 'error'
        assert 'team_id' in body['message']
    
    def test_invalid_language(self, mock_dynamodb_client):
        """Test error when language is invalid."""
        event = {
            'queryStringParameters': {
                'team_id': 'team-001',
                'language': 'fr'  # Invalid language
            }
        }
        
        response = handler(event, None)
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['status'] == 'error'
        assert 'language' in body['message']
    
    def test_empty_query_parameters(self, mock_dynamodb_client):
        """Test handling of None query parameters."""
        event = {
            'queryStringParameters': None
        }
        
        response = handler(event, None)
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['status'] == 'error'
    
    def test_no_risks_found(self, mock_dynamodb_client):
        """Test response when no risks are found for team."""
        # Setup mock to return empty list
        mock_client_instance = Mock()
        mock_client_instance.query_risk_records.return_value = []
        mock_dynamodb_client.return_value = mock_client_instance
        
        event = {
            'queryStringParameters': {
                'team_id': 'team-999',
                'language': 'en'
            }
        }
        
        response = handler(event, None)
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['team_id'] == 'team-999'
        assert body['last_analysis'] is None
        assert body['risk_dimensions'] == {}
        assert body['risks'] == []
    
    def test_dynamodb_error_handling(self, mock_dynamodb_client):
        """Test error handling when DynamoDB query fails."""
        # Setup mock to raise exception
        mock_client_instance = Mock()
        mock_client_instance.query_risk_records.side_effect = Exception("DynamoDB error")
        mock_dynamodb_client.return_value = mock_client_instance
        
        event = {
            'queryStringParameters': {
                'team_id': 'team-001',
                'language': 'en'
            }
        }
        
        response = handler(event, None)
        
        assert response['statusCode'] == 500
        body = json.loads(response['body'])
        assert body['status'] == 'error'
        assert 'Internal server error' in body['message']
    
    def test_cors_headers_present(self, mock_dynamodb_client, sample_risk_items):
        """Test that CORS headers are included in response."""
        # Setup mock
        mock_client_instance = Mock()
        mock_client_instance.query_risk_records.return_value = sample_risk_items
        mock_dynamodb_client.return_value = mock_client_instance
        
        event = {
            'queryStringParameters': {
                'team_id': 'team-001',
                'language': 'en'
            }
        }
        
        response = handler(event, None)
        
        assert 'Access-Control-Allow-Origin' in response['headers']
        assert response['headers']['Access-Control-Allow-Origin'] == '*'
        assert response['headers']['Content-Type'] == 'application/json'
    
    def test_risk_dimensions_conversion(self, mock_dynamodb_client, sample_risk_items):
        """Test that Decimal values are converted to float in risk dimensions."""
        # Setup mock
        mock_client_instance = Mock()
        mock_client_instance.query_risk_records.return_value = sample_risk_items
        mock_dynamodb_client.return_value = mock_client_instance
        
        event = {
            'queryStringParameters': {
                'team_id': 'team-001',
                'language': 'en'
            }
        }
        
        response = handler(event, None)
        body = json.loads(response['body'])
        
        # Verify all dimensions are floats
        dimensions = body['risk_dimensions']
        assert isinstance(dimensions['delivery_cadence'], float)
        assert isinstance(dimensions['knowledge_concentration'], float)
        assert isinstance(dimensions['dependency_risk'], float)
        assert isinstance(dimensions['workload_distribution'], float)
        assert isinstance(dimensions['attrition_signal'], float)


class TestFormatRisks:
    """Tests for _format_risks helper function."""
    
    def test_format_risks_english(self, sample_risk_items):
        """Test formatting risks with English language."""
        formatted = _format_risks(sample_risk_items, 'en')
        
        assert len(formatted) == 2
        assert formatted[0]['risk_id'] == 'risk-001'
        assert formatted[0]['dimension'] == 'knowledge_concentration'
        assert formatted[0]['severity'] == 'high'
        assert formatted[0]['description'] == 'Knowledge is concentrated in few team members'
        assert formatted[0]['recommendations'] == ['Implement pair programming', 'Create documentation']
    
    def test_format_risks_spanish(self, sample_risk_items):
        """Test formatting risks with Spanish language."""
        formatted = _format_risks(sample_risk_items, 'es')
        
        assert len(formatted) == 2
        assert formatted[0]['description'] == 'El conocimiento está concentrado en pocos miembros del equipo'
        assert formatted[0]['recommendations'] == ['Implementar programación en parejas', 'Crear documentación']
    
    def test_format_risks_preserves_metadata(self, sample_risk_items):
        """Test that formatting preserves all required metadata."""
        formatted = _format_risks(sample_risk_items, 'en')
        
        risk = formatted[0]
        assert 'risk_id' in risk
        assert 'dimension' in risk
        assert 'severity' in risk
        assert 'description' in risk
        assert 'detected_at' in risk
        assert 'recommendations' in risk


class TestConvertDecimals:
    """Tests for _convert_decimals helper function."""
    
    def test_convert_decimal_to_float(self):
        """Test converting Decimal to float."""
        result = _convert_decimals(Decimal('45.5'))
        assert isinstance(result, float)
        assert result == 45.5
    
    def test_convert_list_with_decimals(self):
        """Test converting list containing Decimals."""
        input_list = [Decimal('1.5'), Decimal('2.5'), 'string', 42]
        result = _convert_decimals(input_list)
        
        assert isinstance(result[0], float)
        assert isinstance(result[1], float)
        assert result[0] == 1.5
        assert result[1] == 2.5
        assert result[2] == 'string'
        assert result[3] == 42
    
    def test_convert_dict_with_decimals(self):
        """Test converting dict containing Decimals."""
        input_dict = {
            'value': Decimal('10.5'),
            'name': 'test',
            'count': 5
        }
        result = _convert_decimals(input_dict)
        
        assert isinstance(result['value'], float)
        assert result['value'] == 10.5
        assert result['name'] == 'test'
        assert result['count'] == 5
    
    def test_convert_nested_structure(self):
        """Test converting nested structure with Decimals."""
        input_data = {
            'risks': [
                {
                    'severity': 'high',
                    'score': Decimal('85.5')
                },
                {
                    'severity': 'low',
                    'score': Decimal('25.0')
                }
            ],
            'total': Decimal('110.5')
        }
        result = _convert_decimals(input_data)
        
        assert isinstance(result['risks'][0]['score'], float)
        assert isinstance(result['risks'][1]['score'], float)
        assert isinstance(result['total'], float)
        assert result['risks'][0]['score'] == 85.5
        assert result['total'] == 110.5
    
    def test_convert_preserves_non_decimal_types(self):
        """Test that non-Decimal types are preserved."""
        input_data = {
            'string': 'test',
            'int': 42,
            'float': 3.14,
            'bool': True,
            'none': None
        }
        result = _convert_decimals(input_data)
        
        assert result == input_data
