from dataclasses import dataclass, field
from typing import Optional, Dict, Any

@dataclass
class Finding:
    """
    Standardized data model for all rule-based findings in the FDSS.
    Corresponds to the structure: Evidence / Metric -> Finding -> Interpretation -> Recommendation -> Severity -> Confidence
    """
    module: str
    finding: str
    interpretation: str
    recommendation: str
    severity: str  # Critical, High, Medium, Low, Positive
    confidence: float
    year: str
    metric_value: Optional[float] = None
    threshold_value: Optional[float] = None
    priority_score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Converts the Finding dataclass instance into a dictionary for JSON serialization."""
        return {
            "module": self.module,
            "finding": self.finding,
            "interpretation": self.interpretation,
            "recommendation": self.recommendation,
            "severity": self.severity,
            "confidence": self.confidence,
            "year": self.year,
            "metric_value": self.metric_value,
            "threshold_value": self.threshold_value,
            "priority_score": self.priority_score
        }