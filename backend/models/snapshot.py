"""Snapshot data model for historical team metrics."""

from datetime import datetime
from typing import Dict, List, Any
from pydantic import BaseModel, Field
import uuid
import json


class SnapshotRisk(BaseModel):
    """Simplified risk data for snapshot storage."""
    
    risk_id: str
    dimension: str
    severity: str
    description_en: str
    description_es: str


class SnapshotMetadata(BaseModel):
    """Metadata about the snapshot."""
    
    team_size: int
    project_count: int
    analysis_duration_ms: int


class Snapshot(BaseModel):
    """Historical snapshot of team metrics and risks."""
    
    snapshot_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Snapshot identifier")
    team_id: str = Field(description="Team identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Snapshot timestamp")
    signals: Dict[str, float] = Field(description="Signal values for all five dimensions")
    risks: List[SnapshotRisk] = Field(default_factory=list, description="Detected risks")
    metadata: SnapshotMetadata = Field(description="Snapshot metadata")
    
    def to_json(self) -> str:
        """Serialize snapshot to JSON string."""
        data = {
            "snapshot_id": self.snapshot_id,
            "team_id": self.team_id,
            "timestamp": self.timestamp.isoformat(),
            "signals": self.signals,
            "risks": [
                {
                    "risk_id": risk.risk_id,
                    "dimension": risk.dimension,
                    "severity": risk.severity,
                    "description_en": risk.description_en,
                    "description_es": risk.description_es,
                }
                for risk in self.risks
            ],
            "metadata": {
                "team_size": self.metadata.team_size,
                "project_count": self.metadata.project_count,
                "analysis_duration_ms": self.metadata.analysis_duration_ms,
            }
        }
        return json.dumps(data, indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> "Snapshot":
        """Deserialize snapshot from JSON string."""
        data = json.loads(json_str)
        return cls(
            snapshot_id=data["snapshot_id"],
            team_id=data["team_id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            signals=data["signals"],
            risks=[SnapshotRisk(**risk) for risk in data["risks"]],
            metadata=SnapshotMetadata(**data["metadata"]),
        )
    
    def get_s3_key(self) -> str:
        """Generate S3 key for this snapshot."""
        dt = self.timestamp
        return f"snapshots/{self.team_id}/{dt.year}/{dt.month:02d}/{dt.day:02d}/{self.timestamp.isoformat()}.json"
