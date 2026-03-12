"""Unit tests for DynamoDB client wrapper."""

import pytest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock
from botocore.exceptions import ClientError

from backend.data_access.dynamodb_client import DynamoDBClient
from backend.models.team_signal import TeamSignal, SignalMetadata
from backend.models.risk_record import RiskRecord, SeverityLevel


@pytest.fixture
def mock_dynamodb_resource():
    """Mock boto3 DynamoDB resource."""
    with patch('backend.data_access.dynamodb_client.boto3.resource') as mock_resource:
        mock_table = MagicMock()
        mock_resource.return_value.Table.return_value = mock_table
        yield mock_resource, mock_table


@pytest.fixture
def dynamodb_client(mock_dynamodb_resource):
    """Create DynamoDB client with mocked resource."""
    _, _ = mock_dynamodb_resource
    return DynamoDBClient(
        team_signals_table_name='TestTeamSignals',
        risk_records_table_name='TestRiskRecords'
    )


@pytest.fixture
def sample_team_signal():
    """Create a sample team signal."""
    return TeamSignal(
        team_id="team-alpha",
        timestamp=datetime(2024, 1, 15, 10, 30, 0),
        delivery_cadence=75.5,
        knowledge_concentration=45.2,
        dependency_risk=30.8,
        workload_distribution=60.0,
        attrition_signal=20.5,
        metadata=SignalMetadata(
            team_size=8,
            project_count=3,
            aggregation_period="weekly"
        )
    )


@pytest.fixture
def sample_risk_record():
    """Create a sample risk record."""
    return RiskRecord(
        risk_id="risk-123",
        analysis_id="analysis-456",
        team_id="team-alpha",
        dimension="delivery_cadence",
        severity=SeverityLevel.HIGH,
        detected_at=datetime(2024, 1, 15, 10, 30, 0),
        description_en="High delivery risk detected",
        description_es="Riesgo de entrega alto detectado",
        recommendations_en=["Improve sprint planning"],
        recommendations_es=["Mejorar la planificación del sprint"],
        signal_values={
            "delivery_cadence": 75.5,
            "knowledge_concentration": 45.2,
            "dependency_risk": 30.8,
            "workload_distribution": 60.0,
            "attrition_signal": 20.5
        }
    )


