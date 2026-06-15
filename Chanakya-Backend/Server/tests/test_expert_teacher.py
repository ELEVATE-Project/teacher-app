"""
Test Expert Teacher Tool
=========================

Tests the expert teacher tool for topics beyond NCERT curriculum.
"""

import asyncio
import os
from dotenv import load_dotenv
from orchestrator.tools.expert_teacher import ExpertTeacherTool

# Load environment variables
load_dotenv()


async def test_expert_teacher():
    """Test expert teacher with various queries."""
    
    # Get API key from environment
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY environment variable not set")
        print("Please set it with: $env:GEMINI_API_KEY='your-api-key'")
        return
    
    # Initialize tool
    tool = ExpertTeacherTool(api_key=api_key)
    
    # Test queries
    queries = [
        "What is quantum mechanics?",
        "Explain artificial intelligence and machine learning",
        "What are fractals?",
        "How does blockchain technology work?",
        "Explain the theory of relativity in simple terms"
    ]
    
    contexts = [
        {"grade": "high school", "subject": "physics"},
        {"grade": "high school", "subject": "computer science"},
        {"grade": "middle school", "subject": "mathematics"},
        {"grade": "high school", "subject": "computer science"},
        {"grade": "high school", "subject": "physics"}
    ]
    
    print("=" * 80)
    print("EXPERT TEACHER TOOL TESTS")
    print("=" * 80)
    
    for query, context in zip(queries, contexts):
        print(f"\n\n{'=' * 80}")
        print(f"QUERY: {query}")
        print(f"CONTEXT: Grade={context['grade']}, Subject={context['subject']}")
        print("=" * 80)
        
        try:
            result = await tool.execute(query, context)
            
            print(f"\n📚 EXPLANATION:")
            print(f"{result.explanation}\n")
            
            print(f"🔑 KEY POINTS:")
            for i, point in enumerate(result.key_points, 1):
                print(f"  {i}. {point}")
            
            print(f"\n👨‍🏫 TEACHING TIPS:")
            for i, tip in enumerate(result.teaching_tips, 1):
                print(f"  {i}. {tip}")
            
            if result.examples:
                print(f"\n💡 EXAMPLES:")
                for i, example in enumerate(result.examples, 1):
                    print(f"  {i}. {example}")
            
            if result.common_misconceptions:
                print(f"\n⚠️ COMMON MISCONCEPTIONS:")
                for i, misconception in enumerate(result.common_misconceptions, 1):
                    print(f"  {i}. {misconception}")
            
            if result.follow_up_questions:
                print(f"\n❓ FOLLOW-UP QUESTIONS:")
                for i, question in enumerate(result.follow_up_questions, 1):
                    print(f"  {i}. {question}")
            
            print(f"\n✅ Confidence: {result.confidence}")
            print(f"✅ Validation: {tool.validate(result)}")
            
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_expert_teacher())
