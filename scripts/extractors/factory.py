"""Factory for selecting appropriate document extractor"""

from pathlib import Path
from .base import DocumentExtractor
from .pdf_extractor import PDFExtractor
from .docx_extractor import DOCXExtractor


class UnsupportedFileTypeError(Exception):
    """Raised when file type is not supported"""
    pass


class ExtractorFactory:
    """Factory for selecting appropriate document extractor"""

    @staticmethod
    def get_extractor(file_path: Path) -> DocumentExtractor:
        """
        Select extractor based on file extension

        Args:
            file_path: Path to file

        Returns:
            Appropriate DocumentExtractor instance

        Raises:
            UnsupportedFileTypeError: If file type is not supported
        """
        suffix = file_path.suffix.lower()

        if suffix == '.pdf':
            return PDFExtractor()
        elif suffix == '.docx':
            return DOCXExtractor()
        else:
            raise UnsupportedFileTypeError(
                f"Unsupported file type: {suffix}. Supported types: .pdf, .docx"
            )
