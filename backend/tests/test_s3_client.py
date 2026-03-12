"""Unit tests for S3 client."""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from botocore.exceptions import ClientError

from backend.data_access.s3_client import S3Client
from backend.models.snapshot import Snapshot, SnapshotRisk, SnapshotMetadata


@pytest.fixture
def s3_client():
    """Create S3Client instance with mocked boto3 client."""
    with patch('backend.data_access.s3_client.boto3.client') as mock_boto:
        mock_s3 = Mock()
        mock_boto.return_value = mock_s3
        
        client = S3Client(bucket_name='test-bucket', region_name='us-east-1')
        client.s3_client = mock_s3
        
        yield client


@pytest.fixture
def sample_snapshot():
    """Create a sample snapshot for testing."""
    return Snapshot(
        snapshot_id="test-snapshot-123",
        team_id="team-alpha",
        timestamp=datetime(2024, 1, 15, 10, 30, 0),
        signals={
            "delivery_cadence": 75.0,
            "knowledge_concentration": 60.0,
            "dependency_risk": 45.0,
            "workload_distribution": 80.0,
            "attrition_signal": 30.0
        },
        risks=[
            SnapshotRisk(
                risk_id="risk-1",
                dimension="knowledge_concentration",
                severity="high",
                description_en="Knowledge concentrated in few team members",
                description_es="Conocimiento concentrado en pocos miembros del equipo"
            )
        ],
        metadata=SnapshotMetadata(
            team_size=8,
            project_count=3,
            analysis_duration_ms=1500
        )
    )


class TestS3ClientPutSnapshot:
    """Tests for put_snapshot method."""
    
    def test_put_snapshot_success(self, s3_client, sample_snapshot):
        """Test successful snapshot storage."""
        # Mock S3 response
        s3_client.s3_client.put_object.return_value = {
            'ETag': '"abc123"',
            'VersionId': 'v1'
        }
        
        result = s3_client.put_snapshot(sample_snapshot)
        
        # Verify S3 was called correctly
        s3_client.s3_client.put_object.assert_called_once()
        call_args = s3_client.s3_client.put_object.call_args
        
        assert call_args[1]['Bucket'] == 'test-bucket'
        assert call_args[1]['Key'] == 'snapshots/team-alpha/2024/01/15/2024-01-15T10:30:00.json'
        assert call_args[1]['ContentType'] == 'application/json'
        assert isinstance(call_args[1]['Body'], bytes)
        
        # Verify response
        assert result['key'] == 'snapshots/team-alpha/2024/01/15/2024-01-15T10:30:00.json'
        assert result['bucket'] == 'test-bucket'
        assert result['etag'] == '"abc123"'
        assert result['version_id'] == 'v1'
    
    def test_put_snapshot_generates_correct_key(self, s3_client, sample_snapshot):
        """Test that timestamp-based key generation is correct."""
        s3_client.s3_client.put_object.return_value = {'ETag': '"test"'}
        
        result = s3_client.put_snapshot(sample_snapshot)
        
        # Verify key format: snapshots/{team_id}/{year}/{month}/{day}/{timestamp}.json
        expected_key = 'snapshots/team-alpha/2024/01/15/2024-01-15T10:30:00.json'
        assert result['key'] == expected_key
    
    def test_put_snapshot_serializes_to_json(self, s3_client, sample_snapshot):
        """Test that snapshot is properly serialized to JSON."""
        s3_client.s3_client.put_object.return_value = {'ETag': '"test"'}
        
        s3_client.put_snapshot(sample_snapshot)
        
        call_args = s3_client.s3_client.put_object.call_args
        body = call_args[1]['Body'].decode('utf-8')
        
        # Verify JSON contains expected fields
        assert '"snapshot_id": "test-snapshot-123"' in body
        assert '"team_id": "team-alpha"' in body
        assert '"delivery_cadence": 75.0' in body
        assert '"knowledge_concentration": 60.0' in body
    
    def test_put_snapshot_failure(self, s3_client, sample_snapshot):
        """Test handling of S3 put failure."""
        # Mock S3 error
        s3_client.s3_client.put_object.side_effect = ClientError(
            error_response={
                'Error': {
                    'Code': 'AccessDenied',
                    'Message': 'Access denied'
                }
            },
            operation_name='PutObject'
        )
        
        with pytest.raises(ClientError) as exc_info:
            s3_client.put_snapshot(sample_snapshot)
        
        assert 'Failed to store snapshot' in str(exc_info.value)


