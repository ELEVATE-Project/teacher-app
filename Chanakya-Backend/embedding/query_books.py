#!/usr/bin/env python3
"""
Example script to query NCERT books using the RAG orchestrator
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
    from embedding.rag_orchestrator import RAGOrchestrator
except ImportError:
    # Fallback for direct execution
    sys.path.insert(0, str(Path(__file__).parent))
    from rag_orchestrator import RAGOrchestrator

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Main function to query books"""
    parser = argparse.ArgumentParser(
        description="Query NCERT books using RAG system"
    )
    parser.add_argument(
        'query',
        type=str,
        help='Question to ask about NCERT books'
    )
    parser.add_argument(
        '--db-path',
        type=str,
        default='embedding/ncert_books.db',
        help='Path to SQLite database (default: embedding/ncert_books.db)'
    )
    parser.add_argument(
        '--top-k',
        type=int,
        default=5,
        help='Number of relevant documents to retrieve (default: 5)'
    )
    parser.add_argument(
        '--class',
        type=str,
        default=None,
        dest='class_filter',
        help='Filter by class (e.g., Class_10)'
    )
    parser.add_argument(
        '--subject',
        type=str,
        default=None,
        help='Filter by subject (e.g., Mathematics)'
    )
    parser.add_argument(
        '--language',
        type=str,
        default=None,
        help='Filter by language (e.g., English)'
    )
    parser.add_argument(
        '--temperature',
        type=float,
        default=0.7,
        help='Temperature for Gemini generation (default: 0.7)'
    )
    parser.add_argument(
        '--gemini-api-key',
        type=str,
        default=None,
        help='Gemini API key (default: from GEMINI_API_KEY env var)'
    )
    parser.add_argument(
        '--model',
        type=str,
        default='models/gemini-2.5-flash',
        help='Gemini model to use (default: models/gemini-2.5-flash, options: models/gemini-2.5-flash, models/gemini-2.5-pro)'
    )
    parser.add_argument(
        '--interactive',
        action='store_true',
        help='Run in interactive mode (ask multiple questions)'
    )
    
    args = parser.parse_args()
    
    # Validate API key
    gemini_api_key = args.gemini_api_key or os.getenv("GEMINI_API_KEY")
    if not gemini_api_key or gemini_api_key.strip() == "":
        logger.error("=" * 60)
        logger.error("Gemini API key not found or is empty!")
        logger.error("=" * 60)
        logger.error("Please set GEMINI_API_KEY in your .env file:")
        logger.error("  1. Edit .env file: nano .env")
        logger.error("  2. Add: GEMINI_API_KEY=your_actual_api_key_here")
        logger.error("  3. Get your API key from: https://makersuite.google.com/app/apikey")
        logger.error("")
        logger.error("Or use --gemini-api-key flag: python embedding/query_books.py 'question' --gemini-api-key YOUR_KEY")
        logger.error("=" * 60)
        sys.exit(1)
    
    # Check if database exists
    db_path = Path(args.db_path)
    if not db_path.exists():
        logger.error(f"Database not found: {db_path}")
        logger.error("Please run generate_embeddings.py first to create the database")
        sys.exit(1)
    
    # Build filters
    filters = {}
    if args.class_filter:
        filters['class'] = args.class_filter
    if args.subject:
        filters['subject'] = args.subject
    if args.language:
        filters['language'] = args.language
    
    try:
        # Initialize RAG orchestrator
        orchestrator = RAGOrchestrator(
            db_path=str(db_path),
            gemini_api_key=gemini_api_key,
            model_name=args.model
        )
        
        # Get statistics
        stats = orchestrator.get_statistics()
        logger.info(f"Database contains {stats['total_documents']} documents")
        
        if args.interactive:
            # Interactive mode
            print("\n" + "=" * 60)
            print("NCERT Books RAG System - Interactive Mode")
            print("=" * 60)
            print("Type 'quit' or 'exit' to stop\n")
            
            while True:
                try:
                    query = input("\nQuestion: ").strip()
                    
                    if query.lower() in ['quit', 'exit', 'q']:
                        print("Goodbye!")
                        break
                    
                    if not query:
                        continue
                    
                    # Process query
                    result = orchestrator.query(
                        query,
                        top_k=args.top_k,
                        filters=filters if filters else None,
                        temperature=args.temperature
                    )
                    
                    # Display results
                    print("\n" + "-" * 60)
                    print("Answer:")
                    print("-" * 60)
                    print(result['answer'])
                    print("\n" + "-" * 60)
                    print("Sources:")
                    print("-" * 60)
                    for i, source in enumerate(result['sources'], 1):
                        if 'class' in source:
                            print(f"{i}. {source['class']} - {source['subject']} - "
                                  f"{source['bookname']} ({source['language']}), "
                                  f"Page {source['page_number']}")
                        else:
                            print(f"{i}. {source.get('source', 'Unknown')}")
                    
                except KeyboardInterrupt:
                    print("\nGoodbye!")
                    break
                except Exception as e:
                    logger.error(f"Error processing query: {e}")
                    print(f"Error: {e}")
        else:
            # Single query mode
            logger.info(f"Processing query: {args.query}")
            
            result = orchestrator.query(
                args.query,
                top_k=args.top_k,
                filters=filters if filters else None,
                temperature=args.temperature
            )
            
            # Display results
            print("\n" + "=" * 60)
            print("Answer:")
            print("=" * 60)
            print(result['answer'])
            print("\n" + "=" * 60)
            print("Sources:")
            print("=" * 60)
            for i, source in enumerate(result['sources'], 1):
                if 'class' in source:
                    print(f"{i}. {source['class']} - {source['subject']} - "
                          f"{source['bookname']} ({source['language']}), "
                          f"Page {source['page_number']}")
                else:
                    print(f"{i}. {source.get('source', 'Unknown')}")
        
        # Close database connection
        orchestrator.close()
        
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
