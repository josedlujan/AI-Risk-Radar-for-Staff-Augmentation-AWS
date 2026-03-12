"""Integration tests demonstrating S3 client functionality."""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch

from backend.data_access.s3_client import S3Client
from backend.models.snapshot import Snapshot, SnapshotRisk, SnapshotMetadata


def test_snapshot_serialization_and_key_generation():
    """
    Demonstrates snapshot serialization to JSON and timestamp-based key generation.
    Requirements: 5.1, 5.2
    """
    # Create a snapshot
    snapshot = Snapshot(
        snapshot_id="integration-test-123",
        team_id="team-beta",
        timestamp=datetime(2024, 3, 20, 15, 45, 30),
        signals={
            "delivery_cadence": 85.0,
            "knowledge_concentration": 55.0,
            "dependency_risk": 40.0,
            "workload_distribution": 90.0,
            "attrition_signal": 25.0
        },
        risks=[
            SnapshotRisk(
                risk_id="risk-integration-1",
                dimension="delivery_cadence",
                severity="medium",
                description_en="Delivery pace is slightly below target",
                description_es="El ritmo de entrega está ligeramente por debajo del objetivo"
            )
        ],
        metadata=SnapshotMetadata(
            team_size=10,
            project_count=4,
            analysis_duration_ms=2000
        )
    )
    
    # Test JSON serialization
    json_str = snapshot.to_json()
    assert '"snapshot_id": "integration-test-123"' in json_str
    assert '"team_id": "team-beta"' in json_str
    assert '"delivery_cadence": 85.0' in json_str
    assert '"severity": "medium"' in json_str
    
    # Test timestamp-based key generation
    key = snapshot.get_s3_key()
    expected_key = "snapshots/team-beta/2024/03/20/2024-03-20T15:45:30.json"
    assert key == expected_key
    
    print(f"✓ Snapshot serialization successful")
    print(f"✓ Generated S3 key: {key}")


def test_snapshot_round_trip_integrity():
    """
    Demonstrates snapshot storage and retrieval with data integrity.
    Requirements: 5.5
    """
    # Create original snapshot
    original = Snapshot(
        snapshot_id="round-trip-test",
        team_id="team-gamma",
        timestamp=datetime(2024, 2, 10, 9, 15, 0),
        signals={
            "delivery_cadence": 70.0,
            "knowledge_concentration": 80.0,
            "dependency_risk": 65.0,
            "workload_distribution": 75.0,
            "attrition_signal": 50.0
        },
        risks=[
            SnapshotRisk(
                risk_id="risk-rt-1",
                dimension="knowledge_concentration",
                severity="high",
                description_en="High knowledge concentration detected",
                description_es="Alta concentración de conocimiento detectada"
            ),
            SnapshotRisk(
                risk_id="risk-rt-2",
                dimension="attrition_signal",
                severity="medium",
                description_en="Moderate attrition risk",
                description_es="Riesgo moderado de deserción"
            )
        ],
        metadata=SnapshotMetadata(
            team_size=12,
            project_count=5,
            analysis_duration_ms=3500
        )
    )
    
    # Serialize to JSON
    json_str = original.to_json()
    
    # Deserialize from JSON
    restored = Snapshot.from_json(json_str)
    
    # Verify data integrity
    assert restored.snapshot_id == original.snapshot_id
    assert restored.team_id == original.team_id
    assert restored.timestamp == original.timestamp
    assert restored.signals == original.signals
    assert len(restored.risks) == len(original.risks)
    assert restored.risks[0].risk_id == original.risks[0].risk_id
    assert restored.risks[0].severity == original.risks[0].severity
    assert restored.risks[1].description_en == original.risks[1].description_en
    assert restored.metadata.team_size == original.metadata.team_size
    assert restored.metadata.project_count == original.metadata.project_count
    
    print(f"✓ Round-trip integrity verified")
    print(f"✓ Original and restored snapshots match perfectly")


