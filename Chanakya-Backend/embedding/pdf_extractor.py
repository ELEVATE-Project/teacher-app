"""
PDF text extraction using LlamaParse API
"""

import os
import logging
import time
from typing import List, Dict, Optional
from pathlib import Path
from llama_cloud_services import LlamaParse
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

# LlamaParse tier options: fast, cost_effective, agentic, agentic_plus
LLAMAPARSE_TIER_OPTIONS = ("fast", "cost_effective", "agentic", "agentic_plus")


class PDFExtractor:
    """Extract text from PDFs using LlamaParse API"""

    def __init__(self, api_key: Optional[str] = None, tier: Optional[str] = None):
        """
        Initialize PDF extractor with LlamaParse

        Args:
            api_key: LlamaParse API key (if None, reads from LLAMA_CLOUD_API_KEY env var)
            tier: Parsing tier (if None, reads from LLAMAPARSE_TIER env var; default: fast).
                Options: fast, cost_effective, agentic, agentic_plus
        """
        self.api_key = api_key or os.getenv("LLAMA_CLOUD_API_KEY")

        if not self.api_key:
            raise ValueError(
                "LlamaParse API key not provided. "
                "Set LLAMA_CLOUD_API_KEY environment variable or pass api_key parameter. "
                "Get your API key from: https://cloud.llamaindex.ai/"
            )

        # Validate API key format (should not be empty or placeholder)
        if self.api_key.strip() in ["", "your_llama_parse_api_key_here", "your_api_key_here"]:
            raise ValueError(
                "Invalid LlamaParse API key. Please set a valid API key in .env file. "
                "Get your API key from: https://cloud.llamaindex.ai/"
            )

        raw_tier = (tier or os.getenv("LLAMAPARSE_TIER", "fast")).strip().lower()
        self.tier = raw_tier if raw_tier in LLAMAPARSE_TIER_OPTIONS else "fast"

        # Initialize LlamaParse with selected tier
        self.parser = LlamaParse(
            api_key=self.api_key,
            tier=self.tier,
            version="latest",
            max_pages=0,  # 0 means parse all pages
            precise_bounding_box=True,
        )

        logger.info("PDF extractor initialized with LlamaParse tier=%s", self.tier)
    
    def extract_text(self, pdf_path: str, max_retries: int = 3) -> List[Dict[str, any]]:
        """
        Extract text from a PDF file with page-level granularity
        
        Args:
            pdf_path: Path to the PDF file
            max_retries: Maximum number of retry attempts
        
        Returns:
            List of dictionaries, each containing:
            - 'page_number': Page number (1-indexed)
            - 'text': Text content of the page
        """
        pdf_path = Path(pdf_path)
        
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        if not pdf_path.suffix.lower() == '.pdf':
            raise ValueError(f"File is not a PDF: {pdf_path}")
        
        logger.info(f"Extracting text from: {pdf_path.name}")
        
        # Retry logic with exponential backoff
        for attempt in range(max_retries):
            try:
                # Parse the PDF using the new API
                result = self.parser.parse(str(pdf_path))
                
                # Get text documents split by page
                text_documents = result.get_text_documents(split_by_page=True)
                
                # Extract pages from the parsed document
                pages = []
                
                # Process each document (each document represents a page)
                for i, doc in enumerate(text_documents, 1):
                    # Get text content
                    text = doc.text if hasattr(doc, 'text') else str(doc)
                    
                    # Try to get page number from metadata
                    page_num = None
                    if hasattr(doc, 'metadata') and doc.metadata:
                        page_num = doc.metadata.get('page_label', None)
                        if page_num:
                            try:
                                page_num = int(page_num)
                            except (ValueError, TypeError):
                                page_num = None
                    
                    # If no page number from metadata, use index
                    if page_num is None:
                        page_num = i
                    
                    if text and text.strip():
                        pages.append({
                            'page_number': page_num,
                            'text': text.strip()
                        })
                
                # If no pages extracted, try accessing raw pages
                if not pages:
                    # Try accessing result.pages directly
                    if hasattr(result, 'pages') and result.pages:
                        for i, page in enumerate(result.pages, 1):
                            page_text = getattr(page, 'text', None) or getattr(page, 'md', '')
                            if page_text and page_text.strip():
                                pages.append({
                                    'page_number': i,
                                    'text': page_text.strip()
                                })
                
                # If still no pages, try markdown documents
                if not pages:
                    try:
                        markdown_docs = result.get_markdown_documents(split_by_page=True)
                        for i, doc in enumerate(markdown_docs, 1):
                            text = doc.text if hasattr(doc, 'text') else str(doc)
                            if text and text.strip():
                                pages.append({
                                    'page_number': i,
                                    'text': text.strip()
                                })
                    except Exception as e:
                        logger.warning(f"Could not get markdown documents: {e}")
                
                # Sort pages by page number
                pages.sort(key=lambda x: x['page_number'])
                
                logger.info(f"Extracted {len(pages)} pages from {pdf_path.name}")
                return pages
                
            except Exception as e:
                error_msg = str(e)
                
                # Check for authentication errors
                if "401" in error_msg or "Invalid token" in error_msg or "Unauthorized" in error_msg:
                    logger.error(
                        f"LlamaParse API authentication failed. Please check your API key.\n"
                        f"  - Verify LLAMA_CLOUD_API_KEY in .env file\n"
                        f"  - Get your API key from: https://cloud.llamaindex.ai/\n"
                        f"  - Make sure the API key is correct and not expired"
                    )
                    raise ValueError(
                        "Invalid LlamaParse API key. Please check your .env file and ensure "
                        "LLAMA_CLOUD_API_KEY is set correctly. Get your API key from: "
                        "https://cloud.llamaindex.ai/"
                    ) from e
                
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.warning(
                        f"Error extracting PDF (attempt {attempt + 1}/{max_retries}): {e}. "
                        f"Retrying in {wait_time} seconds..."
                    )
                    time.sleep(wait_time)
                else:
                    logger.error(f"Failed to extract PDF after {max_retries} attempts: {e}")
                    raise
        
        return []
    
    def extract_text_batch(self, pdf_paths: List[str]) -> Dict[str, List[Dict[str, any]]]:
        """
        Extract text from multiple PDF files
        
        Args:
            pdf_paths: List of paths to PDF files
        
        Returns:
            Dictionary mapping PDF paths to their extracted pages
        """
        results = {}
        
        for pdf_path in pdf_paths:
            try:
                pages = self.extract_text(pdf_path)
                results[pdf_path] = pages
            except Exception as e:
                logger.error(f"Failed to extract {pdf_path}: {e}")
                results[pdf_path] = []
        
        return results
    
    def extract_metadata_from_path(self, pdf_path: str) -> Dict[str, str]:
        """
        Extract metadata (class, subject, bookname, language) from file path
        
        Supports two folder structures:
        1. Finaldata/Class X/Subject/PDF file
        2. books/Class_X/Subject/Language/filename.pdf (original structure)
        
        Args:
            pdf_path: Path to the PDF file
        
        Returns:
            Dictionary with metadata: class, subject, bookname, language
        """
        path = Path(pdf_path)
        parts = path.parts
        
        metadata = {
            'class': None,
            'subject': None,
            'bookname': None,
            'language': 'English'  # Default to English for Finaldata structure
        }
        
        try:
            # Check for Finaldata structure: Finaldata/Class X/Subject/PDF file
            if 'Finaldata' in parts:
                finaldata_idx = parts.index('Finaldata')
                remaining_parts = parts[finaldata_idx + 1:]
                
                if len(remaining_parts) >= 1:
                    # First part is class (e.g., "Class 6", "Class 7")
                    class_name = remaining_parts[0]
                    metadata['class'] = class_name.replace(' ', '_')  # Normalize to Class_6 format
                    
                    if len(remaining_parts) >= 2:
                        # Second part is subject
                        subject_name = remaining_parts[1]
                        # Clean up subject name (remove "Class X - " prefix if present)
                        subject_name = subject_name.replace(f"{class_name} - ", "").replace(f"{class_name} ", "")
                        metadata['subject'] = subject_name
                        
                        # Bookname is the PDF filename
                        if len(remaining_parts) >= 3:
                            metadata['bookname'] = Path(remaining_parts[-1]).stem
                        else:
                            metadata['bookname'] = path.stem
                    else:
                        metadata['bookname'] = path.stem
                else:
                    metadata['bookname'] = path.stem
            
            # Check for original books structure: books/Class_X/Subject/Language/filename.pdf
            elif 'books' in parts:
                books_idx = parts.index('books')
                remaining_parts = parts[books_idx + 1:]
                
                if len(remaining_parts) >= 1:
                    # First part should be class
                    class_name = remaining_parts[0]
                    metadata['class'] = class_name
                    
                    if len(remaining_parts) >= 2:
                        # Second part should be subject
                        subject_name = remaining_parts[1]
                        metadata['subject'] = subject_name
                        
                        if len(remaining_parts) >= 3:
                            # Third part might be language or bookname
                            third_part = remaining_parts[2]
                            
                            # Check if it's a language (common languages)
                            common_languages = ['English', 'Hindi', 'Urdu', 'Sanskrit', 'Tamil', 'Telugu', 'Marathi', 'Gujarati', 'Bengali']
                            if third_part in common_languages:
                                metadata['language'] = third_part
                                if len(remaining_parts) >= 4:
                                    metadata['bookname'] = Path(remaining_parts[3]).stem
                            else:
                                # It's probably a bookname/folder
                                metadata['bookname'] = Path(third_part).stem
                                if len(remaining_parts) >= 4:
                                    metadata['language'] = remaining_parts[3]
            
            # If bookname not found, use filename
            if not metadata['bookname']:
                metadata['bookname'] = path.stem
            
            # If subject not found, try to extract from path
            if not metadata['subject']:
                # Try to find subject-like folder names
                for part in parts:
                    if any(keyword in part for keyword in ['Science', 'History', 'Geography', 'Mathematics', 'Social', 'Political']):
                        metadata['subject'] = part
                        break
            
        except (ValueError, IndexError) as e:
            logger.warning(f"Could not extract metadata from path {pdf_path}: {e}")
            # Fallback: use filename
            if not metadata['bookname']:
                metadata['bookname'] = path.stem
        
        return metadata
