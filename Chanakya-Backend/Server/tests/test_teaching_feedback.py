"""
Test Teaching Feedback Analyzer
================================

Tests the teaching feedback system with sample teaching transcripts.
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from teaching_feedback import TeachingFeedbackAnalyzer, TeachingSession
from teaching_feedback.storage import FeedbackStorage


async def test_teaching_feedback():
    """Test teaching feedback with different teaching scenarios."""
    
    # Load API key
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("[ERROR] GEMINI_API_KEY not found in environment")
        return
    
    print("\n" + "="*80)
    print("TEACHING FEEDBACK ANALYZER - TEST SUITE")
    print("="*80)
    
    # Create analyzer and storage
    analyzer = TeachingFeedbackAnalyzer(api_key=api_key)
    storage = FeedbackStorage(db_path="data/test_teaching_feedback.db")
    
    # Test scenarios
    test_cases = [
        {
            "name": "Good Fractions Lesson",
            "session": TeachingSession(
                transcript="""
                Today we will learn about fractions. A fraction is a part of a whole. 
                Let me show you with a roti. If I cut this roti into 4 equal pieces, 
                each piece is one-fourth or 1/4. The top number is called numerator, 
                it tells us how many pieces we take. The bottom number is denominator, 
                it tells us how many total pieces. Let's practice - if I have 3 pieces 
                out of 4, what fraction is that? Yes, 3/4! Now you try with your notebooks, 
                draw a circle and divide it into 2 parts. Color one part. What fraction 
                did you color? Very good! Remember, fractions help us share things equally.
                """,
                topic="fractions",
                grade_level="4",
                duration_minutes=15,
                language="en"
            )
        },
        {
            "name": "Weak Photosynthesis Lesson",
            "session": TeachingSession(
                transcript="""
                Photosynthesis is the process by which plants make their food. 
                Plants need sunlight, water and carbon dioxide. They use chlorophyll 
                which is green in color. The chemical formula is 6CO2 + 6H2O + light 
                energy = C6H12O6 + 6O2. This happens in the chloroplast. The light 
                dependent reactions happen first, then light independent reactions. 
                The products are glucose and oxygen. This is how plants survive. 
                Open your textbook to page 45 and copy the diagram.
                """,
                topic="photosynthesis",
                grade_level="7",
                duration_minutes=10,
                language="en"
            )
        },
        {
            "name": "Engaging Multiplication Lesson",
            "session": TeachingSession(
                transcript="""
                Namaste students! Today we learn 5 times table. See this 5 rupee coin? 
                If you have 1 coin, you have 5 rupees. If you have 2 coins, how much? 
                Let's count - 5, 10! Very good! So 5 times 2 is 10. Now if you have 
                3 coins? Count with me - 5, 10, 15. So 5 times 3 is 15. Let me show 
                you a trick - 5 times any number, the answer ends in 0 or 5. See? 
                5x1=5, 5x2=10, 5x3=15. Can you guess 5x4? Yes! 20! Now practice in 
                pairs - one student asks, other answers. I will give 1 point for each 
                correct answer. Let's see who becomes multiplication champion today!
                """,
                topic="multiplication tables",
                grade_level="3",
                duration_minutes=12,
                language="en"
            )
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{'='*80}")
        print(f"TEST {i}/{len(test_cases)}: {test['name']}")
        print(f"{'='*80}")
        print(f"Topic: {test['session'].topic}")
        print(f"Grade: {test['session'].grade_level}")
        print(f"Duration: {test['session'].duration_minutes} minutes")
        print(f"Transcript Preview: {test['session'].transcript[:100]}...")
        print("-" * 80)
        
        try:
            # Analyze teaching session
            feedback = await analyzer.analyze(test['session'])
            
            # Save to database
            teacher_id = f"teacher_{i}"
            storage.save_feedback(feedback, teacher_id=teacher_id)
            
            # Display results
            print(f"\n[OVERALL SCORE]: {feedback.overall_score:.2f}/1.0")
            
            print(f"\n[CONCEPT COVERAGE]:")
            print(f"  Depth Score: {feedback.concept_coverage.depth_score:.2f}")
            print(f"  Covered: {', '.join(feedback.concept_coverage.concepts_covered)}")
            if feedback.concept_coverage.concepts_missed:
                print(f"  Missed: {', '.join(feedback.concept_coverage.concepts_missed)}")
            
            print(f"\n[CLARITY]:")
            print(f"  Score: {feedback.clarity.clarity_score:.2f}")
            print(f"  Language Level: {feedback.clarity.language_level}")
            if feedback.clarity.strengths:
                print(f"  Strengths: {', '.join(feedback.clarity.strengths[:2])}")
            if feedback.clarity.confusing_parts:
                print(f"  Confusing Parts: {', '.join(feedback.clarity.confusing_parts[:2])}")
            
            print(f"\n[ENGAGEMENT]:")
            print(f"  Score: {feedback.engagement.engagement_score:.2f}")
            if feedback.engagement.techniques_used:
                print(f"  Techniques Used: {', '.join(feedback.engagement.techniques_used)}")
            if feedback.engagement.missed_opportunities:
                print(f"  Missed Opportunities: {', '.join(feedback.engagement.missed_opportunities[:2])}")
            
            print(f"\n[RURAL CONTEXT]:")
            print(f"  Appropriateness: {feedback.rural_context.rural_appropriateness:.2f}")
            print(f"  Resource Requirements: {feedback.rural_context.resource_requirements}")
            print(f"  Local Context Used: {'Yes' if feedback.rural_context.local_context_used else 'No'}")
            
            print(f"\n[KEY STRENGTHS]:")
            for strength in feedback.key_strengths:
                print(f"  + {strength}")
            
            print(f"\n[IMPROVEMENT AREAS]:")
            for area in feedback.improvement_areas:
                print(f"  - {area}")
            
            print(f"\n[ACTIONABLE TIPS]:")
            for tip in feedback.actionable_tips:
                print(f"  -> {tip}")
            
            if feedback.misconceptions_missed:
                print(f"\n[MISCONCEPTIONS TO ADDRESS NEXT TIME]:")
                for misc in feedback.misconceptions_missed:
                    print(f"  ! {misc}")
            
            print(f"\n[SUCCESS] Analysis complete!")
            
        except Exception as e:
            print(f"\n[ERROR] Test failed: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*80)
    print("ALL TESTS COMPLETED")
    print("="*80)
    
    # Test history retrieval
    print("\n" + "="*80)
    print("TESTING FEEDBACK HISTORY")
    print("="*80)
    
    history = storage.get_teacher_history("teacher_1", limit=5)
    print(f"\nTeacher: teacher_1")
    print(f"Total Sessions: {history.total_sessions}")
    print(f"Average Score: {history.average_score:.2f}")
    print(f"Improvement Trend: {history.improvement_trend}")


if __name__ == "__main__":
    asyncio.run(test_teaching_feedback())
