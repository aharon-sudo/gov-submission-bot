"""Bundle generation orchestrator"""

import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

from ..models.match_result import MatchResult
from ..models.opportunity import OpportunityData
from ..models.bundle import BundleInfo
from .matrix_generator import MatrixGenerator
from .risk_generator import RiskGenerator
from .email_generator import EmailGenerator


class BundleOrchestrator:
    """Coordinate generation of all output files"""

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.matrix_generator = MatrixGenerator()
        self.risk_generator = RiskGenerator()
        self.email_generator = EmailGenerator()

    def generate_bundle(
        self,
        match_result: MatchResult,
        opp_data: OpportunityData,
        output_dir: Path
    ) -> BundleInfo:
        """
        Create full bundle at outputs/<opp_name>/<candidate_name>/

        Args:
            match_result: Match result data
            opp_data: Opportunity data
            output_dir: Base output directory

        Returns:
            BundleInfo with paths and metadata
        """
        # Create safe directory names
        opp_name = self._sanitize_filename(opp_data.title or opp_data.opportunity_id)
        candidate_name = self._sanitize_filename(match_result.candidate_name)

        # Create bundle directory
        bundle_dir = output_dir / opp_name / candidate_name
        bundle_dir.mkdir(parents=True, exist_ok=True)

        self.logger.info(f"Generating bundle at {bundle_dir}")

        # Generate files
        matrix_path = bundle_dir / 'requirements_matrix.md'
        risk_path = bundle_dir / 'risk_flags.md'
        email_path = bundle_dir / 'submission_email.txt'

        # Generate requirements matrix
        matrix_content = self.matrix_generator.generate(match_result)
        with open(matrix_path, 'w') as f:
            f.write(matrix_content)
        self.logger.debug(f"Generated {matrix_path}")

        # Generate risk flags
        risk_content = self.risk_generator.generate(match_result, opp_data)
        with open(risk_path, 'w') as f:
            f.write(risk_content)
        self.logger.debug(f"Generated {risk_path}")

        # Generate submission email
        email_content = self.email_generator.generate(match_result, opp_data)
        with open(email_path, 'w') as f:
            f.write(email_content)
        self.logger.debug(f"Generated {email_path}")

        # Create bundle info
        bundle_info = BundleInfo(
            opportunity_name=opp_name,
            candidate_name=candidate_name,
            output_path=bundle_dir,
            matrix_path=matrix_path,
            risk_path=risk_path,
            email_path=email_path,
            match_percentage=match_result.overall_match_percentage,
            created_at=datetime.now().isoformat()
        )

        self.logger.info(f"Bundle generated successfully: {bundle_info}")

        return bundle_info

    def _sanitize_filename(self, name: str) -> str:
        """Sanitize string for use as directory/filename"""
        # Remove/replace problematic characters
        name = name.replace('/', '-')
        name = name.replace('\\', '-')
        name = name.replace(':', '-')
        name = name.replace('*', '')
        name = name.replace('?', '')
        name = name.replace('"', '')
        name = name.replace('<', '')
        name = name.replace('>', '')
        name = name.replace('|', '')

        # Limit length
        if len(name) > 100:
            name = name[:100]

        # Strip whitespace
        name = name.strip()

        return name