def test_s3_client_storage_and_retrieval():
    """
    Demonstrates complete S3 client workflow: store and retrieve snapshots.
    Requirements: 5.1, 5.2, 5.5
    """
    with patch('backend.data_access.s3_client.boto3.client') as mock_boto:
        # Setup mock S3 client
        mock_s3 = Mock()
        mock_boto.return_value = mock_s3
        
        # Create S3 client
        s3_client = S3Client(bucket_name='test-integration-bucket')
        s3_client.s3_client = mock_s3
        
        # Create snapshot
        snapshot = Snapshot(
            snapshot_id="workflow-test",
            team_id="team-delta",
            timestamp=datetime(2024, 4, 5, 12, 0, 0),
            signals={
                "delivery_cadence": 95.0,
                "knowledge_concentration": 45.0,
                "dependency_risk": 30.0,
                "workload_distribution": 85.0,
                "attrition_signal": 20.0
            },
            risks=[],
            metadata=SnapshotMetadata(
                team_size=6,
                project_count=2,
                analysis_duration_ms=1200
            )
        )
        
        # Mock put_object response
        mock_s3.put_object.return_value = {
            'ETag': '"workflow-etag"',
            'VersionId': 'v1'
        }
        
        # Store snapshot
        put_result = s3_client.put_snapshot(snapshot)
        
        assert put_result['key'] == 'snapshots/team-delta/2024/04/05/2024-04-05T12:00:00.json'
        assert put_result['bucket'] == 'test-integration-bucket'
        print(f"✓ Snapshot stored at: {put_result['key']}")
        
        # Mock get_object response
        json_content = snapshot.to_json()
        mock_body = Mock()
        mock_body.read.return_value = json_content.encode('utf-8')
        mock_s3.get_object.return_value = {'Body': mock_body}
        
        # Retrieve snapshot
        retrieved = s3_client.get_snapshot(put_result['key'])
        
        assert retrieved.snapshot_id == snapshot.snapshot_id
        assert retrieved.team_id == snapshot.team_id
        assert retrieved.signals == snapshot.signals
        print(f"✓ Snapshot retrieved successfully")
        print(f"✓ Complete workflow verified")


def test_timestamp_based_retrieval():
    """
    Demonstrates retrieval by team ID and timestamp.
    Requirements: 5.2, 5.5
    """
    with patch('backend.data_access.s3_client.boto3.client') as mock_boto:
        mock_s3 = Mock()
        mock_boto.return_value = mock_s3
        
        s3_client = S3Client(bucket_name='test-bucket')
        s3_client.s3_client = mock_s3
        
        # Create snapshot with specific timestamp
        snapshot = Snapshot(
            snapshot_id="timestamp-test",
            team_id="team-epsilon",
            timestamp=datetime(2024, 5, 15, 18, 30, 45),
            signals={
                "delivery_cadence": 80.0,
                "knowledge_concentration": 60.0,
                "dependency_risk": 50.0,
                "workload_distribution": 70.0,
                "attrition_signal": 40.0
            },
            risks=[],
            metadata=SnapshotMetadata(
                team_size=8,
                project_count=3,
                analysis_duration_ms=1800
            )
        )
        
        # Mock get_object response
        json_content = snapshot.to_json()
        mock_body = Mock()
        mock_body.read.return_value = json_content.encode('utf-8')
        mock_s3.get_object.return_value = {'Body': mock_body}
        
        # Retrieve by team ID and timestamp
        retrieved = s3_client.get_snapshot_by_team_and_timestamp(
            team_id='team-epsilon',
            timestamp_iso='2024-05-15T18:30:45'
        )
        
        # Verify correct key was constructed
        expected_key = 'snapshots/team-epsilon/2024/05/15/2024-05-15T18:30:45.json'
        mock_s3.get_object.assert_called_once()
        call_args = mock_s3.get_object.call_args
        assert call_args[1]['Key'] == expected_key
        
        assert retrieved.team_id == 'team-epsilon'
        print(f"✓ Timestamp-based retrieval successful")
        print(f"✓ Retrieved snapshot for team-epsilon at 2024-05-15T18:30:45")


if __name__ == '__main__':
    # Run integration tests
    print("\n=== S3 Client Integration Tests ===\n")
    
    print("Test 1: Snapshot Serialization and Key Generation")
    test_snapshot_serialization_and_key_generation()
    
    print("\nTest 2: Snapshot Round-Trip Integrity")
    test_snapshot_round_trip_integrity()
    
    print("\nTest 3: S3 Client Storage and Retrieval")
    test_s3_client_storage_and_retrieval()
    
    print("\nTest 4: Timestamp-Based Retrieval")
    test_timestamp_based_retrieval()
    
    print("\n=== All Integration Tests Passed ===\n")
