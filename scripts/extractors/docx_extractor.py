"""DOCX text extractor using python-docx"""

import logging
from pathlib import Path
from docx import Document
from docx.opc.exceptions import PackageNotFoundError
from .base import DocumentExtractor


class DOCXExtractor(DocumentExtractor):
    """Extract text from DOCX files using python-docx"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def extract_text(self, file_path: Path) -> str:
        """
        Extract text from DOCX file

        Args:
            file_path: Path to DOCX file

        Returns:
            Extracted text content

        Raises:
            PackageNotFoundError: If DOCX is corrupted or invalid
            FileNotFoundError: If file doesn't exist
        """
        try:
            self.logger.debug(f"Extracting text from DOCX: {file_path}")

            doc = Document(str(file_path))
            text_parts = []

            # Extract paragraph text
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text_parts.append(paragraph.text)

            # Extract table text (important for government forms)
            for table in doc.tables:
                for row in table.rows:
                    row_text = []
                    for cell in row.cells:
                        if cell.text.strip():
                            row_text.append(cell.text.strip())
                    if row_text:
                        text_parts.append(' | '.join(row_text))

            # Join all parts
            text = '\n'.join(text_parts)

            self.logger.debug(f"Extracted {len(text)} characters from {file_path.name}")
            return text

        except PackageNotFoundError as e:
            self.logger.error(f"Invalid DOCX file {file_path.name}: {e}")
            raise
        except FileNotFoundError as e:
            self.logger.error(f"DOCX file not found: {file_path}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error extracting DOCX {file_path.name}: {e}")
            raise

    def supports_file(self, file_path: Path) -> bool:
        """Check if file is a DOCX"""
        return file_path.suffix.lower() == '.docx'
