"""
Teaching Feedback Analyzer
===========================

Analyzes teaching sessions using Gemini and provides constructive feedback.
"""

import json
import re
import uuid
from typing import Optional
from datetime import datetime
from google import genai
from google.genai import types
import structlog

from .schemas import TeachingSession, TeachingFeedback, ConceptCoverage, ClarityAnalysis, EngagementAnalysis, RuralContextAnalysis


TEACHING_ANALYSIS_PROMPT = """You are an experienced educational coach specializing in RURAL Indian schools.

Your task is to analyze a teaching session transcript and provide constructive, actionable feedback.

=== ANALYSIS FRAMEWORK ===

Evaluate the teaching session on these dimensions:

1. CONCEPT COVERAGE (0-1 score)
   - Were core concepts for this topic/grade covered?
   - What important concepts were missed?
   - Was depth appropriate for grade level?

2. CLARITY (0-1 score)
   - Were explanations simple and clear?
   - Was language appropriate for rural students?
   - Were any parts confusing or too complex?

3. ENGAGEMENT (0-1 score)
   - Did teacher use questions to check understanding?
   - Were examples relatable and interesting?
   - Were students likely to stay engaged?

4. RURAL APPROPRIATENESS (0-1 score)
   - Did teacher use local/familiar contexts?
   - Were resource requirements practical (no expensive equipment)?
   - Was content culturally appropriate?

5. MISCONCEPTION PREVENTION
   - Were common student misconceptions addressed?
   - Which common confusions were not prevented?

=== FEEDBACK REQUIREMENTS ===
- Be CONSTRUCTIVE and encouraging - focus on growth
- Provide SPECIFIC examples from transcript
- Give ACTIONABLE tips (what to do differently next time)
- Keep rural context in mind - no unrealistic suggestions
- Balance strengths and improvement areas
- Focus on 3-5 key points (not overwhelming)

=== OUTPUT FORMAT ===
Return JSON with these exact keys:
- overall_score: float (0-1) - overall teaching effectiveness
- concepts_covered: array of strings - what was taught
- concepts_missed: array of strings - what should have been covered
- depth_score: float (0-1)
- clarity_score: float (0-1)
- strengths: array of strings - clear explanations observed
- confusing_parts: array of strings - potentially confusing sections
- language_level: string (too_simple, appropriate, too_complex)
- engagement_score: float (0-1)
- techniques_used: array of strings - engagement methods observed
- missed_opportunities: array of strings - where engagement could improve
- rural_appropriateness: float (0-1)
- resource_requirements: string (none, basic, advanced)
- local_context_used: boolean - used familiar examples?
- suggestions_for_rural: array of strings - rural-specific improvements
- key_strengths: array of 3-5 strings - top things done well
- improvement_areas: array of 3-5 strings - top areas to improve
- actionable_tips: array of 3-5 strings - specific next-time actions
- misconceptions_addressed: array of strings - confusions prevented
- misconceptions_missed: array of strings - confusions not addressed

=== TEACHING SESSION ===
Topic: {topic}
Grade Level: {grade_level}
Duration: {duration} minutes
Language: {language}

Transcript:
{transcript}

Analyze this teaching session and provide constructive feedback following the format above.
Return ONLY valid JSON, no other text.
"""


