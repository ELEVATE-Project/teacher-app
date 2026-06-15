#!/usr/bin/env python3
"""
Script to generate embeddings for all NCERT books and store them in the database
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

# Import from embedding package
try:
    from embedding.process_books import BookProcessor
except ImportError:
    # Fallback for direct execution
    sys.path.insert(0, str(Path(__file__).parent))
    from process_books import BookProcessor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('embedding/generation_log.txt', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def main():
    """Main function to process all books"""
    parser = argparse.ArgumentParser(
        description="Generate embeddings for all NCERT books"
    )
    parser.add_argument(
        '--books-dir',
        type=str,
        default='Finaldata',
        help='Directory containing PDF books (default: Finaldata)'
    )
    parser.add_argument(
        '--db-path',
        type=str,
        default='embedding/ncert_books.db',
        help='Path to SQLite database (default: embedding/ncert_books.db)'
    )
    parser.add_argument(
        '--no-skip-existing',
        action='store_true',
        help='Reprocess books even if they already exist in database'
    )
    parser.add_argument(
        '--max-files',
        type=int,
        default=None,
        help='Maximum number of files to process (for testing)'
    )
    parser.add_argument(
        '--llama-api-key',
        type=str,
        default=None,
        help='LlamaParse API key (default: from LLAMA_CLOUD_API_KEY env var)'
    )
    
    args = parser.parse_args()
    
    # Validate API key
    llama_api_key = args.llama_api_key or os.getenv("LLAMA_CLOUD_API_KEY")
    if not llama_api_key:
        logger.error(
            "LlamaParse API key not found. "
            "Set LLAMA_CLOUD_API_KEY environment variable or use --llama-api-key"
        )
        sys.exit(1)
    
    # Check if books directory exists
    books_dir = Path(args.books_dir)
    if not books_dir.exists():
        logger.error(f"Books directory not found: {books_dir}")
        sys.exit(1)
    
    # Create database directory if needed
    db_path = Path(args.db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info("=" * 60)
    logger.info("NCERT Books Embedding Generation")
    logger.info("=" * 60)
    logger.info(f"Books directory: {books_dir}")
    logger.info(f"Database path: {db_path}")
    logger.info(f"Skip existing: {not args.no_skip_existing}")
    if args.max_files:
        logger.info(f"Max files: {args.max_files}")
    logger.info("=" * 60)
    
    try:
        # Initialize processor
        processor = BookProcessor(
            books_dir=str(books_dir),
            db_path=str(db_path),
            llama_api_key=llama_api_key
        )
        
        # Process all books
        stats = processor.process_all_books(
            skip_existing=not args.no_skip_existing,
            max_files=args.max_files
        )
        
        # Close database connection
        processor.close()
        
        logger.info("\nProcessing completed successfully!")
        logger.info(f"Total documents in database: {stats['total_documents_in_db']}")
        
    except KeyboardInterrupt:
        logger.info("\nProcessing interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error during processing: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
