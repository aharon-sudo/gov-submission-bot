"""Configuration management"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
import anthropic


class ConfigurationError(Exception):
    """Raised when configuration is invalid"""
    pass


class Config:
    """Central configuration loaded from environment"""

    def __init__(self):
        # Load .env file
        load_dotenv()

        # API Keys
        self.anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
        if not self.anthropic_api_key:
            raise ConfigurationError("ANTHROPIC_API_KEY not found in .env")

        self.slack_webhook_url = os.getenv('SLACK_WEBHOOK_URL')
        if not self.slack_webhook_url:
            raise ConfigurationError("SLACK_WEBHOOK_URL not found in .env")

        # Directory paths (relative to project root)
        self.project_root = Path(__file__).parent.parent
        self.inbox_dir = self.project_root / 'inbox'
        self.resumes_dir = self.project_root / 'resumes'
        self.opps_dir = self.project_root / 'opps'
        self.outputs_dir = self.project_root / 'outputs'
        self.logs_dir = self.project_root / 'logs'

        # Claude API settings
        self.claude_model = 'claude-opus-4-5-20251101'  # Best accuracy
        self.claude_temperature = 0  # Deterministic
        self.claude_max_tokens_parsing = 4096
        self.claude_max_tokens_matching = 8192

        # Retry settings
        self.max_retries = 3
        self.retry_delays = [1, 2, 4]  # Exponential backoff in seconds

        # Document processing
        self.max_document_chars = 100000  # Truncate very long documents

        # Validate and create directories
        self.validate_directories()

    def validate_directories(self):
        """Ensure all required directories exist"""
        for dir_path in [self.opps_dir, self.outputs_dir, self.logs_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

        # Check that inbox and resumes exist (user should create these)
        if not self.inbox_dir.exists():
            raise ConfigurationError(f"inbox/ directory not found at {self.inbox_dir}")
        if not self.resumes_dir.exists():
            raise ConfigurationError(f"resumes/ directory not found at {self.resumes_dir}")

    def get_anthropic_client(self) -> anthropic.Anthropic:
        """Create authenticated Anthropic client"""
        return anthropic.Anthropic(api_key=self.anthropic_api_key)

    @classmethod
    def load(cls) -> 'Config':
        """Load and validate configuration"""
        return cls()
