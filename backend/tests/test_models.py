"""Unit tests for core data models."""

import pytest
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from models import (
    TeamSignal,
    SignalMetadata,
    RiskRecord,
    SeverityLevel,
    AnalysisResult,
    Snapshot,
)


class TestTeamSignal:
    """Tests for TeamSignal model."""
    
    def test_valid_team_signal(self, sample_team_id, sample_signal_metadata):
        """Test creating a valid team signal."""
        signal = TeamSignal(
            team_id=sample_team_id,
            timestamp=datetime.utcnow(),
            delivery_cadence=75.0,
            knowledge_concentration=60.0,
            dependency_risk=45.0,
            workload_distribution=80.0,
            attrition_signal=30.0,
            metadata=sample_signal_metadata,
        )
        
        assert signal.team_id == sample_team_id
        assert 0 <= signal.delivery_cadence <= 100
        assert signal.metadata.team_size == 8
    
    def test_team_signal_rejects_individual_identifiers(self, sample_signal_metadata):
        """Test that team_id with individual identifiers is rejected."""
        with pytest.raises(ValueError, match="individual identifier"):
            TeamSignal(
                team_id="user_john_doe",
                timestamp=datetime.utcnow(),
                delivery_cadence=75.0,
                knowledge_concentration=60.0,
                dependency_risk=45.0,
                workload_distribution=80.0,
                attrition_signal=30.0,
                metadata=sample_signal_metadata,
            )
    
    def test_team_signal_to_dynamodb(self, sample_team_id, sample_signal_metadata):
        """Test conversion to DynamoDB item format."""
        signal = TeamSignal(
            team_id=sample_team_id,
            timestamp=datetime.utcnow(),
            delivery_cadence=75.0,
            knowledge_concentration=60.0,
            dependency_risk=45.0,
            workload_distribution=80.0,
            attrition_signal=30.0,
            metadata=sample_signal_metadata,
        )
        
        item = signal.to_dynamodb_item()
        assert item["PK"] == f"TEAM#{sample_team_id}"
        assert item["SK"].startswith("SIGNAL#")
        assert item["delivery_cadence"] == 75.0


class TestRiskRecord:
    """Tests for RiskRecord model."""
    
    def test_valid_risk_record(self, sample_team_id):
        """Test creating a valid risk record."""
        risk = RiskRecord(
            analysis_id="analysis-123",
            team_id=sample_team_id,
            dimension="delivery_cadence",
            severity=SeverityLevel.HIGH,
            description_en="Delivery cadence is declining",
            description_es="La cadencia de entrega está disminuyendo",
            recommendations_en=["Reduce WIP", "Focus on smaller tasks"],
            recommendations_es=["Reducir WIP", "Enfocarse en tareas más pequeñas"],
            signal_values={
                "delivery_cadence": 45.0,
                "knowledge_concentration": 60.0,
                "dependency_risk": 50.0,
                "workload_distribution": 70.0,
                "attrition_signal": 30.0,
            },
        )
        
        assert risk.severity == SeverityLevel.HIGH
        assert len(risk.recommendations_en) >= 1
        assert len(risk.recommendations_es) >= 1
    
    def test_risk_record_to_dynamodb(self, sample_team_id):
        """Test conversion to DynamoDB item format."""
        risk = RiskRecord(
            analysis_id="analysis-123",
            team_id=sample_team_id,
            dimension="delivery_cadence",
            severity=SeverityLevel.CRITICAL,
            description_en="Critical issue",
            description_es="Problema crítico",
            recommendations_en=["Fix immediately"],
            recommendations_es=["Arreglar inmediatamente"],
            signal_values={},
        )
        
        item = risk.to_dynamodb_item()
        assert item["PK"] == f"TEAM#{sample_team_id}"
        assert item["SK"].startswith("RISK#")
        assert item["severity"] == "critical"


class TestSnapshot:
    """Tests for Snapshot model."""
    
    def test_snapshot_serialization(self, sample_team_id):
        """Test snapshot JSON serialization and deserialization."""
        from models.snapshot import SnapshotRisk, SnapshotMetadata
        
        snapshot = Snapshot(
            team_id=sample_team_id,
            signals={
                "delivery_cadence": 75.0,
                "knowledge_concentration": 60.0,
                "dependency_risk": 45.0,
                "workload_distribution": 80.0,
                "attrition_signal": 30.0,
            },
            risks=[
                SnapshotRisk(
                    risk_id="risk-1",
                    dimension="delivery_cadence",
                    severity="high",
                    description_en="Issue detected",
                    description_es="Problema detectado",
                )
            ],
            metadata=SnapshotMetadata(
                team_size=8,
                project_count=3,
                analysis_duration_ms=5000,
            ),
        )
        
        # Serialize to JSON
        json_str = snapshot.to_json()
        assert sample_team_id in json_str
        
        # Deserialize from JSON
        restored = Snapshot.from_json(json_str)
        assert restored.team_id == snapshot.team_id
        assert restored.signals == snapshot.signals
        assert len(restored.risks) == 1
    
    def test_snapshot_s3_key_generation(self, sample_team_id):
        """Test S3 key generation for snapshots."""
        from models.snapshot import SnapshotMetadata
        
        snapshot = Snapshot(
            team_id=sample_team_id,
            timestamp=datetime(2024, 1, 15, 10, 30, 0),
            signals={},
            risks=[],
            metadata=SnapshotMetadata(
                team_size=8,
                project_count=3,
                analysis_duration_ms=5000,
            ),
        )
        
        key = snapshot.get_s3_key()
        assert key.startswith(f"snapshots/{sample_team_id}/2024/01/15/")
        assert key.endswith(".json")


class TestAnalysisResult:
    """Tests for AnalysisResult model."""
    
    def test_analysis_result_risk_count(self, sample_team_id):
        """Test risk count property."""
        result = AnalysisResult(
            team_id=sample_team_id,
            risks=[
                RiskRecord(
                    analysis_id="analysis-123",
                    team_id=sample_team_id,
                    dimension="delivery_cadence",
                    severity=SeverityLevel.HIGH,
                    description_en="Issue 1",
                    description_es="Problema 1",
                    recommendations_en=["Fix 1"],
                    recommendations_es=["Arreglar 1"],
                    signal_values={},
                ),
                RiskRecord(
                    analysis_id="analysis-123",
                    team_id=sample_team_id,
                    dimension="workload_distribution",
                    severity=SeverityLevel.MEDIUM,
                    description_en="Issue 2",
                    description_es="Problema 2",
                    recommendations_en=["Fix 2"],
                    recommendations_es=["Arreglar 2"],
                    signal_values={},
                ),
            ],
        )
        
        assert result.risk_count == 2
        high_risks = result.get_risks_by_severity("high")
        assert len(high_risks) == 1
