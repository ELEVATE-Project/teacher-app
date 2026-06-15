"""
Chanakya Orchestrator
=====================

LangGraph-based orchestrator that handles context, understands queries,
and routes to appropriate tools.
"""

import json
import re
import time
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, TypedDict, List, AsyncIterator
from google import genai
from google.genai import types
from cachetools import LRUCache
import structlog

from .schemas import (
    OrchestratorInput,
    OrchestratorOutput,
    ActivityOutput,
    ConversationContext,
    ConversationMessage,
)
from .tools import ActivityGeneratorTool, CrisisHandlerTool, TeacherMotivationTool, ContentExplainerTool, ClassroomGuidanceTool, ExpertTeacherTool, GeneralConversationTool, QuickAnswerTool, ResourceFinderTool, FeedbackResponseTool


# LangGraph imports
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

# SQLite storage for conversations
from .storage import ConversationStorage

# Config
from .config import Config


# =============================================================================
# State Definition
# =============================================================================

class OrchestratorState(TypedDict):
    """Enhanced state that flows through the orchestrator graph."""
    
    # Input
    query: str
    context: Optional[dict]
    session_id: str
    
    messages: list  # Simple list of message dicts
    intent: Optional[str]
    selected_tool: Optional[str]
    tool_reasoning: Optional[str]
    confidence: float
    
    # Resource finder flag
    needs_resources: bool
    resource_topic: Optional[str]
    
    retry_count: int
    max_retries: int
    is_valid: bool
    validation_message: Optional[str]
    
    # Hallucination detection
    hallucination_score: float
    hallucination_check_count: int
    needs_hallucination_recheck: bool
    
    # Follow-up actions
    needs_follow_up: bool
    follow_up_action: Optional[str]
    
    needs_fallback: bool
    fallback_from_tool: Optional[str]
    fallback_count: int
    
    # Output
    tool_result: Optional[dict]
    resource_result: Optional[dict]  # Results from resource finder
    error: Optional[str]
    processing_time_ms: float


# =============================================================================
# Router Prompt
# =============================================================================

ROUTER_PROMPT = """You are Chanakya's intelligent router for a classroom support system.

Your job is to understand the teacher's query and decide which tool to use.

AVAILABLE TOOLS:
1. "general_conversation" - **[USE FOR NON-EDUCATIONAL QUERIES]** Use for:
   - Greetings (hi, hello, good morning, namaste)
   - Gratitude (thank you, thanks, appreciate it)
   - Unclear/ambiguous queries that need clarification (only when genuinely unclear)
   - Out-of-scope questions (weather, news, personal matters, non-teaching topics)
   - Small talk or casual conversation
   When the query is NOT about teaching, education, or classroom matters, use this tool.

2. "expert_teacher" - **[DEFAULT FOR EDUCATIONAL AND KNOWLEDGE QUERIES]** Use for:
   - ANY educational question, concept explanation, or teaching query
   - General knowledge questions (who is X, what is Y, explain Z)
   - Historical figures, scientists, political leaders, inventors
   - Science concepts, math concepts, geography, history
   - Current affairs related to education or knowledge
   - Definitions that need detailed explanation
   - Simple calculations and quick facts
   This is a knowledgeable expert teacher with broad subject knowledge that can answer both curriculum and non-curriculum topics. **When in doubt about any knowledge-based content, use this tool.**

3. "content_explainer" - Use ONLY when the teacher specifically mentions NCERT or specifically asks for textbook-based answers. This retrieves information from NCERT textbooks. If uncertain whether content is in NCERT, prefer expert_teacher instead.

4. "activity_generator" - Use when the teacher explicitly wants a hands-on activity, demonstration, or interactive exercise. Must include words like "activity", "game", "demonstration", "exercise".

5. "crisis_handler" - Use when there is an IMMEDIATE classroom management crisis: students making noise, losing focus, being disruptive, chaos, behavior problems. This tool provides instant solutions (under 2 minutes) to restore order and attention.

6. "teacher_motivation" - Use when the teacher is expressing feelings of burnout, stress, exhaustion, lack of motivation, feeling overwhelmed, or needing emotional support. This tool provides motivation, tips, and recovery strategies for teacher wellbeing.

7. "classroom_guidance" - Use when the teacher describes PEDAGOGICAL challenges, student learning difficulties, teaching strategy questions, or needs practical tips for daily classroom situations. Examples: "students can't interpret graphs", "only few students participate", "how to make lessons interactive", "students memorize but don't understand".

8. "feedback_response" - **[USE FOR TEACHER FEEDBACK]** Use when the teacher provides feedback about an activity, lesson, or teaching approach they tried. Examples:
   - "the activity was not good"
   - "students didn't like the activity"
   - "that worked great!"
   - "the lesson was confusing"
   - "students loved it"
   Keywords: "activity was", "lesson was", "students didn't like", "didn't work", "worked well", "loved it", "hated it", "not good", "feedback about"
   This tool responds to feedback and stores context for analysis.

9. "resource_finder" - **[USE ONLY WHEN EXPLICITLY REQUESTED]** Use ONLY when the teacher EXPLICITLY asks for:
   - YouTube videos or video tutorials (must contain words: "video", "youtube")
   - Web links or articles (must contain words: "link", "article", "website")
   - Additional resources or materials (must contain words: "resources", "materials", "find me")
   - Lesson plans or teaching materials
   - PDFs or downloadable content
   **CRITICAL**: Do NOT use this tool for general questions or explanations. Only use when the query explicitly requests external resources, links, videos, or articles.
   Keywords that MUST be present: "videos", "youtube", "links", "link", "resources", "materials", "pdf", "articles", "find me", "give me links", "show me videos"
   This tool searches the web using Tavily API and returns curated educational resources.

FUTURE TOOLS (not yet available, do NOT select these):
- "assessment_creator" - For creating quizzes/tests

ANALYZE THE QUERY AND RESPOND WITH JSON:
{
    "selected_tool": "general_conversation" or "expert_teacher" or "content_explainer" or "activity_generator" or "crisis_handler" or "teacher_motivation" or "classroom_guidance" or "feedback_response" or "resource_finder",
    "reasoning": "Brief explanation of why this tool was selected",
    "extracted_topic": "The main topic/concept OR crisis situation OR motivation issue OR teaching challenge OR feedback content OR conversation type",
    "confidence": 0.95,
    "needs_resources": true or false
}

Note: Set "needs_resources": true if the query ALSO asks for videos, links, or resources in addition to the main query. This will trigger resource_finder as a secondary tool.

EXAMPLES:

Query: "Hi"
Response: {"selected_tool": "general_conversation", "reasoning": "Simple greeting - needs friendly response", "extracted_topic": "greeting", "confidence": 0.99, "needs_resources": false}

Query: "Thank you so much!"
Response: {"selected_tool": "general_conversation", "reasoning": "Expression of gratitude", "extracted_topic": "gratitude", "confidence": 0.99}

Query: "What's the weather like today?"
Response: {"selected_tool": "general_conversation", "reasoning": "Out of scope - not related to teaching or education", "extracted_topic": "out_of_scope", "confidence": 0.98}

Query: "I need help"
Response: {"selected_tool": "general_conversation", "reasoning": "Unclear query - needs clarification on what kind of help", "extracted_topic": "clarification_needed", "confidence": 0.95}

Query: "What is photosynthesis?"
Response: {"selected_tool": "expert_teacher", "reasoning": "General educational question - expert teacher can provide comprehensive answer", "extracted_topic": "photosynthesis", "confidence": 0.97}

Query: "who is narendra modi"
Response: {"selected_tool": "expert_teacher", "reasoning": "General knowledge question about a person - expert teacher handles GK queries", "extracted_topic": "narendra modi", "confidence": 0.98}

Query: "who discovered gravity"
Response: {"selected_tool": "expert_teacher", "reasoning": "General knowledge question about historical figure and scientific discovery", "extracted_topic": "gravity discovery", "confidence": 0.97}

Query: "what is the capital of France"
Response: {"selected_tool": "expert_teacher", "reasoning": "General knowledge geography question", "extracted_topic": "capital of France", "confidence": 0.98}

Query: "Explain Pythagoras theorem to me"
Response: {"selected_tool": "expert_teacher", "reasoning": "Concept explanation request - expert teacher is best for clear explanations", "extracted_topic": "Pythagoras theorem", "confidence": 0.98}

Query: "What is quantum mechanics?"
Response: {"selected_tool": "expert_teacher", "reasoning": "Educational question requiring expert knowledge", "extracted_topic": "quantum mechanics", "confidence": 0.95}

Query: "Explain NCERT Chapter 5 on photosynthesis"
Response: {"selected_tool": "content_explainer", "reasoning": "Teacher specifically asked for NCERT textbook content", "extracted_topic": "photosynthesis", "confidence": 0.98}

Query: "Give me an activity for teaching addition with carry"
Response: {"selected_tool": "activity_generator", "reasoning": "Teacher explicitly asked for an activity", "extracted_topic": "addition with carry", "confidence": 0.98}

Query: "How can I teach fractions in a fun way?"
Response: {"selected_tool": "activity_generator", "reasoning": "Teacher wants an engaging activity method to teach", "extracted_topic": "fractions", "confidence": 0.95}

Query: "Students are making too much noise and not listening"
Response: {"selected_tool": "crisis_handler", "reasoning": "Immediate classroom management crisis - noise and attention problem", "extracted_topic": "noise control", "confidence": 0.98}

Query: "My class is completely out of control, everyone is talking"
Response: {"selected_tool": "crisis_handler", "reasoning": "Crisis situation - chaos and lack of control", "extracted_topic": "classroom chaos", "confidence": 0.97}

Query: "I'm feeling burnt out and don't want to teach anymore"
Response: {"selected_tool": "teacher_motivation", "reasoning": "Teacher expressing burnout and loss of motivation - needs emotional support", "extracted_topic": "burnout and exhaustion", "confidence": 0.97}

Query: "I feel like I'm failing as a teacher, nothing is working"
Response: {"selected_tool": "teacher_motivation", "reasoning": "Teacher expressing self-doubt and stress - needs encouragement", "extracted_topic": "self-doubt and discouragement", "confidence": 0.96, "needs_resources": false}

Query: "Students are unable to interpret maps and graphs systematically"
Response: {"selected_tool": "classroom_guidance", "reasoning": "Teacher describing a pedagogical challenge about student learning skills", "extracted_topic": "interpreting visual data", "confidence": 0.96, "needs_resources": false}

Query: "Only 2-3 students answer questions in class"
Response: {"selected_tool": "classroom_guidance", "reasoning": "Teacher describing student engagement issue needing teaching strategies", "extracted_topic": "low participation", "confidence": 0.97, "needs_resources": false}

Query: "How can I make my lessons more interactive?"
Response: {"selected_tool": "classroom_guidance", "reasoning": "Teacher asking for teaching strategy advice", "extracted_topic": "interactive teaching methods", "confidence": 0.95, "needs_resources": false}

Query: "The activity was not good"
Response: {"selected_tool": "feedback_response", "reasoning": "Teacher providing negative feedback about an activity", "extracted_topic": "activity feedback", "confidence": 0.98, "needs_resources": false}

Query: "Students didn't like the hands-on activity"
Response: {"selected_tool": "feedback_response", "reasoning": "Teacher giving feedback that students didn't like an activity", "extracted_topic": "activity feedback", "confidence": 0.97, "needs_resources": false}

Query: "That lesson worked great!"
Response: {"selected_tool": "feedback_response", "reasoning": "Teacher providing positive feedback about a lesson", "extracted_topic": "lesson feedback", "confidence": 0.98, "needs_resources": false}

Query: "The demonstration was confusing for students"
Response: {"selected_tool": "feedback_response", "reasoning": "Teacher providing feedback that demonstration was confusing", "extracted_topic": "demonstration feedback", "confidence": 0.96, "needs_resources": false}

Query: "Give me YouTube videos about photosynthesis"
Response: {"selected_tool": "resource_finder", "reasoning": "Teacher explicitly asking for YouTube videos on a topic", "extracted_topic": "photosynthesis", "confidence": 0.98, "needs_resources": true}

Query: "Find me resources and lesson plans for teaching fractions"
Response: {"selected_tool": "resource_finder", "reasoning": "Teacher asking for resources and lesson plan materials", "extracted_topic": "teaching fractions", "confidence": 0.97, "needs_resources": true}

Query: "Show me links and articles about water cycle"
Response: {"selected_tool": "resource_finder", "reasoning": "Teacher explicitly requesting links and articles", "extracted_topic": "water cycle", "confidence": 0.98, "needs_resources": true}

Query: "Explain photosynthesis and give me some videos and links"
Response: {"selected_tool": "expert_teacher", "reasoning": "Educational explanation needed, PLUS resources requested", "extracted_topic": "photosynthesis", "confidence": 0.95, "needs_resources": true}

Query: "What is gravity? Also share some YouTube tutorials"
Response: {"selected_tool": "expert_teacher", "reasoning": "Knowledge question that needs explanation, plus video resources requested", "extracted_topic": "gravity", "confidence": 0.96, "needs_resources": true}

Query: "Explain photosynthesis"
Response: {"selected_tool": "expert_teacher", "reasoning": "General explanation request - no resources explicitly requested", "extracted_topic": "photosynthesis", "confidence": 0.98, "needs_resources": false}

RULES:
- Return ONLY valid JSON
- **FIRST check if query is a greeting, gratitude, or truly unclear → use "general_conversation"**
- **DEFAULT to "expert_teacher" for ANY educational content or knowledge question (including GK, calculations, facts)**
- **Questions like "who is X", "what is Y", "explain Z", "2+2" → ALWAYS use "expert_teacher" NOT general_conversation**
- Use "content_explainer" ONLY when NCERT is specifically mentioned
- Use "activity_generator" ONLY when explicitly asking for activities/games
- Use "crisis_handler" for ANY immediate behavioral/attention crisis
- Use "teacher_motivation" for burnout, stress, lack of motivation, feeling overwhelmed
- Use "classroom_guidance" for pedagogical challenges, student learning difficulties, teaching strategies
- **Use "resource_finder" ONLY when explicitly asking for videos/links/articles/resources with keywords like: "videos", "youtube", "links", "articles", "find me", "show me", "give me links"**
- **Do NOT use "resource_finder" for general explanation requests - use "expert_teacher" instead**
- Set "needs_resources": true when query asks for videos, links, resources, materials IN ADDITION to an explanation
- Extract the topic/concept or crisis situation or motivation issue or teaching challenge or conversation type clearly
- Set confidence based on how clearly the query matches the tool's purpose"""


