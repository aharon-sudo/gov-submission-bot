"""Abstract base class for document extractors"""

from abc import ABC, abstractmethod
from pathlib import Path


class DocumentExtractor(ABC):
    """Abstract base class for document extractors"""

    @abstractmethod
    def extract_text(self, file_path: Path) -> str:
        """
        Extract text from document

        Args:
            file_path: Path to document file

        Returns:
            Extracted text content

        Raises:
            Exception: If extraction fails
        """
        pass

    @abstractmethod
    def supports_file(self, file_path: Path) -> bool:
        """
        Check if this extractor supports the file type

        Args:
            file_path: Path to check

        Returns:
            True if this extractor can handle the file
        """
        pass
