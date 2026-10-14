"""PDF text extractor using pdfminer.six"""

import logging
from pathlib import Path
from pdfminer.high_level import extract_text
from pdfminer.pdfparser import PDFSyntaxError
from .base import DocumentExtractor


class PDFExtractor(DocumentExtractor):
    """Extract text from PDF files using pdfminer.six"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def extract_text(self, file_path: Path) -> str:
        """
        Extract text from PDF file

        Args:
            file_path: Path to PDF file

        Returns:
            Extracted text content

        Raises:
            PDFSyntaxError: If PDF is corrupted
            FileNotFoundError: If file doesn't exist
        """
        try:
            self.logger.debug(f"Extracting text from PDF: {file_path}")

            # Extract text using pdfminer.six high-level API
            text = extract_text(str(file_path))

            # Clean up excessive whitespace
            text = self._clean_text(text)

            self.logger.debug(f"Extracted {len(text)} characters from {file_path.name}")
            return text

        except PDFSyntaxError as e:
            self.logger.error(f"PDF syntax error in {file_path.name}: {e}")
            raise
        except FileNotFoundError as e:
            self.logger.error(f"PDF file not found: {file_path}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error extracting PDF {file_path.name}: {e}")
            raise

    def supports_file(self, file_path: Path) -> bool:
        """Check if file is a PDF"""
        return file_path.suffix.lower() == '.pdf'

    def _clean_text(self, text: str) -> str:
        """Clean up extracted text"""
        # Remove excessive blank lines (more than 2 consecutive newlines)
        import re
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)

        # Strip leading/trailing whitespace
        text = text.strip()

        return text
