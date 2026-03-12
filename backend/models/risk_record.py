"""RiskRecord data model for identified risks."""

from datetime import datetime
from enum import Enum
from typing import List, Dict, Any
from pydantic import BaseModel, Field
import uuid


class SeverityLevel(str, Enum):
    """Risk severity classification."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RiskRecord(BaseModel):
    """Record of an identified risk with bilingual recommendations."""
    
    risk_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique risk identifier")
    analysis_id: str = Field(description="Analysis session identifier")
    team_id: str = Field(description="Team identifier")
    dimension: str = Field(description="Risk dimension name")
    severity: SeverityLevel = Field(description="Risk severity level")
    detected_at: datetime = Field(default_factory=datetime.utcnow, description="Detection timestamp")
    description_en: str = Field(description="Risk description in English")
    description_es: str = Field(description="Risk description in Spanish")
    recommendations_en: List[str] = Field(description="Recommendations in English")
    recommendations_es: List[str] = Field(description="Recommendations in Spanish")
    signal_values: Dict[str, float] = Field(description="Signal values at time of detection")
    
    def to_dynamodb_item(self) -> Dict[str, Any]:
        """Convert to DynamoDB item format."""
        return {
            "PK": f"TEAM#{self.team_id}",
            "SK": f"RISK#{self.analysis_id}#{self.risk_id}",
            "risk_id": self.risk_id,
            "analysis_id": self.analysis_id,
            "team_id": self.team_id,
            "dimension": self.dimension,
            "severity": self.severity.value,
            "detected_at": self.detected_at.isoformat(),
            "description_en": self.description_en,
            "description_es": self.description_es,
            "recommendations_en": self.recommendations_en,
            "recommendations_es": self.recommendations_es,
            "signal_values": self.signal_values,
        }
