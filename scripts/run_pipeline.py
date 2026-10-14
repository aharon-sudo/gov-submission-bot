#!/usr/bin/env python3
"""
Government Submission Bot - Main Pipeline
Orchestrates document extraction, parsing, matching, and output generation.
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import List, Tuple

from .config import Config, ConfigurationError
from .logger import setup_logger, log_step_start, log_step_complete
from .extractors.factory import ExtractorFactory, UnsupportedFileTypeError
from .parsers.opportunity_parser import OpportunityParser
from .matchers.resume_matcher import ResumeMatcher
from .generators.bundle_orchestrator import BundleOrchestrator
from .notifiers.slack_notifier import SlackNotifier
from .models.opportunity import OpportunityData
from .models.resume import Resume
from .models.match_result import MatchResult
from .models.bundle import BundleInfo

import re
from pathlib import Path

def safe_slug(s: str, max_len: int = 60) -> str:
    s = (s or "").strip().replace("\n", " ").replace("\r", " ")
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"[^a-zA-Z0-9._ -]+", "", s)
    s = s.strip().replace(" ", "_")
    return (s[:max_len] or "unknown")

class PipelineOrchestrator:
    """Main pipeline orchestrator"""

    def __init__(self):
        try:
            self.config = Config.load()
            self.logger = setup_logger(__name__)
            self.client = self.config.get_anthropic_client()
            self.errors = []

            self.logger.info("Pipeline initialized")
            self.logger.info(f"Project root: {self.config.project_root}")

        except ConfigurationError as e:
            print(f"Configuration error: {e}", file=sys.stderr)
            sys.exit(1)

    def run(self) -> int:
        """
        Execute full pipeline:
        1. Discover files
        2. Extract text
        3. Parse opportunities
        4. Match resumes
        5. Generate bundles
        6. Send notification

        Returns:
            Exit code (0 = success, 1 = errors occurred)
        """
        start_time = datetime.now()

        try:
            # Step 1: Discover files
            log_step_start(self.logger, "File Discovery")
            step_start = datetime.now()

            opp_files = self._discover_opportunity_files()
            resume_files = self._discover_resume_files()

            self.logger.info(f"Found {len(opp_files)} opportunities, {len(resume_files)} resumes")
            log_step_complete(self.logger, "File Discovery", (datetime.now() - step_start).total_seconds())

            if not opp_files:
                self.logger.error("No opportunity files found in inbox/")
                return 1
            if not resume_files:
                self.logger.error("No resume files found in resumes/")
                return 1

            # Step 2: Extract text from opportunities
            log_step_start(self.logger, "Opportunity Text Extraction")
            step_start = datetime.now()

            opp_texts = self._extract_documents(opp_files)
            log_step_complete(
                self.logger,
                "Opportunity Text Extraction",
                (datetime.now() - step_start).total_seconds()
            )

            if not opp_texts:
                self.logger.error("No opportunity texts extracted successfully")
                return 1

            # Step 3: Parse opportunities
            log_step_start(self.logger, "Opportunity Parsing")
            step_start = datetime.now()

            parser = OpportunityParser(self.client, self.config, self.logger)
            opportunities = self._parse_opportunities(parser, opp_texts)

            log_step_complete(
                self.logger,
                "Opportunity Parsing",
                (datetime.now() - step_start).total_seconds()
            )

            if not opportunities:
                self.logger.error("No opportunities parsed successfully")
                return 1

            # Step 4: Extract text from resumes
            log_step_start(self.logger, "Resume Text Extraction")
            step_start = datetime.now()

            resumes = self._extract_resumes(resume_files)

            log_step_complete(
                self.logger,
                "Resume Text Extraction",
                (datetime.now() - step_start).total_seconds()
            )

            if not resumes:
                self.logger.error("No resume texts extracted successfully")
                return 1

            # Step 5: Match resumes to opportunities
            log_step_start(self.logger, "Resume Matching")
            step_start = datetime.now()

            matcher = ResumeMatcher(self.client, self.config, self.logger)
            match_results = self._match_all(matcher, resumes, opportunities)

            log_step_complete(
                self.logger,
                "Resume Matching",
                (datetime.now() - step_start).total_seconds()
            )

            if not match_results:
                self.logger.error("No successful matches")
                return 1

            # Step 6: Generate output bundles
            log_step_start(self.logger, "Bundle Generation")
            step_start = datetime.now()

            orchestrator = BundleOrchestrator(self.logger)
            bundles = self._generate_bundles(orchestrator, match_results, opportunities)

            log_step_complete(
                self.logger,
                "Bundle Generation",
                (datetime.now() - step_start).total_seconds()
            )

            # Step 7: Send Slack notification
            log_step_start(self.logger, "Slack Notification")
            step_start = datetime.now()

            notifier = SlackNotifier(self.config.slack_webhook_url, self.logger)
            duration = (datetime.now() - start_time).total_seconds()
            notifier.send_pipeline_complete(bundles, self.errors, duration)

            log_step_complete(
                self.logger,
                "Slack Notification",
                (datetime.now() - step_start).total_seconds()
            )

            # Final summary
            self.logger.info("=" * 60)
            self.logger.info(f"Pipeline complete in {duration:.2f}s")
            self.logger.info(f"Generated {len(bundles)} bundles")
            if self.errors:
                self.logger.warning(f"Completed with {len(self.errors)} errors")
            else:
                self.logger.info("All tasks completed successfully")
            self.logger.info("=" * 60)

            return 0 if not self.errors else 1

        except KeyboardInterrupt:
            self.logger.warning("Pipeline interrupted by user")
            return 1
        except Exception as e:
            self.logger.exception(f"Pipeline failed: {e}")

            # Try to send error notification
            try:
                notifier = SlackNotifier(self.config.slack_webhook_url, self.logger)
                notifier.send_error(str(e))
            except:
                pass

            return 1

    def _discover_opportunity_files(self) -> List[Path]:
        """Find all PDF/DOCX files in inbox/"""
        inbox = Path(self.config.inbox_dir)
        pdf_files = list(inbox.glob("*.pdf"))
        docx_files = list(inbox.glob("*.docx"))
        return pdf_files + docx_files

    def _discover_resume_files(self) -> List[Path]:
        """Find all PDF/DOCX files in resumes/"""
        resumes = Path(self.config.resumes_dir)
        pdf_files = list(resumes.glob("*.pdf"))
        docx_files = list(resumes.glob("*.docx"))
        return pdf_files + docx_files

    def _extract_documents(self, file_paths: List[Path]) -> List[Tuple[Path, str]]:
        """Extract text from multiple documents"""
        results = []

        for file_path in file_paths:
            try:
                extractor = ExtractorFactory.get_extractor(file_path)
                text = extractor.extract_text(file_path)

                if not text.strip():
                    self.logger.warning(f"Extracted empty text from {file_path.name}")
                    self.errors.append(f"Empty extraction: {file_path.name}")
                    continue

                results.append((file_path, text))
                self.logger.info(f"✓ Extracted {len(text)} chars from {file_path.name}")

            except UnsupportedFileTypeError as e:
                self.logger.error(f"Unsupported file type: {file_path.name}")
                self.errors.append(f"Unsupported file: {file_path.name}")
            except Exception as e:
                self.logger.error(f"Failed to extract {file_path.name}: {e}")
                self.errors.append(f"Extraction failed: {file_path.name}")

        return results

    def _extract_resumes(self, file_paths: List[Path]) -> List[Resume]:
        """Extract text from resumes and create Resume objects"""
        resumes = []

        for file_path, text in self._extract_documents(file_paths):
            resumes.append(Resume(
                file_name=file_path.name,
                file_path=file_path,
                text_content=text
            ))

        return resumes

    def _parse_opportunities(
        self,
        parser: OpportunityParser,
        opp_texts: List[Tuple[Path, str]]
    ) -> List[OpportunityData]:
        """Parse opportunities with Claude and save to opps/"""
        opportunities = []

        for file_path, text in opp_texts:
            try:
                opp_key = file_path.stem
                opp_data = parser.parse_opportunity(file_path, text)
                parser.save_requirements_json(opp_data, Path(self.config.opps_dir) / opp_key)
                opportunities.append(opp_data)

                self.logger.info(
                    f"✓ Parsed {opp_data.opportunity_id}: "
                    f"{len(opp_data.required_qualifications)} required, "
                    f"{len(opp_data.preferred_qualifications)} preferred"
                )

            except Exception as e:
                self.logger.error(f"Failed to parse {file_path.name}: {e}")
                self.errors.append(f"Parsing failed: {file_path.name}")

        return opportunities

    def _match_all(
        self,
        matcher: ResumeMatcher,
        resumes: List[Resume],
        opportunities: List[OpportunityData]
    ) -> List[Tuple[MatchResult, OpportunityData]]:
        """Match all resumes against all opportunities"""
        results = []
        total_matches = len(resumes) * len(opportunities)

        self.logger.info(f"Performing {total_matches} resume-opportunity matches")

        for opp in opportunities:
            for resume in resumes:
                try:
                    match_result = matcher.match_resume(
                        resume.text_content,
                        resume.file_name,
                        opp
                    )
                    results.append((match_result, opp))

                    match_percent = match_result.overall_match_percentage
                    pct_txt = "N/A" if match_percent is None else f"{match_percent:.1f}%"
                    self.logger.info(
                        f"✓ {match_result.candidate_name} -> {opp.opportunity_id}: "
                        f"{pct_txt} match, {len(match_result.critical_gaps)} critical gaps"
                    )

                except Exception as e:
                    self.logger.error(
                        f"Failed to match {resume.file_name} to {opp.opportunity_id}: {e}"
                    )
                    self.errors.append(
                        f"Matching failed: {resume.file_name} -> {opp.opportunity_id}"
                    )

        return results

    def _generate_bundles(
        self,
        orchestrator: BundleOrchestrator,
        match_results: List[Tuple[MatchResult, OpportunityData]],
        opportunities: List[OpportunityData]
    ) -> List[BundleInfo]:
        """Generate output bundles for all matches"""
        bundles = []
        output_dir = Path(self.config.outputs_dir)

        for match_result, opp_data in match_results:
            try:
                bundle = orchestrator.generate_bundle(
                    match_result,
                    opp_data,
                    output_dir
                )
                bundles.append(bundle)

                self.logger.info(f"✓ Generated bundle: {bundle}")

            except Exception as e:
                self.logger.error(
                    f"Failed to generate bundle for {match_result.candidate_name}: {e}"
                )
                self.errors.append(
                    f"Bundle generation failed: {match_result.candidate_name} -> {opp_data.opportunity_id}"
                )

        return bundles


def main():
    """Entry point"""
    print("=" * 60)
    print("  Government Submission Bot - Pipeline")
    print("=" * 60)
    print()

    orchestrator = PipelineOrchestrator()
    exit_code = orchestrator.run()

    print()
    if exit_code == 0:
        print("✅ Pipeline completed successfully")
    else:
        print("⚠️  Pipeline completed with errors")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