# =============================================================================
# Hallucination Detection Prompt
# =============================================================================

HALLUCINATION_DETECTION_PROMPT = """You are a quality assurance validator for educational content generated for teachers.

Your job is to detect hallucinations, fabrications, or unrealistic content in classroom activity descriptions.

EVALUATE THE ACTIVITY FOR:

1. **Realism & Feasibility** (0-1):
   - Can this activity be done in a typical classroom?
   - Are the materials actually available/practical?
   - Is the timing realistic?
   - Are the steps physically possible?

2. **Educational Soundness** (0-1):
   - Does the activity actually teach what it claims?
   - Are the learning outcomes realistic?
   - Is the difficulty appropriate?

3. **Logical Consistency** (0-1):
   - Do the steps make sense in order?
   - Are there contradictions?
   - Are prerequisites mentioned?

4. **Factual Accuracy** (0-1):
   - Are concepts explained correctly?
   - Are there mathematical/scientific errors?
   - Is the terminology appropriate?

RED FLAGS (hallucinations):
- Requiring materials that don't exist or are impractical
- Steps that contradict each other
- Activities that would take unrealistic time
- Dangerous or inappropriate suggestions
- Mathematical/scientific inaccuracies
- Activities that don't match the stated topic
- Overly complex instructions for stated grade level

RESPOND WITH JSON ONLY:
{
    "hallucination_score": 0.85,
    "realism_score": 0.9,
    "educational_score": 0.85,
    "logical_score": 0.8,
    "factual_score": 0.85,
    "issues_found": ["Minor issue description if any"],
    "is_acceptable": true,
    "recommendation": "Accept" or "Regenerate"
}

SCORING:
- 0.9-1.0: Excellent, realistic, high quality
- 0.7-0.89: Good, minor issues but acceptable
- 0.5-0.69: Problematic, contains hallucinations
- 0.0-0.49: Severe hallucinations, must regenerate

Return ONLY valid JSON."""


# =============================================================================
# Orchestrator Class
# =============================================================================

