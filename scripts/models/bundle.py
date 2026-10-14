"""Bundle data models"""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class BundleInfo:
    """Information about a generated output bundle"""
    opportunity_name: str
    candidate_name: str
    output_path: Path
    matrix_path: Path
    risk_path: Path
    email_path: Path
    match_percentage: float
    created_at: str

    def __str__(self) -> str:
        """String representation for logging"""
        return f"{self.opportunity_name}/{self.candidate_name} ({self.match_percentage:.1f}% match)"
