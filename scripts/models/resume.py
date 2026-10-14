"""Resume data models"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class Resume:
    """Resume data"""
    file_name: str
    file_path: Path
    text_content: str
    candidate_name: Optional[str] = None

    def get_candidate_name_safe(self) -> str:
        """Get candidate name or derive from filename"""
        if self.candidate_name:
            return self.candidate_name
        # Remove extension and clean up filename
        return self.file_path.stem.replace('_', ' ').replace('-', ' ').title()