class TestS3ClientGetSnapshot:
    """Tests for get_snapshot method."""
    
    def test_get_snapshot_success(self, s3_client, sample_snapshot):
        """Test successful snapshot retrieval."""
        # Mock S3 response with JSON content
        json_content = sample_snapshot.to_json()
        mock_body = Mock()
        mock_body.read.return_value = json_content.encode('utf-8')
        
        s3_client.s3_client.get_object.return_value = {
            'Body': mock_body
        }
        
        key = 'snapshots/team-alpha/2024/01/15/2024-01-15T10:30:00.json'
        result = s3_client.get_snapshot(key)
        
        # Verify S3 was called correctly
        s3_client.s3_client.get_object.assert_called_once_with(
            Bucket='test-bucket',
            Key=key
        )
        
        # Verify snapshot was parsed correctly
        assert result.snapshot_id == sample_snapshot.snapshot_id
        assert result.team_id == sample_snapshot.team_id
        assert result.signals == sample_snapshot.signals
        assert len(result.risks) == 1
        assert result.risks[0].risk_id == "risk-1"
    
    def test_get_snapshot_not_found(self, s3_client):
        """Test handling of non-existent snapshot."""
        # Mock S3 NoSuchKey error
        s3_client.s3_client.get_object.side_effect = ClientError(
            error_response={
                'Error': {
                    'Code': 'NoSuchKey',
                    'Message': 'The specified key does not exist'
                }
            },
            operation_name='GetObject'
        )
        
        with pytest.raises(ClientError) as exc_info:
            s3_client.get_snapshot('snapshots/team-alpha/2024/01/15/nonexistent.json')
        
        assert exc_info.value.response['Error']['Code'] == 'NoSuchKey'
        assert 'Snapshot not found' in exc_info.value.response['Error']['Message']
    
    def test_get_snapshot_other_error(self, s3_client):
        """Test handling of other S3 errors."""
        # Mock S3 error
        s3_client.s3_client.get_object.side_effect = ClientError(
            error_response={
                'Error': {
                    'Code': 'InternalError',
                    'Message': 'Internal server error'
                }
            },
            operation_name='GetObject'
        )
        
        with pytest.raises(ClientError) as exc_info:
            s3_client.get_snapshot('snapshots/team-alpha/2024/01/15/test.json')
        
        assert 'Failed to retrieve snapshot' in str(exc_info.value)
    
    def test_get_snapshot_round_trip(self, s3_client, sample_snapshot):
        """Test that storing and retrieving a snapshot preserves data."""
        # Store snapshot
        s3_client.s3_client.put_object.return_value = {'ETag': '"test"'}
        put_result = s3_client.put_snapshot(sample_snapshot)
        
        # Mock retrieval
        json_content = sample_snapshot.to_json()
        mock_body = Mock()
        mock_body.read.return_value = json_content.encode('utf-8')
        s3_client.s3_client.get_object.return_value = {'Body': mock_body}
        
        # Retrieve snapshot
        retrieved = s3_client.get_snapshot(put_result['key'])
        
        # Verify data integrity
        assert retrieved.snapshot_id == sample_snapshot.snapshot_id
        assert retrieved.team_id == sample_snapshot.team_id
        assert retrieved.timestamp == sample_snapshot.timestamp
        assert retrieved.signals == sample_snapshot.signals
        assert len(retrieved.risks) == len(sample_snapshot.risks)
        assert retrieved.metadata.team_size == sample_snapshot.metadata.team_size


class TestS3ClientGetSnapshotByTeamAndTimestamp:
    """Tests for get_snapshot_by_team_and_timestamp method."""
    
    def test_get_snapshot_by_team_and_timestamp(self, s3_client, sample_snapshot):
        """Test retrieval by team ID and timestamp."""
        json_content = sample_snapshot.to_json()
        mock_body = Mock()
        mock_body.read.return_value = json_content.encode('utf-8')
        s3_client.s3_client.get_object.return_value = {'Body': mock_body}
        
        result = s3_client.get_snapshot_by_team_and_timestamp(
            team_id='team-alpha',
            timestamp_iso='2024-01-15T10:30:00'
        )
        
        # Verify correct key was constructed
        expected_key = 'snapshots/team-alpha/2024/01/15/2024-01-15T10:30:00.json'
        s3_client.s3_client.get_object.assert_called_once_with(
            Bucket='test-bucket',
            Key=expected_key
        )
        
        assert result.team_id == 'team-alpha'


