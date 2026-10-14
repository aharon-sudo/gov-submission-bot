"""Match result data models"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class RequirementMatch:
    """Match result for a single requirement"""
    requirement_id: str
    requirement_text: str
    status: str  # "meets" | "partial" | "not_evidenced"
    evidence_snippets: List[str]
    roles_used: List[str]
    years_calculated: Optional[float]
    confidence: float
    reasoning: str

    def is_met(self) -> bool:
        """Check if requirement is fully met"""
        return self.status == "meets"

    def is_partial(self) -> bool:
        """Check if requirement is partially met"""
        return self.status == "partial"

    def has_evidence(self) -> bool:
        """Check if there's any evidence"""
        return bool(self.evidence_snippets)


@dataclass
class MatchResult:
    """Complete match result for a resume against an opportunity"""
    candidate_name: str
    resume_file: str
    opportunity_id: str
    match_results: List[RequirementMatch]
    overall_match_percentage: float
    critical_gaps: List[str]

    def get_required_matches(self) -> List[RequirementMatch]:
        """Get matches for required qualifications"""
        return [m for m in self.match_results if m.requirement_id.startswith('REQ-')]

    def get_preferred_matches(self) -> List[RequirementMatch]:
        """Get matches for preferred qualifications"""
        return [m for m in self.match_results if m.requirement_id.startswith('PREF-')]

    def get_met_count(self) -> int:
        """Count fully met requirements"""
        return sum(1 for m in self.match_results if m.is_met())

    def get_partial_count(self) -> int:
        """Count partially met requirements"""
        return sum(1 for m in self.match_results if m.is_partial())

    def get_unmet_count(self) -> int:
        """Count unmet requirements"""
        return sum(1 for m in self.match_results if not m.has_evidence())

    def get_low_confidence_matches(self, threshold: float = 0.6) -> List[RequirementMatch]:
        """Get matches with low confidence scores"""
        return [m for m in self.match_results if m.confidence < threshold and m.has_evidence()]
