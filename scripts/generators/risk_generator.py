"""Generate risk flags markdown"""

from typing import List
from ..models.match_result import MatchResult, RequirementMatch
from ..models.opportunity import OpportunityData


class RiskGenerator:
    """Generate risk flags markdown"""

    def generate(self, match_result: MatchResult, opp_data: OpportunityData) -> str:
        """
        Create risk_flags.md

        Args:
            match_result: Match result data
            opp_data: Opportunity data

        Returns:
            Markdown content
        """
        lines = []

        # Header
        lines.append(f"# Risk Assessment: {match_result.candidate_name}")
        lines.append("")
        lines.append(f"**Opportunity:** {opp_data.title}")
        lines.append(f"**Opportunity ID:** {match_result.opportunity_id}")
        lines.append("")

        # Critical gaps (unmet required qualifications)
        critical_gaps = self._get_critical_gaps(match_result)
        if critical_gaps:
            lines.append("## ⚠️ Critical Gaps (Required Qualifications)")
            lines.append("")
            for match in critical_gaps:
                lines.append(f"- **{match.requirement_id}:** {match.requirement_text}")
                if match.status == "partial":
                    lines.append(f"  - Status: ⚠️ Partial evidence only")
                else:
                    lines.append(f"  - Status: ❌ No evidence in resume")
                if match.reasoning:
                    lines.append(f"  - Note: {match.reasoning}")
            lines.append("")
        else:
            lines.append("## ✅ No Critical Gaps")
            lines.append("")
            lines.append("All required qualifications are met.")
            lines.append("")

        # Missing preferred qualifications
        missing_preferred = self._get_missing_preferred(match_result)
        if missing_preferred:
            lines.append("## Missing Preferred Qualifications")
            lines.append("")
            for match in missing_preferred:
                lines.append(f"- **{match.requirement_id}:** {match.requirement_text}")
            lines.append("")

        # Low confidence matches
        low_confidence = match_result.get_low_confidence_matches(threshold=0.6)
        if low_confidence:
            lines.append("## ⚠️ Confidence Concerns (Low Confidence Matches)")
            lines.append("")
            for match in low_confidence:
                lines.append(f"- **{match.requirement_id}:** {match.requirement_text}")
                lines.append(f"  - Status: {match.status}")
                lines.append(f"  - Confidence: {match.confidence:.2f}")
                lines.append(f"  - Reasoning: {match.reasoning}")
            lines.append("")

        # Strengths
        strengths = self._get_strengths(match_result)
        if strengths:
            lines.append("## ✅ Strengths")
            lines.append("")
            for match in strengths[:5]:  # Top 5 strengths
                lines.append(f"- **{match.requirement_id}:** {match.requirement_text}")
                if match.evidence_snippets:
                    lines.append(f"  - Evidence: \"{match.evidence_snippets[0][:100]}...\"")
                if match.years_calculated:
                    lines.append(f"  - Years: {match.years_calculated:.1f}")
            lines.append("")

        # Overall risk level
        risk_level = self._calculate_risk_level(match_result)
        lines.append(f"## Overall Risk Level: {risk_level}")
        lines.append("")
        lines.append(self._get_recommendation(match_result, critical_gaps, low_confidence))
        lines.append("")

        return '\n'.join(lines)

    def _get_critical_gaps(self, match_result: MatchResult) -> List[RequirementMatch]:
        """Get unmet or partially met required qualifications"""
        return [
            m for m in match_result.get_required_matches()
            if m.status in ["partial", "not_evidenced"]
        ]

    def _get_missing_preferred(self, match_result: MatchResult) -> List[RequirementMatch]:
        """Get unmet preferred qualifications"""
        return [
            m for m in match_result.get_preferred_matches()
            if m.status == "not_evidenced"
        ]

    def _get_strengths(self, match_result: MatchResult) -> List[RequirementMatch]:
        """Get strongest matches (high confidence, fully met)"""
        strengths = [
            m for m in match_result.match_results
            if m.is_met() and m.confidence >= 0.8
        ]
        # Sort by confidence descending
        return sorted(strengths, key=lambda m: m.confidence, reverse=True)

    def _calculate_risk_level(self, match_result: MatchResult) -> str:
        """Calculate overall risk level"""
        critical_gaps = self._get_critical_gaps(match_result)
        low_confidence = match_result.get_low_confidence_matches()

        if len(critical_gaps) >= 3:
            return "HIGH"
        elif len(critical_gaps) >= 1 or len(low_confidence) >= 3:
            return "MEDIUM"
        else:
            return "LOW"

    def _get_recommendation(
        self,
        match_result: MatchResult,
        critical_gaps: List[RequirementMatch],
        low_confidence: List[RequirementMatch]
    ) -> str:
        """Generate recommendation based on gaps"""
        if not critical_gaps and not low_confidence:
            return "**Recommendation:** Strong candidate. Proceed with submission."

        recommendations = []
        if critical_gaps:
            gap_ids = [g.requirement_id for g in critical_gaps[:3]]
            recommendations.append(f"Review and address critical gaps ({', '.join(gap_ids)})")

        if low_confidence:
            recommendations.append("Verify low-confidence matches with additional documentation")

        return "**Recommendation:** " + ". ".join(recommendations) + "."
