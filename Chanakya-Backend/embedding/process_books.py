"""
Main processing pipeline for extracting text from PDFs, generating embeddings, and storing in database
"""

import os
import logging
from pathlib import Path
from typing import List, Tuple, Optional
from tqdm import tqdm

from .pdf_extractor import PDFExtractor
from .embedding_service import EmbeddingService
from .database import Database

logger = logging.getLogger(__name__)


class BookProcessor:
    """Process NCERT books: extract text, generate embeddings, store in database"""
    
    def __init__(self, books_dir: str = "Finaldata", db_path: str = "embedding/ncert_books.db",
                 llama_api_key: Optional[str] = None):
        """
        Initialize the book processor
        
        Args:
            books_dir: Directory containing PDF books
            db_path: Path to SQLite database
            llama_api_key: LlamaParse API key (optional, reads from env if not provided)
        """
        self.books_dir = Path(books_dir)
        self.db_path = db_path
        
        # Initialize components
        self.pdf_extractor = PDFExtractor(api_key=llama_api_key)
        self.embedding_service = EmbeddingService()
        self.database = Database(db_path=db_path)
        
        logger.info(f"Book processor initialized. Books directory: {self.books_dir}")
    
    def find_pdf_files(self) -> List[Path]:
        """
        Find all PDF files in the books directory
        
        Returns:
            List of paths to PDF files
        """
        pdf_files = list(self.books_dir.rglob("*.pdf")) + list(self.books_dir.rglob("*.PDF"))
        logger.info(f"Found {len(pdf_files)} PDF files")
        return pdf_files
    
    def process_single_book(self, pdf_path: Path, skip_existing: bool = True) -> Tuple[int, int]:
        """
        Process a single PDF book
        
        Args:
            pdf_path: Path to the PDF file
            skip_existing: If True, skip if book already processed
        
        Returns:
            Tuple of (pages_processed, pages_failed)
        """
        logger.info(f"Processing: {pdf_path}")
        
        # Extract metadata from path
        metadata = self.pdf_extractor.extract_metadata_from_path(str(pdf_path))
        class_name = metadata.get('class', 'Unknown')
        subject = metadata.get('subject', 'Unknown')
        bookname = metadata.get('bookname', pdf_path.stem)
        language = metadata.get('language', 'Unknown')
        
        # Check if already processed (simple check - could be improved)
        if skip_existing:
            source_pattern = f"{class_name}|{subject}|{bookname}|{language}|%"
            existing = self.database.get_documents_by_source(source_pattern)
            if existing:
                logger.info(f"Skipping {pdf_path.name} - already processed ({len(existing)} pages)")
                return len(existing), 0
        
        try:
            # Extract text from PDF
            pages = self.pdf_extractor.extract_text(str(pdf_path))
            
            if not pages:
                logger.warning(f"No pages extracted from {pdf_path.name}")
                return 0, 0
            
            # Prepare documents for batch processing
            documents_to_insert = []
            
            # Generate embeddings in batches
            texts = [page['text'] for page in pages]
            embeddings = self.embedding_service.generate_embeddings_batch(texts)
            
            # Create source strings and prepare for insertion
            for i, (page, embedding) in enumerate(zip(pages, embeddings)):
                page_num = page['page_number']
                content = page['text']
                
                # Format: "class|subject|bookname|language|page_number"
                source = f"{class_name}|{subject}|{bookname}|{language}|{page_num}"
                
                documents_to_insert.append((content, embedding, source))
            
            # Insert into database
            self.database.insert_documents_batch(documents_to_insert)
            
            logger.info(
                f"Processed {pdf_path.name}: {len(pages)} pages "
                f"(Class: {class_name}, Subject: {subject}, Language: {language})"
            )
            
            return len(pages), 0
            
        except Exception as e:
            logger.error(f"Error processing {pdf_path.name}: {e}")
            return 0, 1
    
    def process_all_books(self, skip_existing: bool = True, 
                         max_files: Optional[int] = None) -> dict:
        """
        Process all PDF books in the books directory
        
        Args:
            skip_existing: If True, skip books that are already processed
            max_files: Maximum number of files to process (None for all)
        
        Returns:
            Dictionary with processing statistics
        """
        pdf_files = self.find_pdf_files()
        
        if max_files:
            pdf_files = pdf_files[:max_files]
        
        logger.info(f"Starting to process {len(pdf_files)} PDF files")
        
        stats = {
            'total_files': len(pdf_files),
            'files_processed': 0,
            'files_failed': 0,
            'total_pages': 0,
            'pages_failed': 0
        }
        
        # Process with progress bar
        for pdf_path in tqdm(pdf_files, desc="Processing books"):
            try:
                pages_processed, pages_failed = self.process_single_book(
                    pdf_path, skip_existing=skip_existing
                )
                
                stats['total_pages'] += pages_processed
                stats['pages_failed'] += pages_failed
                
                if pages_processed > 0 or pages_failed == 0:
                    stats['files_processed'] += 1
                else:
                    stats['files_failed'] += 1
                    
            except Exception as e:
                logger.error(f"Failed to process {pdf_path}: {e}")
                stats['files_failed'] += 1
        
        # Final statistics
        total_docs = self.database.get_document_count()
        stats['total_documents_in_db'] = total_docs
        
        logger.info("=" * 60)
        logger.info("Processing Summary:")
        logger.info(f"  Files processed: {stats['files_processed']}/{stats['total_files']}")
        logger.info(f"  Files failed: {stats['files_failed']}")
        logger.info(f"  Total pages processed: {stats['total_pages']}")
        logger.info(f"  Pages failed: {stats['pages_failed']}")
        logger.info(f"  Total documents in database: {total_docs}")
        logger.info("=" * 60)
        
        return stats
    
    def close(self):
        """Close database connection"""
        self.database.close()
