"""Resume matcher using Claude API with evidence validation"""

import json
import logging
import time
from typing import Optional, List
import anthropic
from rapidfuzz import fuzz

from ..models.opportunity import OpportunityData
from ..models.match_result import MatchResult, RequirementMatch
from .prompts import create_matching_prompt


class ResumeMatcher:
    """Match resume against opportunity requirements"""

    def __init__(self, client: anthropic.Anthropic, config, logger: Optional[logging.Logger] = None):
        self.client = client
        self.config = config
        self.logger = logger or logging.getLogger(__name__)

    def match_resume(
        self,
        resume_text: str,
        resume_file_name: str,
        opp_data: OpportunityData
    ) -> MatchResult:
        """
        Match resume against all requirements

        Args:
            resume_text: Raw text from resume
            resume_file_name: Original filename
            opp_data: Opportunity data with requirements

        Returns:
            MatchResult object

        Raises:
            Exception: If matching fails after retries
        """
        self.logger.info(f"Matching {resume_file_name} to {opp_data.opportunity_id}")

        # Truncate if too long
        if len(resume_text) > self.config.max_document_chars:
            self.logger.warning(
                f"Resume text is {len(resume_text)} chars, truncating to {self.config.max_document_chars}"
            )
            resume_text = resume_text[:self.config.max_document_chars]

        # Prepare requirements for matching
        requirements = [
            {
                'id': q.id,
                'text': q.text,
                'category': q.category,
                'is_required': q.is_required
            }
            for q in opp_data.all_qualifications()
        ]

        # Create prompt
        prompt = create_matching_prompt(
            resume_text,
            resume_file_name,
            opp_data.opportunity_id,
            requirements
        )

        # Call Claude with retries
        response_text = self._call_claude_with_retry(prompt)

        # Parse JSON response
        match_result = self._parse_response(response_text, resume_file_name, opp_data.opportunity_id)

        # Validate evidence snippets
        self._validate_evidence(match_result, resume_text)

        self.logger.info(
            f"Match complete: {match_result.overall_match_percentage:.1f}% match, "
            f"{len(match_result.critical_gaps)} critical gaps"
        )

        return match_result

    def _call_claude_with_retry(self, prompt: str) -> str:
        """Call Claude API with retry logic"""
        last_error = None

        for attempt in range(self.config.max_retries):
            try:
                self.logger.debug(f"Claude API call attempt {attempt + 1}/{self.config.max_retries}")

                response = self.client.messages.create(
                    model=self.config.claude_model,
                    max_tokens=self.config.claude_max_tokens_matching,
                    temperature=self.config.claude_temperature,
                    messages=[{
                        "role": "user",
                        "content": prompt
                    }]
                )

                # Extract text from response
                response_text = response.content[0].text

                self.logger.debug(
                    f"Claude API success: {response.usage.input_tokens} in, "
                    f"{response.usage.output_tokens} out"
                )

                return response_text

            except anthropic.RateLimitError as e:
                last_error = e
                if attempt < self.config.max_retries - 1:
                    delay = self.config.retry_delays[attempt]
                    self.logger.warning(f"Rate limit hit, retrying in {delay}s...")
                    time.sleep(delay)
            except anthropic.APITimeoutError as e:
                last_error = e
                if attempt < self.config.max_retries - 1:
                    delay = self.config.retry_delays[attempt]
                    self.logger.warning(f"API timeout, retrying in {delay}s...")
                    time.sleep(delay)
            except anthropic.APIError as e:
                last_error = e
                self.logger.error(f"Claude API error: {e}")
                if attempt < self.config.max_retries - 1:
                    delay = self.config.retry_delays[attempt]
                    self.logger.warning(f"Retrying in {delay}s...")
                    time.sleep(delay)

        # All retries failed
        raise Exception(f"Claude API call failed after {self.config.max_retries} attempts: {last_error}")

    def _parse_response(self, response_text: str, resume_file: str, opportunity_id: str) -> MatchResult:
        """Parse JSON response from Claude"""
        try:
            # Try to extract JSON from response
            json_text = response_text.strip()

            # Remove markdown code blocks if present
            if json_text.startswith('```'):
                lines = json_text.split('\n')
                json_text = '\n'.join(lines[1:-1])
                if json_text.startswith('json'):
                    json_text = json_text[4:].strip()

            # Parse JSON
            data = json.loads(json_text)

            # Validate required fields
            if 'match_results' not in data:
                raise ValueError("Missing 'match_results' in response")

            # Convert to MatchResult
            return MatchResult(
                candidate_name=data.get('candidate_name', 'Unknown'),
                resume_file=resume_file,
                opportunity_id=opportunity_id,
                match_results=[
                    RequirementMatch(
                        requirement_id=m['requirement_id'],
                        requirement_text=m['requirement_text'],
                        status=m['status'],
                        evidence_snippets=m.get('evidence_snippets', []),
                        roles_used=m.get('roles_used', []),
                        years_calculated=m.get('years_calculated'),
                        confidence=m.get('confidence', 0.0),
                        reasoning=m.get('reasoning', '')
                    )
                    for m in data['match_results']
                ],
                overall_match_percentage=data.get('overall_match_percentage', 0.0),
                critical_gaps=data.get('critical_gaps', [])
            )

        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON response: {e}")
            self.logger.debug(f"Response text: {response_text}")
            raise Exception(f"Invalid JSON response from Claude: {e}")
        except (ValueError, TypeError, KeyError) as e:
            self.logger.error(f"Invalid response structure: {e}")
            raise Exception(f"Invalid response structure: {e}")

    def _validate_evidence(self, match_result: MatchResult, resume_text: str):
        """
        Validate that evidence snippets actually exist in resume

        Uses fuzzy matching to allow for minor whitespace differences
        """
        for match in match_result.match_results:
            if not match.evidence_snippets:
                continue

            validated_snippets = []
            for snippet in match.evidence_snippets:
                if self._snippet_exists_in_resume(snippet, resume_text):
                    validated_snippets.append(snippet)
                else:
                    self.logger.warning(
                        f"Evidence snippet not found in resume for {match.requirement_id}: "
                        f"'{snippet[:50]}...'"
                    )

            # If evidence validation failed, downgrade status
            if len(validated_snippets) < len(match.evidence_snippets):
                original_status = match.status
                original_count = len(match.evidence_snippets)
                validated_count = len(validated_snippets)

                # Update evidence list
                match.evidence_snippets = validated_snippets

                # Downgrade status if needed
                if validated_count == 0:
                    match.status = "not_evidenced"
                    match.confidence = min(match.confidence, 0.3)
                    self.logger.warning(
                        f"Downgraded {match.requirement_id} from '{original_status}' to 'not_evidenced' "
                        f"(no valid evidence found)"
                    )
                elif match.status == "meets":
                    match.status = "partial"
                    match.confidence = min(match.confidence, 0.7)
                    self.logger.warning(
                        f"Downgraded {match.requirement_id} from 'meets' to 'partial' "
                        f"(only {validated_count}/{original_count} evidence snippets validated)"
                    )

    def _snippet_exists_in_resume(self, snippet: str, resume_text: str, threshold: int = 85) -> bool:
        """
        Check if snippet exists in resume using fuzzy matching

        Args:
            snippet: Evidence snippet to find
            resume_text: Full resume text
            threshold: Fuzzy match threshold (0-100)

        Returns:
            True if snippet found (with fuzzy matching)
        """
        # Normalize whitespace
        snippet_normalized = ' '.join(snippet.split())

        # Try exact match first (after normalization)
        if snippet_normalized.lower() in resume_text.lower():
            return True

        # Try fuzzy matching on sliding windows
        # This handles cases where whitespace/formatting differs
        snippet_len = len(snippet_normalized)
        window_size = snippet_len + 50  # Allow some extra chars

        for i in range(0, len(resume_text) - window_size + 1, 50):
            window = resume_text[i:i + window_size]
            window_normalized = ' '.join(window.split())

            # Use partial ratio for substring matching
            similarity = fuzz.partial_ratio(snippet_normalized.lower(), window_normalized.lower())

            if similarity >= threshold:
                return True

        return False
