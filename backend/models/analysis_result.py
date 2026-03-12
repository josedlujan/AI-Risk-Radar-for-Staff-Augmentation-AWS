"""AnalysisResult data model for AI analysis output."""

from typing import List
from pydantic import BaseModel, Field
import uuid

from .risk_record import RiskRecord


class AnalysisResult(BaseModel):
    """Result of AI-powered risk analysis."""
    
    analysis_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Analysis session identifier")
    team_id: str = Field(description="Team identifier")
    risks: List[RiskRecord] = Field(default_factory=list, description="Identified risks")
    analysis_duration_ms: int = Field(default=0, description="Analysis duration in milliseconds")
    
    @property
    def risk_count(self) -> int:
        """Number of risks detected."""
        return len(self.risks)
    
    def get_risks_by_severity(self, severity: str) -> List[RiskRecord]:
        """Get risks filtered by severity level."""
        return [risk for risk in self.risks if risk.severity.value == severity]