class ChanakyaOrchestrator:
    """
    LangGraph-based orchestrator for Chanakya classroom support system.
    
    Handles:
    - Context management across conversations
    - Query understanding and intent classification
    - Tool selection and execution
    """
    
    def __init__(self, api_key: str):
        """
        Initialize the orchestrator.
        
        Args:
            api_key: Google AI API key for Gemini
        """
        self.api_key = api_key
        self.client = genai.Client(api_key=api_key)
        self.model_name = Config.GEMINI_MODEL
        self.logger = structlog.get_logger("chanakya.orchestrator")
        
        # Initialize tools
        self.tools = {
            "activity_generator": ActivityGeneratorTool(api_key=api_key),
            "crisis_handler": CrisisHandlerTool(api_key=api_key),
            "teacher_motivation": TeacherMotivationTool(api_key=api_key),
            "content_explainer": ContentExplainerTool(),
            "classroom_guidance": ClassroomGuidanceTool(api_key=api_key),
            "expert_teacher": ExpertTeacherTool(api_key=api_key),
            "general_conversation": GeneralConversationTool(api_key=api_key),
            "quick_answer": QuickAnswerTool(api_key=api_key),
            "resource_finder": ResourceFinderTool(),
            "feedback_response": FeedbackResponseTool(api_key=api_key)
        }
        
        # Conversation contexts (LRU cache to prevent memory leaks)
        self.contexts: LRUCache = LRUCache(maxsize=1000)
        
        # SQLite storage for persistent conversation history
        if Config.db.use_sqlite:
            self.storage = ConversationStorage()
        else:
            self.storage = None
        
        # Build the LangGraph
        self.graph = self._build_graph()
    
    async def _detect_language(self, text: str) -> str:
        """
        Detect language of input text using character analysis first, then LLM.
        
        Returns: Full language name (e.g., 'English', 'Hindi', 'Tamil', 'Hinglish')
        """
        # Fast character-based detection for Devanagari scripts
        if any('\u0900' <= char <= '\u097F' for char in text):
            self.logger.info("language_detection", detected='Hindi', method='character_analysis')
            return 'Hindi'
        
        # Check for other Indic scripts
        if any('\u0A80' <= char <= '\u0AFF' for char in text):
            self.logger.info("language_detection", detected='Gujarati', method='character_analysis')
            return 'Gujarati'
        if any('\u0B00' <= char <= '\u0B7F' for char in text):
            self.logger.info("language_detection", detected='Tamil', method='character_analysis')
            return 'Tamil'
        if any('\u0C00' <= char <= '\u0C7F' for char in text):
            self.logger.info("language_detection", detected='Telugu', method='character_analysis')
            return 'Telugu'
        if any('\u0C80' <= char <= '\u0CFF' for char in text):
            self.logger.info("language_detection", detected='Kannada', method='character_analysis')
            return 'Kannada'
        if any('\u0980' <= char <= '\u09FF' for char in text):
            self.logger.info("language_detection", detected='Bengali', method='character_analysis')
            return 'Bengali'
        
        # Fallback to LLM for Hinglish/English detection
        try:
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=[
                    types.Content(
                        role="user",
                        parts=[types.Part(text=f"""Identify the language. Look for these patterns:

**Hinglish** (Hindi + English mix in Roman script):
- Contains Hindi words in Roman script: kya, hai, mein, ka, ko, se, ke, hota, hoti, kar, karo, etc.
- Examples: "kya hai", "explain karo", "photosynthesis kya hota hai", "mujhe batao"
- If you see words like: kya, hai, kaise, kahan, kab, kyun, mein - it's Hinglish

**English**: Pure English, no Hindi words

Text: "{text}"

Respond with ONLY ONE word: Hinglish or English

Language:""")]
                    )
                ],
                config=types.GenerateContentConfig(
                    temperature=0.0,
                    max_output_tokens=5,
                )
            )
            
            detected = response.text.strip().lower()
            # Map to full names
            lang_map = {
                'english': 'English',
                'hindi': 'Hindi',
                'tamil': 'Tamil',
                'bengali': 'Bengali',
                'telugu': 'Telugu',
                'gujarati': 'Gujarati',
                'marathi': 'Marathi',
                'kannada': 'Kannada',
                'malayalam': 'Malayalam',
                'hinglish': 'Hinglish'
            }
            
            for key, value in lang_map.items():
                if key in detected:
                    self.logger.info("language_detection", detected=value, method='llm')
                    return value
            
            # Default to English if uncertain
            self.logger.info("language_detection", detected='English', method='llm_default')
            return 'English'
            
        except Exception as e:
            self.logger.warning("language_detection_failed", error=str(e))
            return 'English'  # Default fallback
    
    async def _translate_text(self, text: str, target_lang: str) -> str:
        """
        Translate text to target language using Gemini.
        
        Args:
            text: Text to translate
            target_lang: Target language (full name like 'Hindi', 'Tamil', 'English')
        
        Returns:
            Translated text
        """
        # Skip translation for English
        if not text or target_lang.lower() in ['english', 'en']:
            return text
        
        try:
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=[
                    types.Content(
                        role="user",
                        parts=[types.Part(text=f"Translate this to {target_lang} (preserve formatting and structure, only translate the text content):\n\n{text}")]
                    )
                ],
                config=types.GenerateContentConfig(
                    temperature=0.3,
                    max_output_tokens=2048,
                )
            )
            
            return response.text.strip()
            
        except Exception as e:
            self.logger.warning("translation_failed",
                target_lang=target_lang,
                error=str(e)
            )
            return text  # Return original if translation fails
    
    async def _translate_dict_result(self, result: dict, target_lang: str, tool_name: str) -> dict:
        """
        Translate dictionary results from various tools to target language.
        
        Args:
            result: Tool result dictionary
            target_lang: Target language (e.g., 'Hindi', 'Tamil')
            tool_name: Name of the tool that generated this result
        
        Returns:
            Translated result dictionary
        """
        if target_lang.lower() in ['english', 'en']:
            return result
        
        self.logger.info("translating_dict_result",
            tool=tool_name,
            target_lang=target_lang
        )
        
        try:
            # General conversation tool
            if tool_name == "general_conversation":
                if "response" in result:
                    result["response"] = await self._translate_text(result["response"], target_lang)
                if "suggested_topics" in result and isinstance(result["suggested_topics"], list):
                    result["suggested_topics"] = [
                        await self._translate_text(topic, target_lang) 
                        for topic in result["suggested_topics"]
                    ]
            
            # Classroom guidance tool
            elif tool_name == "classroom_guidance":
                if "situation_analysis" in result:
                    result["situation_analysis"] = await self._translate_text(result["situation_analysis"], target_lang)
                if "immediate_tips" in result and isinstance(result["immediate_tips"], list):
                    result["immediate_tips"] = [
                        await self._translate_text(tip, target_lang) 
                        for tip in result["immediate_tips"]
                    ]
                if "step_by_step_strategies" in result and isinstance(result["step_by_step_strategies"], list):
                    for strategy in result["step_by_step_strategies"]:
                        if "strategy_name" in strategy:
                            strategy["strategy_name"] = await self._translate_text(strategy["strategy_name"], target_lang)
                        if "steps" in strategy and isinstance(strategy["steps"], list):
                            strategy["steps"] = [
                                await self._translate_text(step, target_lang) 
                                for step in strategy["steps"]
                            ]
                        if "why_it_works" in strategy:
                            strategy["why_it_works"] = await self._translate_text(strategy["why_it_works"], target_lang)
                if "long_term_approach" in result:
                    result["long_term_approach"] = await self._translate_text(result["long_term_approach"], target_lang)
                if "rural_adaptations" in result:
                    result["rural_adaptations"] = await self._translate_text(result["rural_adaptations"], target_lang)
                if "encouragement" in result:
                    result["encouragement"] = await self._translate_text(result["encouragement"], target_lang)
            
            # Expert teacher tool
            elif tool_name == "expert_teacher":
                if "explanation" in result:
                    result["explanation"] = await self._translate_text(result["explanation"], target_lang)
                if "key_points" in result and isinstance(result["key_points"], list):
                    result["key_points"] = [
                        await self._translate_text(point, target_lang) 
                        for point in result["key_points"]
                    ]
                if "examples" in result and isinstance(result["examples"], list):
                    result["examples"] = [
                        await self._translate_text(example, target_lang) 
                        for example in result["examples"]
                    ]
                if "teaching_tips" in result and isinstance(result["teaching_tips"], list):
                    result["teaching_tips"] = [
                        await self._translate_text(tip, target_lang) 
                        for tip in result["teaching_tips"]
                    ]
                if "common_misconceptions" in result and isinstance(result["common_misconceptions"], list):
                    result["common_misconceptions"] = [
                        await self._translate_text(misc, target_lang) 
                        for misc in result["common_misconceptions"]
                    ]
                if "follow_up_questions" in result and isinstance(result["follow_up_questions"], list):
                    result["follow_up_questions"] = [
                        await self._translate_text(q, target_lang) 
                        for q in result["follow_up_questions"]
                    ]
            
            # Content explainer tool
            elif tool_name == "content_explainer":
                if "explanation" in result:
                    result["explanation"] = await self._translate_text(result["explanation"], target_lang)
                if "key_points" in result and isinstance(result["key_points"], list):
                    result["key_points"] = [
                        await self._translate_text(point, target_lang) 
                        for point in result["key_points"]
                    ]
                if "examples" in result and isinstance(result["examples"], list):
                    result["examples"] = [
                        await self._translate_text(example, target_lang) 
                        for example in result["examples"]
                    ]
            
            # Teacher motivation tool
            elif tool_name == "teacher_motivation":
                if "motivation_title" in result:
                    result["motivation_title"] = await self._translate_text(result["motivation_title"], target_lang)
                if "acknowledgment" in result:
                    result["acknowledgment"] = await self._translate_text(result["acknowledgment"], target_lang)
                if "immediate_tips" in result and isinstance(result["immediate_tips"], list):
                    result["immediate_tips"] = [
                        await self._translate_text(tip, target_lang) 
                        for tip in result["immediate_tips"]
                    ]
                if "long_term_strategies" in result and isinstance(result["long_term_strategies"], list):
                    result["long_term_strategies"] = [
                        await self._translate_text(strategy, target_lang) 
                        for strategy in result["long_term_strategies"]
                    ]
                if "inspiration" in result:
                    result["inspiration"] = await self._translate_text(result["inspiration"], target_lang)
                if "self_care_reminder" in result:
                    result["self_care_reminder"] = await self._translate_text(result["self_care_reminder"], target_lang)
            
            # Crisis handler tool
            elif tool_name == "crisis_handler":
                if "crisis_analysis" in result:
                    result["crisis_analysis"] = await self._translate_text(result["crisis_analysis"], target_lang)
                if "immediate_steps" in result and isinstance(result["immediate_steps"], list):
                    result["immediate_steps"] = [
                        await self._translate_text(step, target_lang) 
                        for step in result["immediate_steps"]
                    ]
                if "de_escalation_phrases" in result and isinstance(result["de_escalation_phrases"], list):
                    result["de_escalation_phrases"] = [
                        await self._translate_text(phrase, target_lang) 
                        for phrase in result["de_escalation_phrases"]
                    ]
                if "prevention_strategies" in result and isinstance(result["prevention_strategies"], list):
                    result["prevention_strategies"] = [
                        await self._translate_text(strategy, target_lang) 
                        for strategy in result["prevention_strategies"]
                    ]
                if "followup_actions" in result and isinstance(result["followup_actions"], list):
                    result["followup_actions"] = [
                        await self._translate_text(action, target_lang) 
                        for action in result["followup_actions"]
                    ]
            
            return result
            
        except Exception as e:
            self.logger.error("dict_translation_failed",
                tool=tool_name,
                target_lang=target_lang,
                error=str(e)
            )
            return result  # Return original if translation fails
    
    
    def _build_graph(self) -> StateGraph:
        """Build the enhanced LangGraph workflow with conditional routing."""
        
        # Create the graph
        workflow = StateGraph(OrchestratorState)
        
        # Add nodes
        workflow.add_node("understand_query", self._understand_query_node)
        workflow.add_node("select_tool", self._select_tool_node)
        workflow.add_node("check_confidence", self._check_confidence_node)
        workflow.add_node("retry", self._retry_node)
        workflow.add_node("execute_tool", self._execute_tool_node)
        workflow.add_node("validate_output", self._validate_output_node)
        workflow.add_node("fallback", self._fallback_node)
        workflow.add_node("check_hallucination", self._check_hallucination_node)
        workflow.add_node("handle_follow_up", self._handle_follow_up_node)
        
        # Define edges
        workflow.set_entry_point("understand_query")
        workflow.add_edge("understand_query", "select_tool")
        workflow.add_edge("select_tool", "check_confidence")
        
        # Conditional routing based on confidence
        workflow.add_conditional_edges(
            "check_confidence",
            self._route_based_on_confidence,
            {
                "execute": "execute_tool",
                "retry": "retry",
                "end": END
            }
        )
        
        # Retry loops back to select_tool
        workflow.add_edge("retry", "select_tool")
        
        workflow.add_edge("execute_tool", "validate_output")
        
        # Conditional routing after validation - check for fallback
        workflow.add_conditional_edges(
            "validate_output",
            self._route_after_validation,
            {
                "fallback": "fallback",
                "check_hallucination": "check_hallucination",
            }
        )
        
        # Fallback goes to execute_tool with new tool selection
        workflow.add_edge("fallback", "execute_tool")
        
        # Conditional routing after hallucination check
        workflow.add_conditional_edges(
            "check_hallucination",
            self._route_after_hallucination_check,
            {
                "follow_up": "handle_follow_up",
                "retry": "retry",
                "end": END
            }
        )
        
        workflow.add_edge("handle_follow_up", END)
        
        # Return uncompiled workflow - we'll compile with checkpointer later
        return workflow
    
    async def _understand_query_node(self, state: OrchestratorState) -> dict:
        """
        Node: Understand and enrich the query with context.
        """
        query = state["query"]
        session_id = state["session_id"]
        
        # Get or create conversation context (LRU cached in-memory)
        if session_id not in self.contexts:
            self.contexts[session_id] = ConversationContext(session_id=session_id)
            
            # Load previous messages from SQLite if available
            if self.storage and await self.storage.session_exists(session_id):
                prev_messages = await self.storage.get_messages(session_id, limit=Config.MAX_CONTEXT_MESSAGES)
                for msg in prev_messages:
                    self.contexts[session_id].add_message(msg["role"], msg["content"])
        
        ctx = self.contexts[session_id]
        
        # Add user message to context
        ctx.add_message("user", query)
        
        # Save to SQLite storage
        if self.storage:
            try:
                message_id = await self.storage.add_message(session_id, "user", query)
                self.logger.info("user_message_saved", 
                    session_id=session_id, 
                    message_id=message_id)
            except Exception as e:
                self.logger.error("failed_to_save_user_message",
                    session_id=session_id,
                    error=str(e),
                    exc_info=True)
        
        # Check if summarization is needed
        if len(ctx.messages) > Config.SUMMARIZATION_THRESHOLD:
            await self._summarize_context(session_id)
        
        # Build context from previous messages for enrichment
        context_messages = []
        for msg in ctx.messages[-Config.MAX_CONTEXT_MESSAGES:]:
            context_messages.append({"role": msg.role, "content": msg.content})
        
        return {
            "messages": context_messages,
            "intent": None,  # Will be set by router
        }
    
    async def _select_tool_node(self, state: OrchestratorState) -> dict:
        """
        Node: Select the appropriate tool based on the query.
        Uses conversation context to understand follow-up queries.
        """
        query = state["query"]
        messages = state.get("messages", [])
        context = state.get("context", {})
        
        # Check if quick_answer_mode is enabled
        quick_answer_mode = context.get("quick_answer_mode", False)
        if quick_answer_mode:
            self.logger.info("quick_answer_mode_enabled", query=query)
            return {
                "selected_tool": "quick_answer",
                "tool_reasoning": "Quick Answer Mode enabled - forcing fast response",
                "intent": query,
                "confidence": 1.0,
            }
        
        # Build context string from previous messages
        context_str = ""
        if len(messages) > 1:
            context_str = "Previous conversation:\n"
            for msg in messages[:-1]:  # All except current
                context_str += f"{msg['role']}: {msg['content']}\n"
            context_str += "\nCurrent query: "
        
        try:
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=[
                    types.Content(
                        role="user",
                        parts=[types.Part(text=f"{context_str}Route this teacher query: {query}")]
                    )
                ],
                config=types.GenerateContentConfig(
                    system_instruction=ROUTER_PROMPT,
                    temperature=0.1,
                    max_output_tokens=Config.MAX_OUTPUT_TOKENS,
                    response_mime_type="application/json"
                )
            )
            
            # Parse response
            text = response.text.strip()
            
            # Check if response is empty
            if not text:
                self.logger.warning("router_empty_response", query=query)
                return {
                    "selected_tool": "activity_generator",
                    "tool_reasoning": "Default selection (empty router response)",
                    "intent": query,
                    "confidence": 0.5,
                }
            
            # Robust JSON extraction using regex
            # Try to find JSON object in response
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text, re.DOTALL)
            
            if not json_match:
                # Fallback: clean up markdown code blocks
                if text.startswith("```json"):
                    text = text[7:]
                if text.startswith("```"):
                    text = text[3:]
                if text.endswith("```"):
                    text = text[:-3]
                text = text.strip()
            else:
                text = json_match.group()
            
            # Try to parse JSON
            try:
                parsed = json.loads(text)
                
                self.logger.info("router_success",
                    tool=parsed.get("selected_tool"),
                    confidence=parsed.get("confidence"),
                    query=query[:50]
                )
                
            except json.JSONDecodeError as e:
                self.logger.warning("router_json_parse_error",
                    query=query[:50],
                    error=str(e),
                    response_text=text[:200]
                )
                return {
                    "selected_tool": "activity_generator",
                    "tool_reasoning": "Default selection (invalid JSON response)",
                    "intent": query,
                    "confidence": 0.5,
                }
            
            return {
                "selected_tool": parsed.get("selected_tool", "activity_generator"),
                "tool_reasoning": parsed.get("reasoning", "Default selection"),
                "intent": parsed.get("extracted_topic", query),
                "confidence": float(parsed.get("confidence", 0.8)),
                "needs_resources": parsed.get("needs_resources", False),
                "resource_topic": parsed.get("extracted_topic", query) if parsed.get("needs_resources") else None,
            }
            
        except Exception:
            # Default to activity generator on error
            return {
                "selected_tool": "activity_generator",
                "tool_reasoning": "Default selection (router error)",
                "intent": query,
                "confidence": 0.5,
                "needs_resources": False,
                "resource_topic": None,
            }
    
    async def _detect_hallucination(self, activity_output: dict, query: str) -> dict:
        """
        Detect hallucinations in generated activity using Gemini.
        
        Args:
            activity_output: The generated activity to validate
            query: Original user query for context
        
        Returns:
            Dict with hallucination_score and validation details
        """
        try:
            # Format activity for validation
            activity_text = f"""
ORIGINAL QUERY: {query}

GENERATED ACTIVITY:
Activity Name: {activity_output.get('activity_name', 'N/A')}
Description: {activity_output.get('description', 'N/A')}
Duration: {activity_output.get('duration_minutes', 'N/A')} minutes
Materials: {', '.join(activity_output.get('materials_needed', []))}
Grade Level: {activity_output.get('grade_level', 'N/A')}

STEPS:
{chr(10).join(f"{i+1}. {step}" for i, step in enumerate(activity_output.get('steps', [])))}

LEARNING OUTCOME: {activity_output.get('learning_outcome', 'N/A')}

TIPS: {', '.join(activity_output.get('tips', [])) if activity_output.get('tips') else 'None'}
"""
            
            # Call Gemini for hallucination detection
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=[
                    types.Content(
                        role="user",
                        parts=[types.Part(text=f"Validate this activity:\n\n{activity_text}")]
                    )
                ],
                config=types.GenerateContentConfig(
                    system_instruction=HALLUCINATION_DETECTION_PROMPT,
                    temperature=0.1,
                    max_output_tokens=10000,
                    response_mime_type="application/json"
                )
            )
            
            # Check if response was truncated
            if hasattr(response, 'candidates') and response.candidates:
                finish_reason = response.candidates[0].finish_reason
                if finish_reason != 1:  # 1 = STOP (normal completion)
                    self.logger.warning("gemini_incomplete_response", 
                        finish_reason=finish_reason,
                        text_length=len(response.text))
            
            # Parse validation response
            text = response.text.strip()
            
            # Robust JSON extraction - remove markdown code blocks
            text = re.sub(r'```(?:json)?\s*|\s*```', '', text)
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text, re.DOTALL)
            if json_match:
                text = json_match.group()
            
            # Try parsing as-is first
            try:
                validation_result = json.loads(text)
            except json.JSONDecodeError as first_error:
                # Gemini sometimes returns JSON with unquoted keys or trailing commas
                # Fix common issues:
                try:
                    # 1. Add quotes around unquoted property names (at start, after {, or after ,)
                    text = re.sub(r'([,\{]\s*)(\w+)(\s*):', r'\1"\2"\3:', text)
                    # 2. Remove trailing commas before closing braces/brackets  
                    text = re.sub(r',(\s*[}\]])', r'\1', text)
                    validation_result = json.loads(text)
                except json.JSONDecodeError:
                    # If still failing, save to file for debugging and re-raise
                    with open("gemini_json_error.txt", "w") as f:
                        f.write(f"Error: {first_error}\n\n")
                        f.write(f"Raw response:\n{response.text}\n\n")
                        f.write(f"After regex extraction:\n{text}")
                    raise first_error
            
            self.logger.info("hallucination_check",
                score=validation_result.get("hallucination_score"),
                is_acceptable=validation_result.get("is_acceptable"),
                issues=len(validation_result.get("issues_found", []))
            )
            
            return {
                "hallucination_score": float(validation_result.get("hallucination_score", 0.5)),
                "is_acceptable": validation_result.get("is_acceptable", False),
                "issues_found": validation_result.get("issues_found", []),
                "recommendation": validation_result.get("recommendation", "Regenerate"),
                "detailed_scores": {
                    "realism": validation_result.get("realism_score", 0.5),
                    "educational": validation_result.get("educational_score", 0.5),
                    "logical": validation_result.get("logical_score", 0.5),
                    "factual": validation_result.get("factual_score", 0.5)
                }
            }
            
        except Exception as e:
            self.logger.error("hallucination_check_error",
                error=str(e),
                exc_info=True
            )
            # Default to accepting if validation fails (fail open)
            return {
                "hallucination_score": 0.75,
                "is_acceptable": True,
                "issues_found": ["Validation check failed"],
                "recommendation": "Accept",
                "detailed_scores": {}
            }
    
    async def _summarize_context(self, session_id: str) -> None:
        """
        Summarize older messages in the conversation when it gets too long.
        Keeps recent messages and replaces older ones with a summary.
        """
        ctx = self.contexts.get(session_id)
        if not ctx or len(ctx.messages) <= Config.SUMMARIZATION_THRESHOLD:
            return
        
        # Split messages: older to summarize vs recent to keep
        split_point = len(ctx.messages) - Config.SUMMARIZATION_KEEP_RECENT
        older_messages = ctx.messages[:split_point]
        recent_messages = ctx.messages[split_point:]
        
        # Build conversation text for summarization
        conversation_text = "\n".join([
            f"{msg.role}: {msg.content}" for msg in older_messages
        ])
        
        try:
            # Call Gemini to summarize
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=[
                    types.Content(
                        role="user",
                        parts=[types.Part(text=f"Summarize this teacher-student conversation concisely, preserving key topics and context:\n\n{conversation_text}")]
                    )
                ],
                config=types.GenerateContentConfig(
                    temperature=0.3,
                    max_output_tokens=500,
                )
            )
            
            summary = response.text.strip()
            
            # Replace older messages with summary
            ctx.messages = [
                ConversationMessage(
                    role="system",
                    content=f"[Previous conversation summary: {summary}]",
                    timestamp=older_messages[0].timestamp
                )
            ] + recent_messages
            
        except Exception:
            # If summarization fails, just keep recent messages
            ctx.messages = recent_messages
    
    async def _check_confidence_node(self, state: OrchestratorState) -> dict:
        """
        Node: Check confidence and set retry tracking.
        """
        retry_count = state.get("retry_count", 0)
        return {
            "retry_count": retry_count,
            "max_retries": 2,
        }
    
    async def _retry_node(self, state: OrchestratorState) -> dict:
        """
        Node: Handle retry by incrementing retry count.
        """
        retry_count = state.get("retry_count", 0)
        return {
            "retry_count": retry_count + 1,
        }
    
    async def _fallback_node(self, state: OrchestratorState) -> dict:
        """
        Node: Handle fallback from content_explainer to expert_teacher.
        """
        self.logger.info("executing_fallback", 
            from_tool="content_explainer",
            to_tool="expert_teacher"
        )
        
        # Override tool selection
        return {
            "selected_tool": "expert_teacher",
            "tool_reasoning": "Fallback from RAG - content not found in NCERT",
            "needs_fallback": False,
        }
    
    def _route_after_validation(self, state: OrchestratorState) -> str:
        """
        Route after validation: check if fallback is needed.
        """
        needs_fallback = state.get("needs_fallback", False)
        fallback_from_tool = state.get("fallback_from_tool")
        
        # If RAG failed, fallback to expert_teacher
        if needs_fallback and fallback_from_tool == "content_explainer":
            self.logger.info("routing_to_fallback", 
                from_tool="content_explainer",
                to_tool="expert_teacher"
            )
            return "fallback"
        
        # Otherwise proceed to hallucination check
        return "check_hallucination"
    
    def _route_based_on_confidence(self, state: OrchestratorState) -> str:
        """
        Conditional routing: Check if confidence is high enough.
        """
        confidence = state.get("confidence", 0.8)
        retry_count = state.get("retry_count", 0)
        max_retries = state.get("max_retries", 2)
        
        # If too many retries, give up and execute anyway
        if retry_count >= max_retries:
            return "end"
        
        # If confidence is too low, retry with modified query
        if confidence < 0.6:
            return "retry"
        
        # Normal execution
        return "execute"
    
    async def _execute_tool_node(self, state: OrchestratorState) -> dict:
        """
        Node: Execute the selected tool.
        Also fetches resources if needs_resources is True.
        """
        tool_name = state["selected_tool"]
        topic = state["intent"] or state["query"]
        context = state.get("context") or {}
        needs_resources = state.get("needs_resources", False)
        resource_topic = state.get("resource_topic") or topic
        
        # Add recent messages to context for feedback tool
        if tool_name == "feedback_response":
            messages = state.get("messages", [])
            context["recent_messages"] = messages[-3:] if len(messages) >= 3 else messages
        
        if tool_name not in self.tools:
            self.logger.error("unknown_tool", tool_name=tool_name)
            return {
                "tool_result": None,
                "resource_result": None,
                "error": f"Unknown tool: {tool_name}"
            }
        
        try:
            tool = self.tools[tool_name]
            
            self.logger.info("tool_execution_start",
                tool=tool_name,
                topic=topic[:50] if topic else None,
                needs_resources=needs_resources
            )
            
            result = await tool.run(topic, context)
            
            self.logger.info("tool_execution_success",
                tool=tool_name,
                has_result=result is not None
            )
            
            # Convert to dict for storage - handle both Pydantic models and dicts
            if hasattr(result, 'model_dump'):
                result_dict = result.model_dump()
            elif isinstance(result, dict):
                result_dict = result
            else:
                result_dict = {"output": str(result)}
            
            # Store feedback context if this is a feedback response
            if tool_name == "feedback_response" and self.storage:
                try:
                    session_id = state.get("session_id")
                    messages = state.get("messages", [])
                    
                    # Get sentiment and response from result
                    sentiment = result_dict.get("sentiment", "unclear")
                    response_text = result_dict.get("response", "")
                    
                    # Store feedback with last 3 messages
                    await self.storage.store_feedback_context(
                        session_id=session_id,
                        feedback_content=topic,
                        recent_messages=messages,
                        sentiment=sentiment,
                        response=response_text
                    )
                    
                    self.logger.info("feedback_context_stored",
                        session_id=session_id,
                        sentiment=sentiment,
                        message_count=len(messages)
                    )
                except Exception as e:
                    self.logger.warning("feedback_storage_failed", error=str(e))
            
            # Fetch resources if needed (and not already using resource_finder)
            resource_result = None
            if needs_resources and tool_name != "resource_finder" and "resource_finder" in self.tools:
                try:
                    self.logger.info("fetching_additional_resources", topic=resource_topic)
                    resource_finder = self.tools["resource_finder"]
                    resource_result = await resource_finder.run(resource_topic, context)
                    
                    # Convert to dict if needed
                    if hasattr(resource_result, 'model_dump'):
                        resource_result = resource_result.model_dump()
                    
                    self.logger.info("resources_fetched_successfully",
                        total_results=resource_result.get("total_results", 0) if resource_result else 0
                    )
                except Exception as e:
                    self.logger.warning("resource_fetch_failed", error=str(e))
                    resource_result = None
            
            return {
                "tool_result": result_dict,
                "resource_result": resource_result,
                "error": None
            }
            
        except Exception as e:
            self.logger.error("tool_execution_error",
                tool=tool_name,
                error=str(e),
                exc_info=True
            )
            return {
                "tool_result": None,
                "resource_result": None,
                "error": str(e)
            }
    
    async def _validate_output_node(self, state: OrchestratorState) -> dict:
        """
        Node: Validate the tool output and check if follow-up is needed.
        """
        tool_result = state.get("tool_result")
        error = state.get("error")
        selected_tool = state.get("selected_tool")
        
        # If there's an error, mark as invalid
        if error:
            return {
                "is_valid": False,
                "validation_message": f"Tool execution failed: {error}",
                "needs_follow_up": False,
            }
        
        # If no result, mark as invalid
        if not tool_result:
            return {
                "is_valid": False,
                "validation_message": "Tool returned no result",
                "needs_follow_up": False,
            }
        
        # Basic validation: check if result has expected structure
        is_valid = True
        validation_message = "Output validated successfully"
        needs_follow_up = False
        follow_up_action = None
        needs_fallback = False
        fallback_from_tool = None
        
        # Check if content_explainer failed to find content - trigger fallback to expert_teacher
        fallback_count = state.get("fallback_count", 0)
        if selected_tool == "content_explainer" and fallback_count < 1:
            confidence = tool_result.get("confidence", 1.0)
            coverage = tool_result.get("coverage", "")
            retrieved_passages = tool_result.get("retrieved_passages", 0)
            
            # If RAG couldn't find good content, fallback to expert_teacher
            if (confidence < 0.4 or 
                coverage == "insufficient" or 
                retrieved_passages == 0):
                self.logger.info("rag_fallback_triggered",
                    confidence=confidence,
                    coverage=coverage,
                    retrieved_passages=retrieved_passages
                )
                needs_fallback = True
                fallback_from_tool = "content_explainer"
                is_valid = False  # Mark as invalid to trigger fallback
                validation_message = "RAG found insufficient content - falling back to expert teacher"
        
        # Crisis handler follow-up: after managing crisis, suggest activity
        if selected_tool == "crisis_handler":
            needs_follow_up = True
            follow_up_action = {
                "tool": "activity_generator",
                "reason": "Suggest calming activity after crisis intervention"
            }
        
        return {
            "is_valid": is_valid,
            "validation_message": validation_message,
            "needs_follow_up": needs_follow_up,
            "follow_up_action": follow_up_action,
            "needs_fallback": needs_fallback,
            "fallback_from_tool": fallback_from_tool,
            "fallback_count": fallback_count + 1 if needs_fallback else fallback_count,
        }
    
    async def _check_hallucination_node(self, state: OrchestratorState) -> dict:
        """
        Node: Check for hallucinations in the generated output.
        Smart skipping: Only validates 15% of queries (complex/risky activities).
        """
        tool_result = state.get("tool_result")
        query = state["query"]
        selected_tool = state.get("selected_tool")
        hallucination_check_count = state.get("hallucination_check_count", 0)
        
        # Only check activity_generator outputs
        if selected_tool != "activity_generator" or not tool_result:
            return {
                "hallucination_score": 1.0,
                "hallucination_check_count": 0,
                "needs_hallucination_recheck": False
            }
        
        # Smart skip logic - Skip 85% of simple activities
        should_skip = self._should_skip_hallucination_check(tool_result, query)
        if should_skip:
            self.logger.info("hallucination_check_skipped",
                reason="simple_activity",
                query_preview=query[:50]
            )
            return {
                "hallucination_score": 1.0,  # Assume safe
                "hallucination_check_count": 0,
                "needs_hallucination_recheck": False
            }
        
        # Run hallucination detection for complex activities
        validation = await self._detect_hallucination(tool_result, query)
        
        score = validation["hallucination_score"]
        is_acceptable = score >= Config.HALLUCINATION_THRESHOLD
        
        self.logger.info("hallucination_validation",
            score=score,
            is_acceptable=is_acceptable,
            check_count=hallucination_check_count + 1,
            issues=len(validation.get("issues_found", []))
        )
        
        return {
            "hallucination_score": score,
            "hallucination_check_count": hallucination_check_count + 1,
            "needs_hallucination_recheck": not is_acceptable,
            "validation_message": f"Hallucination score: {score:.2f} - {validation['recommendation']}"
        }
    
    def _should_skip_hallucination_check(self, activity_output, query: str) -> bool:
        """
        Heuristic to determine if hallucination check can be skipped.
        
        Simple rule: Skip if activity has less than 8 steps.
        Activities with 8+ steps are validated for hallucinations.
        """
        # Extract step count from activity output
        if hasattr(activity_output, 'steps'):
            step_count = len(activity_output.steps) if activity_output.steps else 0
            
            # Skip validation if less than 8 steps
            if step_count < 8:
                self.logger.info("hallucination_skip_decision",
                    step_count=step_count,
                    threshold=8,
                    skipped=True
                )
                return True
            else:
                self.logger.info("hallucination_skip_decision",
                    step_count=step_count,
                    threshold=8,
                    skipped=False
                )
                return False
        
        # Default: Skip if step count unavailable (assume simple activity)
        return True
    
    def _route_after_hallucination_check(self, state: OrchestratorState) -> str:
        """
        Conditional routing: After hallucination check, decide next step.
        """
        needs_recheck = state.get("needs_hallucination_recheck", False)
        hallucination_check_count = state.get("hallucination_check_count", 0)
        needs_follow_up = state.get("needs_follow_up", False)
        
        # If hallucination detected and checks left, retry
        if needs_recheck and hallucination_check_count < Config.MAX_HALLUCINATION_CHECKS:
            self.logger.warning("hallucination_retry",
                check_count=hallucination_check_count,
                score=state.get("hallucination_score")
            )
            return "retry"
        
        # If needs follow-up, handle it
        if needs_follow_up:
            return "follow_up"
        
        # Otherwise, end (accept result even if low score after max checks)
        if needs_recheck:
            self.logger.warning("hallucination_accepted_after_max_retries",
                score=state.get("hallucination_score"),
                check_count=hallucination_check_count
            )
        
        return "end"
    
    async def _handle_follow_up_node(self, state: OrchestratorState) -> dict:
        """
        Node: Handle follow-up actions (e.g., crisis → activity).
        """
        follow_up_action = state.get("follow_up_action")
        
        if not follow_up_action:
            return {}
        
        try:
            # Execute the follow-up tool
            tool_name = follow_up_action.get("tool")
            if tool_name in self.tools:
                tool = self.tools[tool_name]
                # Use the original query for context
                result = await tool.run(state["query"], state.get("context"))
                
                # Store as follow-up result
                return {
                    "follow_up_result": result.model_dump(),
                }
        except Exception as e:
            return {
                "follow_up_result": {"error": str(e)}
            }
        
        return {}
    
    async def process(self, input_data: OrchestratorInput) -> OrchestratorOutput:
        """
        Process a query through the orchestrator.
        
        Args:
            input_data: The orchestrator input
        
        Returns:
            OrchestratorOutput with the tool result
        """
        start_time = time.time()
        
        # Create session ID if not provided
        session_id = input_data.session_id or str(uuid.uuid4())
        
        self.logger.info("process_start",
            session_id=session_id,
            query=input_data.query[:100]
        )
        
        # Detect input language using LLM
        detected_lang = await self._detect_language(input_data.query)
        
        self.logger.info("language_detected",
            session_id=session_id,
            language=detected_lang
        )
        
        # Store detected language in context for tools to use
        if input_data.context is None:
            input_data.context = {}
        input_data.context['detected_language'] = detected_lang
        
        # Store quick_answer_mode flag in context
        if input_data.quick_answer_mode:
            input_data.context['quick_answer_mode'] = True
        
        # Initial state
        initial_state: OrchestratorState = {
            "query": input_data.query,
            "context": input_data.context,
            "session_id": session_id,
            "messages": [],
            "intent": None,
            "selected_tool": None,
            "tool_reasoning": None,
            "tool_result": None,
            "error": None,
            "confidence": 0.0,
            "retry_count": 0,
            "max_retries": 2,
            "is_valid": True,
            "validation_message": None,
            "hallucination_score": 1.0,
            "hallucination_check_count": 0,
            "needs_hallucination_recheck": False,
            "needs_follow_up": False,
            "follow_up_action": None,
            "processing_time_ms": 0.0,
        }
        
        try:
            # Run the graph with config for checkpointing
            config = {"configurable": {"thread_id": session_id}}
            
            # Use in-memory checkpointer for LangGraph state
            compiled_graph = self.graph.compile(checkpointer=MemorySaver())
            final_state = await compiled_graph.ainvoke(initial_state, config=config)
            
            processing_time_ms = (time.time() - start_time) * 1000
            
            # Build output
            if final_state.get("error"):
                return OrchestratorOutput(
                    tool_used=final_state.get("selected_tool", "none"),
                    reasoning=final_state.get("tool_reasoning", ""),
                    result={},
                    confidence=final_state.get("confidence", 0.0),
                    processing_time_ms=processing_time_ms,
                    error=final_state["error"]
                )
            
            # Parse result based on tool
            result = final_state.get("tool_result")
            
            # If no result, return empty response
            if not result:
                return OrchestratorOutput(
                    tool_used=final_state.get("selected_tool", "none"),
                    reasoning=final_state.get("tool_reasoning", "No result generated"),
                    result={},
                    confidence=final_state.get("confidence", 0.0),
                    processing_time_ms=processing_time_ms,
                    error="No result generated by tool"
                )
            
            # Add follow-up result if present
            follow_up_result = final_state.get("follow_up_result")
            if follow_up_result:
                result["follow_up"] = follow_up_result
            
            # Add resource results if present
            resource_result = final_state.get("resource_result")
            if resource_result and resource_result.get("total_results", 0) > 0:
                result["resources"] = resource_result
            
            if final_state.get("selected_tool") == "activity_generator":
                result = ActivityOutput(**result)
            
            # Translate result to original language if needed
            tool_name = final_state.get("selected_tool", "unknown")
            if detected_lang != 'English':
                self.logger.info("translating_result",
                    session_id=session_id,
                    target_lang=detected_lang,
                    tool=tool_name
                )
                
                # Handle ActivityOutput (from activity_generator, crisis_handler, etc.)
                if isinstance(result, ActivityOutput):
                    # Translate activity fields
                    result.activity_name = await self._translate_text(result.activity_name, detected_lang)
                    result.description = await self._translate_text(result.description, detected_lang)
                    result.learning_outcome = await self._translate_text(result.learning_outcome, detected_lang)
                    
                    # Translate steps
                    translated_steps = []
                    for step in result.steps:
                        translated_steps.append(await self._translate_text(step, detected_lang))
                    result.steps = translated_steps
                    
                    # Translate materials
                    translated_materials = []
                    for material in result.materials_needed:
                        translated_materials.append(await self._translate_text(material, detected_lang))
                    result.materials_needed = translated_materials
                    
                    # Translate tips if present
                    if result.tips:
                        translated_tips = []
                        for tip in result.tips:
                            translated_tips.append(await self._translate_text(tip, detected_lang))
                        result.tips = translated_tips
                
                # Handle dict-based results (other tools)
                elif isinstance(result, dict):
                    result = await self._translate_dict_result(result, detected_lang, tool_name)
            
            # Update conversation context and save to SQLite
            assistant_message = f"Generated activity: {result.activity_name if isinstance(result, ActivityOutput) else 'Response'}"
            
            if session_id in self.contexts:
                self.contexts[session_id].add_message("assistant", assistant_message)
            
            # Save assistant message to SQLite with full metadata
            if self.storage:
                try:
                    # Prepare metadata with full response data
                    # Serialize result properly based on type
                    if hasattr(result, 'model_dump'):
                        result_data = result.model_dump()
                    elif hasattr(result, 'dict'):
                        result_data = result.dict()
                    elif isinstance(result, dict):
                        result_data = result
                    else:
                        result_data = {"data": str(result)}
                    
                    metadata = {
                        "tool_used": final_state.get("selected_tool", "activity_generator"),
                        "reasoning": final_state.get("tool_reasoning", ""),
                        "confidence": final_state.get("confidence", 0.0),
                        "result": result_data,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    message_id = await self.storage.add_message(session_id, "assistant", assistant_message, metadata=metadata)
                    self.logger.info("assistant_message_saved", 
                        session_id=session_id, 
                        message_id=message_id,
                        has_metadata=bool(metadata))
                except Exception as e:
                    self.logger.error("failed_to_save_assistant_message",
                        session_id=session_id,
                        error=str(e),
                        exc_info=True)
            
            self.logger.info("process_complete",
                session_id=session_id,
                tool=final_state.get("selected_tool"),
                confidence=final_state.get("confidence"),
                processing_time_ms=processing_time_ms,
                has_follow_up=follow_up_result is not None
            )
            
            return OrchestratorOutput(
                tool_used=final_state.get("selected_tool", "activity_generator"),
                reasoning=final_state.get("tool_reasoning", ""),
                result=result,
                confidence=final_state.get("confidence", 0.8),
                processing_time_ms=processing_time_ms,
                error=None
            )
            
        except Exception as e:
            processing_time_ms = (time.time() - start_time) * 1000
            
            self.logger.error("process_error",
                session_id=session_id,
                error=str(e),
                processing_time_ms=processing_time_ms,
                exc_info=True
            )
            
            return OrchestratorOutput(
                tool_used="none",
                reasoning="Error occurred during processing",
                result={},
                confidence=0.0,
                processing_time_ms=processing_time_ms,
                error=str(e)
            )
    
    async def process_streaming(self, input_data: OrchestratorInput) -> AsyncIterator[Dict[str, Any]]:
        """
        Process a query through the orchestrator with streaming support.
        
        Yields incremental updates as the graph progresses through nodes.
        
        Args:
            input_data: The orchestrator input
        
        Yields:
            Dict with updates: {"type": "node"|"final", "node": str, "data": dict}
        """
        start_time = time.time()
        
        # Create session ID if not provided
        session_id = input_data.session_id or str(uuid.uuid4())
        
        self.logger.info("process_streaming_start",
            session_id=session_id,
            query=input_data.query[:100]
        )
        
        # Detect input language using LLM
        detected_lang = await self._detect_language(input_data.query)
        
        self.logger.info("language_detected",
            session_id=session_id,
            language=detected_lang
        )
        
        # Store detected language in context for tools to use
        if input_data.context is None:
            input_data.context = {}
        input_data.context['detected_language'] = detected_lang
        
        # Store quick_answer_mode flag in context
        if input_data.quick_answer_mode:
            input_data.context['quick_answer_mode'] = True
        
        # Initial state
        initial_state: OrchestratorState = {
            "query": input_data.query,
            "context": input_data.context,
            "session_id": session_id,
            "messages": [],
            "intent": None,
            "selected_tool": None,
            "tool_reasoning": None,
            "tool_result": None,
            "error": None,
            "confidence": 0.0,
            "retry_count": 0,
            "max_retries": 2,
            "is_valid": True,
            "validation_message": None,
            "hallucination_score": 1.0,
            "hallucination_check_count": 0,
            "needs_hallucination_recheck": False,
            "needs_follow_up": False,
            "follow_up_action": None,
            "processing_time_ms": 0.0,
        }
        
        try:
            # Run the graph with config for checkpointing
            config = {"configurable": {"thread_id": session_id}}
            
            # Use in-memory checkpointer for LangGraph state
            compiled_graph = self.graph.compile(checkpointer=MemorySaver())
            
            # Stream updates as graph progresses
            async for chunk in compiled_graph.astream(initial_state, config=config):
                # Yield node updates
                for node_name, node_state in chunk.items():
                    yield {
                        "type": "node",
                        "node": node_name,
                        "data": {
                            "selected_tool": node_state.get("selected_tool"),
                            "confidence": node_state.get("confidence"),
                            "intent": node_state.get("intent"),
                            "error": node_state.get("error")
                        }
                    }
            
            # Get final state
            final_state = await compiled_graph.aget_state(config)
            final_values = final_state.values
            
            processing_time_ms = (time.time() - start_time) * 1000
            
            # Build final output
            result = final_values.get("tool_result")
            follow_up_result = final_values.get("follow_up_result")
            
            if follow_up_result:
                result["follow_up"] = follow_up_result
            
            if final_values.get("selected_tool") == "activity_generator" and result:
                result = ActivityOutput(**result)
            
            # Translate result to original language if needed
            tool_name = final_values.get("selected_tool", "unknown")
            if detected_lang != 'English':
                self.logger.info("translating_result_streaming",
                    session_id=session_id,
                    target_lang=detected_lang,
                    tool=tool_name
                )
                
                # Handle ActivityOutput (from activity_generator, crisis_handler, etc.)
                if isinstance(result, ActivityOutput):
                    # Translate activity fields
                    result.activity_name = await self._translate_text(result.activity_name, detected_lang)
                    result.description = await self._translate_text(result.description, detected_lang)
                    result.learning_outcome = await self._translate_text(result.learning_outcome, detected_lang)
                    
                    # Translate steps
                    translated_steps = []
                    for step in result.steps:
                        translated_steps.append(await self._translate_text(step, detected_lang))
                    result.steps = translated_steps
                    
                    # Translate materials
                    translated_materials = []
                    for material in result.materials_needed:
                        translated_materials.append(await self._translate_text(material, detected_lang))
                    result.materials_needed = translated_materials
                    
                    # Translate tips if present
                    if result.tips:
                        translated_tips = []
                        for tip in result.tips:
                            translated_tips.append(await self._translate_text(tip, detected_lang))
                        result.tips = translated_tips
                
                # Handle dict-based results (other tools)
                elif isinstance(result, dict):
                    result = await self._translate_dict_result(result, detected_lang, tool_name)
            
            # Update conversation context and save to SQLite
            if result:
                assistant_message = f"Generated activity: {result.activity_name if isinstance(result, ActivityOutput) else 'Response'}"
                
                if session_id in self.contexts:
                    self.contexts[session_id].add_message("assistant", assistant_message)
                
                if self.storage:
                    try:
                        # Prepare metadata with full response data
                        # Serialize result properly based on type
                        if hasattr(result, 'model_dump'):
                            result_data = result.model_dump()
                        elif hasattr(result, 'dict'):
                            result_data = result.dict()
                        elif isinstance(result, dict):
                            result_data = result
                        else:
                            result_data = {"data": str(result)}
                        
                        metadata = {
                            "tool_used": final_values.get("selected_tool", "activity_generator"),
                            "reasoning": final_values.get("tool_reasoning", ""),
                            "confidence": final_values.get("confidence", 0.0),
                            "result": result_data,
                            "timestamp": datetime.utcnow().isoformat()
                        }
                        message_id = await self.storage.add_message(session_id, "assistant", assistant_message, metadata=metadata)
                        self.logger.info("assistant_message_saved_streaming", 
                            session_id=session_id, 
                            message_id=message_id,
                            has_metadata=bool(metadata))
                    except Exception as e:
                        self.logger.error("failed_to_save_assistant_message_streaming",
                            session_id=session_id,
                            error=str(e),
                            exc_info=True)
            
            # Yield final result
            yield {
                "type": "final",
                "data": {
                    "tool_used": final_values.get("selected_tool", "activity_generator"),
                    "reasoning": final_values.get("tool_reasoning", ""),
                    "result": result,
                    "confidence": final_values.get("confidence", 0.8),
                    "processing_time_ms": processing_time_ms,
                    "error": final_values.get("error")
                }
            }
            
            self.logger.info("process_streaming_complete",
                session_id=session_id,
                processing_time_ms=processing_time_ms
            )
            
        except Exception as e:
            processing_time_ms = (time.time() - start_time) * 1000
            
            self.logger.error("process_streaming_error",
                session_id=session_id,
                error=str(e),
                exc_info=True
            )
            
            yield {
                "type": "error",
                "data": {
                    "error": str(e),
                    "processing_time_ms": processing_time_ms
                }
            }
    
    def process_sync(self, input_data: OrchestratorInput) -> OrchestratorOutput:
        """Synchronous version of process()."""
        import asyncio
        return asyncio.run(self.process(input_data))
    
    def get_context(self, session_id: str) -> Optional[ConversationContext]:
        """Get conversation context for a session."""
        return self.contexts.get(session_id)
    
    def clear_context(self, session_id: str) -> bool:
        """Clear conversation context for a session."""
        if session_id in self.contexts:
            del self.contexts[session_id]
            return True
        return False
