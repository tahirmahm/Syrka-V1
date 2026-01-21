"""PDF document processing for policy documents."""

import fitz  # PyMuPDF
from typing import Optional
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class PDFProcessor:
    """
    PDF processor for extracting text and structure from policy documents.

    Uses PyMuPDF (fitz) for efficient PDF parsing.
    """

    def extract_text(self, file_path: str) -> str:
        """
        Extract all text from a PDF file.

        Args:
            file_path: Path to PDF file

        Returns:
            Full text content of the PDF

        Raises:
            FileNotFoundError: If file doesn't exist
            Exception: If PDF processing fails
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")

        try:
            doc = fitz.open(file_path)
            text_parts = []

            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()
                text_parts.append(text)

            doc.close()

            full_text = "\n\n".join(text_parts)
            logger.info(f"Extracted {len(full_text)} characters from {file_path.name}")

            return full_text

        except Exception as e:
            logger.error(f"Failed to extract text from {file_path}: {str(e)}")
            raise

    def extract_with_structure(self, file_path: str) -> dict:
        """
        Extract text with structural information (headings, sections, pages).

        Args:
            file_path: Path to PDF file

        Returns:
            Dictionary with structured content:
            {
                'pages': [
                    {
                        'page_num': 1,
                        'text': '...',
                        'headings': [...],
                        'sections': [...]
                    },
                    ...
                ],
                'metadata': {...}
            }
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")

        try:
            doc = fitz.open(file_path)
            pages_data = []

            # Extract metadata
            metadata = doc.metadata

            for page_num in range(len(doc)):
                page = doc[page_num]

                # Extract text
                text = page.get_text()

                # Extract text with formatting (to identify headings)
                blocks = page.get_text("dict")["blocks"]

                headings = []
                sections = []

                for block in blocks:
                    if block.get("type") == 0:  # Text block
                        for line in block.get("lines", []):
                            for span in line.get("spans", []):
                                text_content = span.get("text", "").strip()
                                font_size = span.get("size", 0)

                                # Heuristic: larger font size indicates heading
                                if font_size > 14 and text_content:
                                    headings.append({
                                        'text': text_content,
                                        'font_size': font_size,
                                        'page': page_num + 1
                                    })

                page_data = {
                    'page_num': page_num + 1,
                    'text': text,
                    'headings': headings
                }

                pages_data.append(page_data)

            doc.close()

            structured_data = {
                'pages': pages_data,
                'metadata': metadata,
                'total_pages': len(pages_data)
            }

            logger.info(f"Extracted structured content from {file_path.name}: {len(pages_data)} pages")

            return structured_data

        except Exception as e:
            logger.error(f"Failed to extract structured content from {file_path}: {str(e)}")
            raise

    def extract_tables(self, file_path: str) -> list[dict]:
        """
        Extract tables from PDF.

        Args:
            file_path: Path to PDF file

        Returns:
            List of table dictionaries with page number and content
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")

        tables = []

        try:
            doc = fitz.open(file_path)

            for page_num in range(len(doc)):
                page = doc[page_num]

                # Find tables using layout analysis
                # This is a simplified approach - production might use dedicated table extraction libraries
                tabs = page.find_tables()

                for table in tabs:
                    try:
                        table_data = {
                            'page': page_num + 1,
                            'rows': table.extract(),
                            'bbox': table.bbox
                        }
                        tables.append(table_data)
                    except:
                        continue

            doc.close()

            logger.info(f"Extracted {len(tables)} tables from {file_path.name}")

            return tables

        except Exception as e:
            logger.error(f"Failed to extract tables from {file_path}: {str(e)}")
            return []

    def get_page_count(self, file_path: str) -> int:
        """
        Get the number of pages in a PDF.

        Args:
            file_path: Path to PDF file

        Returns:
            Number of pages
        """
        try:
            doc = fitz.open(file_path)
            page_count = len(doc)
            doc.close()
            return page_count
        except Exception as e:
            logger.error(f"Failed to get page count from {file_path}: {str(e)}")
            return 0

    def extract_page_range(self, file_path: str, start_page: int, end_page: int) -> str:
        """
        Extract text from a specific page range.

        Args:
            file_path: Path to PDF file
            start_page: Starting page number (1-indexed)
            end_page: Ending page number (1-indexed, inclusive)

        Returns:
            Text from specified pages
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")

        try:
            doc = fitz.open(file_path)
            text_parts = []

            # Convert to 0-indexed and ensure within bounds
            start_idx = max(0, start_page - 1)
            end_idx = min(len(doc), end_page)

            for page_num in range(start_idx, end_idx):
                page = doc[page_num]
                text = page.get_text()
                text_parts.append(text)

            doc.close()

            return "\n\n".join(text_parts)

        except Exception as e:
            logger.error(f"Failed to extract page range from {file_path}: {str(e)}")
            raise
