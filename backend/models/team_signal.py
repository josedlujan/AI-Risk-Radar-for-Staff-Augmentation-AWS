"""TeamSignal data model for aggregated team-level metrics."""

from datetime import datetime
from typing import Dict, Any
from pydantic import BaseModel, Field, field_validator


class SignalMetadata(BaseModel):
    """Metadata about team signal aggregation."""
    
    team_size: int = Field(gt=0, description="Number of engineers in the team")
    project_count: int = Field(gt=0, description="Number of projects the team works on")
    aggregation_period: str = Field(description="Time period for aggregation (e.g., 'weekly', 'daily')")


class TeamSignal(BaseModel):
    """Aggregated team-level signal data across five risk dimensions."""
    
    team_id: str = Field(description="Team identifier")
    timestamp: datetime = Field(description="Signal timestamp")
    delivery_cadence: float = Field(ge=0, le=100, description="Delivery cadence score (0-100)")
    knowledge_concentration: float = Field(ge=0, le=100, description="Knowledge concentration score (0-100)")
    dependency_risk: float = Field(ge=0, le=100, description="Dependency risk score (0-100)")
    workload_distribution: float = Field(ge=0, le=100, description="Workload distribution score (0-100)")
    attrition_signal: float = Field(ge=0, le=100, description="Attrition signal score (0-100)")
    metadata: SignalMetadata = Field(description="Aggregation metadata")
    
    @field_validator('team_id')
    @classmethod
    def validate_team_id(cls, v: str) -> str:
        """Ensure team_id doesn't contain individual identifiers."""
        if not v or not v.strip():
            raise ValueError("team_id cannot be empty")
        # Check for common individual identifier patterns
        individual_patterns = ['user_', 'engineer_', 'employee_', '@', 'email']
        v_lower = v.lower()
        for pattern in individual_patterns:
            if pattern in v_lower:
                raise ValueError(f"team_id contains individual identifier pattern: {pattern}")
        return v
    
    def to_dynamodb_item(self) -> Dict[str, Any]:
        """Convert to DynamoDB item format."""
        return {
            "PK": f"TEAM#{self.team_id}",
            "SK": f"SIGNAL#{self.timestamp.isoformat()}",
            "team_id": self.team_id,
            "timestamp": self.timestamp.isoformat(),
            "delivery_cadence": self.delivery_cadence,
            "knowledge_concentration": self.knowledge_concentration,
            "dependency_risk": self.dependency_risk,
            "workload_distribution": self.workload_distribution,
            "attrition_signal": self.attrition_signal,
            "metadata": {
                "team_size": self.metadata.team_size,
                "project_count": self.metadata.project_count,
                "aggregation_period": self.metadata.aggregation_period,
            }
        }