class TestTeamSignalOperations:
    """Test TeamSignals table operations."""
    
    def test_put_team_signal_success(self, dynamodb_client, mock_dynamodb_resource, sample_team_signal):
        """Test successful team signal storage."""
        _, mock_table = mock_dynamodb_resource
        mock_table.put_item.return_value = {'ResponseMetadata': {'HTTPStatusCode': 200}}
        
        result = dynamodb_client.put_team_signal(sample_team_signal)
        
        assert result['ResponseMetadata']['HTTPStatusCode'] == 200
        mock_table.put_item.assert_called_once()
        
        # Verify the item structure
        call_args = mock_table.put_item.call_args
        item = call_args.kwargs['Item']
        
        assert item['PK'] == 'TEAM#team-alpha'
        assert item['SK'] == 'SIGNAL#2024-01-15T10:30:00'
        assert item['team_id'] == 'team-alpha'
        assert 'ttl' in item
        # Verify floats are converted to Decimal
        assert isinstance(item['delivery_cadence'], Decimal)
        assert item['delivery_cadence'] == Decimal('75.5')

    def test_put_team_signal_with_ttl(self, dynamodb_client, mock_dynamodb_resource, sample_team_signal):
        """Test that TTL is set for 90-day retention."""
        _, mock_table = mock_dynamodb_resource
        mock_table.put_item.return_value = {'ResponseMetadata': {'HTTPStatusCode': 200}}
        
        before_time = datetime.now(timezone.utc) + timedelta(days=90)
        dynamodb_client.put_team_signal(sample_team_signal)
        after_time = datetime.now(timezone.utc) + timedelta(days=90)
        
        call_args = mock_table.put_item.call_args
        item = call_args.kwargs['Item']
        
        assert 'ttl' in item
        ttl_timestamp = item['ttl']
        assert int(before_time.timestamp()) <= ttl_timestamp <= int(after_time.timestamp())
    
    def test_put_team_signal_failure(self, dynamodb_client, mock_dynamodb_resource, sample_team_signal):
        """Test handling of DynamoDB put failure."""
        _, mock_table = mock_dynamodb_resource
        mock_table.put_item.side_effect = ClientError(
            {'Error': {'Code': 'ProvisionedThroughputExceededException', 'Message': 'Throttled'}},
            'PutItem'
        )
        
        with pytest.raises(ClientError) as exc_info:
            dynamodb_client.put_team_signal(sample_team_signal)
        
        assert 'Failed to store team signal' in str(exc_info.value)
    
    def test_query_team_signals_all(self, dynamodb_client, mock_dynamodb_resource):
        """Test querying all signals for a team."""
        _, mock_table = mock_dynamodb_resource
        mock_table.query.return_value = {
            'Items': [
                {'PK': 'TEAM#team-alpha', 'SK': 'SIGNAL#2024-01-15T10:30:00'},
                {'PK': 'TEAM#team-alpha', 'SK': 'SIGNAL#2024-01-14T10:30:00'}
            ]
        }
        
        results = dynamodb_client.query_team_signals('team-alpha')
        
        assert len(results) == 2
        mock_table.query.assert_called_once()
        
        # Verify query parameters
        call_args = mock_table.query.call_args
        assert 'KeyConditionExpression' in call_args.kwargs
        assert call_args.kwargs['ScanIndexForward'] is False  # Most recent first
    
    def test_query_team_signals_with_time_range(self, dynamodb_client, mock_dynamodb_resource):
        """Test querying signals within a time range."""
        _, mock_table = mock_dynamodb_resource
        mock_table.query.return_value = {'Items': []}
        
        start_time = datetime(2024, 1, 1, 0, 0, 0)
        end_time = datetime(2024, 1, 31, 23, 59, 59)
        
        dynamodb_client.query_team_signals('team-alpha', start_time=start_time, end_time=end_time)
        
        mock_table.query.assert_called_once()
    
    def test_query_team_signals_with_limit(self, dynamodb_client, mock_dynamodb_resource):
        """Test querying signals with a limit."""
        _, mock_table = mock_dynamodb_resource
        mock_table.query.return_value = {'Items': []}
        
        dynamodb_client.query_team_signals('team-alpha', limit=10)
        
        call_args = mock_table.query.call_args
        assert call_args.kwargs['Limit'] == 10
    
    def test_query_team_signals_failure(self, dynamodb_client, mock_dynamodb_resource):
        """Test handling of query failure."""
        _, mock_table = mock_dynamodb_resource
        mock_table.query.side_effect = ClientError(
            {'Error': {'Code': 'InternalServerError', 'Message': 'Server error'}},
            'Query'
        )
        
        with pytest.raises(ClientError) as exc_info:
            dynamodb_client.query_team_signals('team-alpha')
        
        assert 'Failed to query team signals' in str(exc_info.value)
    
    def test_scan_team_signals_all(self, dynamodb_client, mock_dynamodb_resource):
        """Test scanning all team signals."""
        _, mock_table = mock_dynamodb_resource
        mock_table.scan.return_value = {
            'Items': [
                {'PK': 'TEAM#team-alpha', 'SK': 'SIGNAL#2024-01-15T10:30:00'},
                {'PK': 'TEAM#team-beta', 'SK': 'SIGNAL#2024-01-15T10:30:00'}
            ]
        }
        
        results = dynamodb_client.scan_team_signals()
        
        assert len(results) == 2
        mock_table.scan.assert_called_once()
    
    def test_scan_team_signals_with_pagination(self, dynamodb_client, mock_dynamodb_resource):
        """Test scanning with pagination."""
        _, mock_table = mock_dynamodb_resource
        
        # First call returns items with LastEvaluatedKey
        mock_table.scan.side_effect = [
            {
                'Items': [{'PK': 'TEAM#team-alpha', 'SK': 'SIGNAL#1'}],
                'LastEvaluatedKey': {'PK': 'TEAM#team-alpha', 'SK': 'SIGNAL#1'}
            },
            {
                'Items': [{'PK': 'TEAM#team-beta', 'SK': 'SIGNAL#2'}]
            }
        ]
        
        results = dynamodb_client.scan_team_signals()
        
        assert len(results) == 2
        assert mock_table.scan.call_count == 2
    
    def test_scan_team_signals_with_limit(self, dynamodb_client, mock_dynamodb_resource):
        """Test scanning with a limit."""
        _, mock_table = mock_dynamodb_resource
        mock_table.scan.return_value = {'Items': []}
        
        dynamodb_client.scan_team_signals(limit=50)
        
        call_args = mock_table.scan.call_args
        assert call_args.kwargs['Limit'] == 50