class TestS3ClientListSnapshots:
    """Tests for list_snapshots method."""
    
    def test_list_snapshots_success(self, s3_client):
        """Test successful snapshot listing."""
        # Mock S3 response
        s3_client.s3_client.list_objects_v2.return_value = {
            'Contents': [
                {
                    'Key': 'snapshots/team-alpha/2024/01/15/2024-01-15T10:30:00.json',
                    'Size': 1024,
                    'LastModified': datetime(2024, 1, 15, 10, 30, 0)
                },
                {
                    'Key': 'snapshots/team-alpha/2024/01/15/2024-01-15T14:00:00.json',
                    'Size': 2048,
                    'LastModified': datetime(2024, 1, 15, 14, 0, 0)
                }
            ]
        }
        
        result = s3_client.list_snapshots(team_id='team-alpha')
        
        # Verify S3 was called correctly
        s3_client.s3_client.list_objects_v2.assert_called_once_with(
            Bucket='test-bucket',
            Prefix='snapshots/team-alpha/',
            MaxKeys=1000
        )
        
        # Verify results
        assert len(result) == 2
        assert result[0]['key'] == 'snapshots/team-alpha/2024/01/15/2024-01-15T10:30:00.json'
        assert result[0]['size'] == 1024
        assert result[1]['size'] == 2048
    
    def test_list_snapshots_with_prefix(self, s3_client):
        """Test snapshot listing with additional prefix."""
        s3_client.s3_client.list_objects_v2.return_value = {'Contents': []}
        
        s3_client.list_snapshots(team_id='team-alpha', prefix='2024/01')
        
        # Verify prefix was constructed correctly
        s3_client.s3_client.list_objects_v2.assert_called_once_with(
            Bucket='test-bucket',
            Prefix='snapshots/team-alpha/2024/01',
            MaxKeys=1000
        )
    
    def test_list_snapshots_empty(self, s3_client):
        """Test listing when no snapshots exist."""
        # Mock empty response
        s3_client.s3_client.list_objects_v2.return_value = {}
        
        result = s3_client.list_snapshots(team_id='team-alpha')
        
        assert result == []
    
    def test_list_snapshots_failure(self, s3_client):
        """Test handling of S3 list failure."""
        s3_client.s3_client.list_objects_v2.side_effect = ClientError(
            error_response={
                'Error': {
                    'Code': 'AccessDenied',
                    'Message': 'Access denied'
                }
            },
            operation_name='ListObjectsV2'
        )
        
        with pytest.raises(ClientError) as exc_info:
            s3_client.list_snapshots(team_id='team-alpha')
        
        assert 'Failed to list snapshots' in str(exc_info.value)


class TestS3ClientDeleteSnapshot:
    """Tests for delete_snapshot method."""
    
    def test_delete_snapshot_success(self, s3_client):
        """Test successful snapshot deletion."""
        s3_client.s3_client.delete_object.return_value = {}
        
        key = 'snapshots/team-alpha/2024/01/15/2024-01-15T10:30:00.json'
        result = s3_client.delete_snapshot(key)
        
        # Verify S3 was called correctly
        s3_client.s3_client.delete_object.assert_called_once_with(
            Bucket='test-bucket',
            Key=key
        )
        
        # Verify response
        assert result['key'] == key
        assert result['bucket'] == 'test-bucket'
        assert result['deleted'] is True
    
    def test_delete_snapshot_failure(self, s3_client):
        """Test handling of S3 delete failure."""
        s3_client.s3_client.delete_object.side_effect = ClientError(
            error_response={
                'Error': {
                    'Code': 'AccessDenied',
                    'Message': 'Access denied'
                }
            },
            operation_name='DeleteObject'
        )
        
        with pytest.raises(ClientError) as exc_info:
            s3_client.delete_snapshot('snapshots/team-alpha/2024/01/15/test.json')
        
        assert 'Failed to delete snapshot' in str(exc_info.value)


class TestS3ClientInitialization:
    """Tests for S3Client initialization."""
    
    def test_init_with_custom_bucket(self):
        """Test initialization with custom bucket name."""
        with patch('backend.data_access.s3_client.boto3.client'):
            client = S3Client(bucket_name='custom-bucket', region_name='us-west-2')
            
            assert client.bucket_name == 'custom-bucket'
    
    def test_init_with_env_var(self):
        """Test initialization with environment variable."""
        with patch('backend.data_access.s3_client.boto3.client'), \
             patch.dict('os.environ', {'SNAPSHOTS_BUCKET': 'env-bucket'}):
            client = S3Client(region_name='us-east-1')
            
            assert client.bucket_name == 'env-bucket'
    
    def test_init_default_bucket(self):
        """Test initialization with default bucket name."""
        with patch('backend.data_access.s3_client.boto3.client'), \
             patch.dict('os.environ', {}, clear=True):
            client = S3Client(region_name='us-east-1')
            
            assert client.bucket_name == 'team-risk-snapshots'
