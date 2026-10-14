"""Generate requirements matrix markdown"""

from typing import List
from ..models.match_result import MatchResult, RequirementMatch


class MatrixGenerator:
    """Generate requirements matrix markdown"""

    def generate(self, match_result: MatchResult) -> str:
        """
        Create requirements_matrix.md with table

        Args:
            match_result: Match result data

        Returns:
            Markdown content
        """
        lines = []

        # Header
        lines.append(f"# Requirements Matrix: {match_result.candidate_name}")
        lines.append("")
        lines.append(f"**Opportunity:** {match_result.opportunity_id}")
        lines.append(f"**Overall Match:** {match_result.overall_match_percentage:.1f}%")
        lines.append("")

        # Summary stats
        required_matches = match_result.get_required_matches()
        preferred_matches = match_result.get_preferred_matches()

        lines.append("## Summary")
        lines.append("")
        lines.append(f"- **Required Qualifications:** {self._count_met(required_matches)}/{len(required_matches)} met")
        lines.append(f"- **Preferred Qualifications:** {self._count_met(preferred_matches)}/{len(preferred_matches)} met")
        lines.append(f"- **Critical Gaps:** {len(match_result.critical_gaps)}")
        lines.append("")

        # Required qualifications table
        if required_matches:
            lines.append("## Required Qualifications")
            lines.append("")
            lines.extend(self._generate_table(required_matches))
            lines.append("")

        # Preferred qualifications table
        if preferred_matches:
            lines.append("## Preferred Qualifications")
            lines.append("")
            lines.extend(self._generate_table(preferred_matches))
            lines.append("")

        return '\n'.join(lines)

    def _generate_table(self, matches: List[RequirementMatch]) -> List[str]:
        """Generate markdown table for matches"""
        lines = []

        # Table header
        lines.append("| ID | Requirement | Status | Evidence | Years | Confidence |")
        lines.append("|----|-------------|--------|----------|-------|------------|")

        # Table rows
        for match in matches:
            status_icon = self._get_status_icon(match.status)
            requirement_text = match.requirement_text[:60] + "..." if len(match.requirement_text) > 60 else match.requirement_text

            # Format evidence
            if match.evidence_snippets:
                evidence = match.evidence_snippets[0][:60] + "..." if match.evidence_snippets else "-"
            else:
                evidence = "-"

            # Format years
            years = f"{match.years_calculated:.1f}" if match.years_calculated is not None else "-"

            # Format confidence
            confidence = f"{match.confidence:.2f}"

            lines.append(
                f"| {match.requirement_id} | {requirement_text} | {status_icon} | {evidence} | {years} | {confidence} |"
            )

        return lines

    def _get_status_icon(self, status: str) -> str:
        """Get emoji icon for status"""
        if status == "meets":
            return "✅ Meets"
        elif status == "partial":
            return "⚠️ Partial"
        else:
            return "❌ Not Evidenced"

    def _count_met(self, matches: List[RequirementMatch]) -> int:
        """Count fully met requirements"""
        return sum(1 for m in matches if m.is_met())