class TeachingFeedbackAnalyzer:
    """
    Analyzes teaching sessions and generates feedback.
    """
    
    def __init__(self, api_key: str):
        """Initialize with Google API key."""
        self.client = genai.Client(api_key=api_key)
        self.model_name = "models/gemini-2.5-flash"
        self.logger = structlog.get_logger("chanakya.teaching_feedback")
    
    async def analyze(self, session: TeachingSession) -> TeachingFeedback:
        """
        Analyze a teaching session and generate feedback.
        
        Args:
            session: TeachingSession with transcript and metadata
        
        Returns:
            TeachingFeedback with comprehensive analysis
        """
        session_id = session.session_id or str(uuid.uuid4())
        
        self.logger.info("analysis_start",
            session_id=session_id,
            topic=session.topic,
            grade=session.grade_level,
            transcript_length=len(session.transcript)
        )
        
        # Build prompt
        prompt = TEACHING_ANALYSIS_PROMPT.format(
            topic=session.topic,
            grade_level=session.grade_level,
            duration=session.duration_minutes or "unknown",
            language=session.language or "en",
            transcript=session.transcript
        )
        
        try:
            # Call Gemini
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.3,  # Lower for more consistent analysis
                    max_output_tokens=4000,
                    response_mime_type="application/json"
                )
            )
            
            # Parse response
            response_text = response.text.strip()
            response_text = re.sub(r'^```json\s*', '', response_text)
            response_text = re.sub(r'\s*```$', '', response_text)
            
            analysis = json.loads(response_text)
            
            # Build structured feedback
            feedback = TeachingFeedback(
                session_id=session_id,
                topic=session.topic,
                grade_level=session.grade_level,
                timestamp=datetime.now(),
                overall_score=analysis.get("overall_score", 0.7),
                concept_coverage=ConceptCoverage(
                    concepts_covered=analysis.get("concepts_covered", []),
                    concepts_missed=analysis.get("concepts_missed", []),
                    depth_score=analysis.get("depth_score", 0.7)
                ),
                clarity=ClarityAnalysis(
                    clarity_score=analysis.get("clarity_score", 0.7),
                    strengths=analysis.get("strengths", []),
                    confusing_parts=analysis.get("confusing_parts", []),
                    language_level=analysis.get("language_level", "appropriate")
                ),
                engagement=EngagementAnalysis(
                    engagement_score=analysis.get("engagement_score", 0.7),
                    techniques_used=analysis.get("techniques_used", []),
                    missed_opportunities=analysis.get("missed_opportunities", [])
                ),
                rural_context=RuralContextAnalysis(
                    rural_appropriateness=analysis.get("rural_appropriateness", 0.7),
                    resource_requirements=analysis.get("resource_requirements", "basic"),
                    local_context_used=analysis.get("local_context_used", False),
                    suggestions_for_rural=analysis.get("suggestions_for_rural", [])
                ),
                key_strengths=analysis.get("key_strengths", []),
                improvement_areas=analysis.get("improvement_areas", []),
                actionable_tips=analysis.get("actionable_tips", []),
                misconceptions_addressed=analysis.get("misconceptions_addressed", []),
                misconceptions_missed=analysis.get("misconceptions_missed", [])
            )
            
            self.logger.info("analysis_complete",
                session_id=session_id,
                overall_score=feedback.overall_score,
                concepts_covered=len(feedback.concept_coverage.concepts_covered),
                concepts_missed=len(feedback.concept_coverage.concepts_missed)
            )
            
            return feedback
            
        except json.JSONDecodeError as e:
            self.logger.error("json_parse_error",
                session_id=session_id,
                error=str(e)
            )
            # Return minimal feedback as fallback
            return self._generate_fallback_feedback(session, session_id)
        
        except Exception as e:
            self.logger.error("analysis_error",
                session_id=session_id,
                error=str(e),
                exc_info=True
            )
            raise
    
    def _generate_fallback_feedback(self, session: TeachingSession, session_id: str) -> TeachingFeedback:
        """Generate basic feedback when analysis fails."""
        return TeachingFeedback(
            session_id=session_id,
            topic=session.topic,
            grade_level=session.grade_level,
            timestamp=datetime.now(),
            overall_score=0.7,
            concept_coverage=ConceptCoverage(
                concepts_covered=["Unable to analyze - please try again"],
                concepts_missed=[],
                depth_score=0.7
            ),
            clarity=ClarityAnalysis(
                clarity_score=0.7,
                strengths=["Session recorded successfully"],
                confusing_parts=[],
                language_level="appropriate"
            ),
            engagement=EngagementAnalysis(
                engagement_score=0.7,
                techniques_used=[],
                missed_opportunities=[]
            ),
            rural_context=RuralContextAnalysis(
                rural_appropriateness=0.7,
                resource_requirements="unknown",
                local_context_used=False,
                suggestions_for_rural=[]
            ),
            key_strengths=["Your dedication to teaching"],
            improvement_areas=["Try recording again for detailed feedback"],
            actionable_tips=["Ensure clear audio quality", "Speak clearly during teaching"],
            misconceptions_addressed=[],
            misconceptions_missed=[]
        )
