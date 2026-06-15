#!/usr/bin/env python3
"""
Simple example of how to query the RAG system programmatically
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from embedding.rag_orchestrator import RAGOrchestrator


def main():
    """Simple example of querying the RAG system"""
    
    # Check if API key is set
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        print("❌ Error: GEMINI_API_KEY not found!")
        print("\nPlease set your Gemini API key:")
        print("  1. Edit the .env file")
        print("  2. Add: GEMINI_API_KEY=your_api_key_here")
        print("  3. Get your API key from: https://makersuite.google.com/app/apikey")
        sys.exit(1)
    
    # Initialize the RAG orchestrator
    print("Initializing RAG system...")
    orchestrator = RAGOrchestrator(
        db_path="embedding/ncert_books.db",
        gemini_api_key=gemini_api_key
    )
    
    # Get database statistics
    stats = orchestrator.get_statistics()
    print(f"Database contains {stats['total_documents']} documents\n")
    
    # Example queries
    queries = [
        "What is photosynthesis?",
        "Explain the water cycle",
        "Who was Ashoka?",
    ]
    
    for query in queries:
        print("=" * 60)
        print(f"Question: {query}")
        print("=" * 60)
        
        # Query the RAG system
        result = orchestrator.query(
            query_text=query,
            top_k=5,  # Retrieve top 5 most relevant pages
            filters=None,  # No filters - search all books
            temperature=0.7  # Balanced creativity
        )
        
        # Display answer
        print("\nAnswer:")
        print("-" * 60)
        print(result['answer'])
        
        # Display sources
        print("\nSources:")
        print("-" * 60)
        for i, source in enumerate(result['sources'], 1):
            if 'class' in source:
                print(f"{i}. {source['class']} - {source['subject']} - "
                      f"{source['bookname']} ({source['language']}), "
                      f"Page {source['page_number']}")
            else:
                print(f"{i}. {source.get('source', 'Unknown')}")
        
        print("\n")
    
    # Close connection
    orchestrator.close()
    print("Done!")


if __name__ == "__main__":
    main()