class TestRiskRecordOperations:
    """Test RiskRecords table operations."""
    
    def test_put_risk_record_success(self, dynamodb_client, mock_dynamodb_resource, sample_risk_record):
        """Test successful risk record storage."""
        _, mock_table = mock_dynamodb_resource
        mock_table.put_item.return_value = {'ResponseMetadata': {'HTTPStatusCode': 200}}
        
        result = dynamodb_client.put_risk_record(sample_risk_record)
        
        assert result['ResponseMetadata']['HTTPStatusCode'] == 200
        mock_table.put_item.assert_called_once()
        
        # Verify the item structure
        call_args = mock_table.put_item.call_args
        item = call_args.kwargs['Item']
        
        assert item['PK'] == 'TEAM#team-alpha'
        assert item['SK'] == 'RISK#analysis-456#risk-123'
        assert item['risk_id'] == 'risk-123'
        assert item['severity'] == 'high'
        assert 'ttl' in item
    
    def test_put_risk_record_with_ttl(self, dynamodb_client, mock_dynamodb_resource, sample_risk_record):
        """Test that TTL is set for 90-day retention."""
        _, mock_table = mock_dynamodb_resource
        mock_table.put_item.return_value = {'ResponseMetadata': {'HTTPStatusCode': 200}}
        
        before_time = datetime.now(timezone.utc) + timedelta(days=90)
        dynamodb_client.put_risk_record(sample_risk_record)
        after_time = datetime.now(timezone.utc) + timedelta(days=90)
        
        call_args = mock_table.put_item.call_args
        item = call_args.kwargs['Item']
        
        assert 'ttl' in item
        ttl_timestamp = item['ttl']
        assert int(before_time.timestamp()) <= ttl_timestamp <= int(after_time.timestamp())
    
    def test_put_risk_record_converts_floats(self, dynamodb_client, mock_dynamodb_resource, sample_risk_record):
        """Test that float values in signal_values are converted to Decimal."""
        _, mock_table = mock_dynamodb_resource
        mock_table.put_item.return_value = {'ResponseMetadata': {'HTTPStatusCode': 200}}
        
        dynamodb_client.put_risk_record(sample_risk_record)
        
        call_args = mock_table.put_item.call_args
        item = call_args.kwargs['Item']
        
        # Verify signal_values floats are converted to Decimal
        assert isinstance(item['signal_values']['delivery_cadence'], Decimal)
        assert item['signal_values']['delivery_cadence'] == Decimal('75.5')
    
    def test_query_risk_records_all(self, dynamodb_client, mock_dynamodb_resource):
        """Test querying all risk records for a team."""
        _, mock_table = mock_dynamodb_resource
        mock_table.query.return_value = {
            'Items': [
                {'PK': 'TEAM#team-alpha', 'SK': 'RISK#analysis-1#risk-1'},
                {'PK': 'TEAM#team-alpha', 'SK': 'RISK#analysis-2#risk-2'}
            ]
        }
        
        results = dynamodb_client.query_risk_records('team-alpha')
        
        assert len(results) == 2
        mock_table.query.assert_called_once()
    
    def test_query_risk_records_by_analysis(self, dynamodb_client, mock_dynamodb_resource):
        """Test querying risk records for a specific analysis."""
        _, mock_table = mock_dynamodb_resource
        mock_table.query.return_value = {
            'Items': [
                {'PK': 'TEAM#team-alpha', 'SK': 'RISK#analysis-456#risk-1'},
                {'PK': 'TEAM#team-alpha', 'SK': 'RISK#analysis-456#risk-2'}
            ]
        }
        
        results = dynamodb_client.query_risk_records('team-alpha', analysis_id='analysis-456')
        
        assert len(results) == 2
        mock_table.query.assert_called_once()
    
    def test_query_risk_records_with_limit(self, dynamodb_client, mock_dynamodb_resource):
        """Test querying risk records with a limit."""
        _, mock_table = mock_dynamodb_resource
        mock_table.query.return_value = {'Items': []}
        
        dynamodb_client.query_risk_records('team-alpha', limit=5)
        
        call_args = mock_table.query.call_args
        assert call_args.kwargs['Limit'] == 5
    
    def test_get_risk_record_success(self, dynamodb_client, mock_dynamodb_resource):
        """Test getting a specific risk record."""
        _, mock_table = mock_dynamodb_resource
        mock_table.get_item.return_value = {
            'Item': {
                'PK': 'TEAM#team-alpha',
                'SK': 'RISK#analysis-456#risk-123',
                'risk_id': 'risk-123'
            }
        }
        
        result = dynamodb_client.get_risk_record('team-alpha', 'analysis-456', 'risk-123')
        
        assert result is not None
        assert result['risk_id'] == 'risk-123'
        mock_table.get_item.assert_called_once_with(
            Key={
                'PK': 'TEAM#team-alpha',
                'SK': 'RISK#analysis-456#risk-123'
            }
        )
    
    def test_get_risk_record_not_found(self, dynamodb_client, mock_dynamodb_resource):
        """Test getting a non-existent risk record."""
        _, mock_table = mock_dynamodb_resource
        mock_table.get_item.return_value = {}
        
        result = dynamodb_client.get_risk_record('team-alpha', 'analysis-456', 'risk-999')
        
        assert result is None


class TestUtilityMethods:
    """Test utility methods."""
    
    def test_convert_floats_to_decimal_dict(self, dynamodb_client):
        """Test converting floats in a dictionary."""
        data = {
            'value': 75.5,
            'nested': {
                'inner_value': 45.2
            }
        }
        
        result = dynamodb_client._convert_floats_to_decimal(data)
        
        assert isinstance(result['value'], Decimal)
        assert result['value'] == Decimal('75.5')
        assert isinstance(result['nested']['inner_value'], Decimal)
        assert result['nested']['inner_value'] == Decimal('45.2')
    
    def test_convert_floats_to_decimal_list(self, dynamodb_client):
        """Test converting floats in a list."""
        data = [75.5, 45.2, 30.8]
        
        result = dynamodb_client._convert_floats_to_decimal(data)
        
        assert all(isinstance(v, Decimal) for v in result)
        assert result[0] == Decimal('75.5')
    
    def test_convert_floats_to_decimal_mixed(self, dynamodb_client):
        """Test converting mixed types."""
        data = {
            'float_val': 75.5,
            'int_val': 42,
            'str_val': 'test',
            'list_val': [1.5, 2.5],
            'none_val': None
        }
        
        result = dynamodb_client._convert_floats_to_decimal(data)
        
        assert isinstance(result['float_val'], Decimal)
        assert isinstance(result['int_val'], int)
        assert isinstance(result['str_val'], str)
        assert isinstance(result['list_val'][0], Decimal)
        assert result['none_val'] is None
