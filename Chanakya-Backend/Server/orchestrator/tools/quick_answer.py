"""
Quick Answer Tool
==================

Handles simple, factual queries that need short, direct answers.
Examples: calculations (2+2), simple facts, definitions, quick questions.
"""

import re
from typing import Dict, Any, Optional
from google import genai
from google.genai import types


class QuickAnswerTool:
    """
    Tool for providing quick, short answers to simple queries.
    
    Handles:
    - Simple calculations (2+2, 5*8, etc.)
    - Quick facts (capital of India, speed of light, etc.)
    - Short definitions (what is GDP, what is photosynthesis)
    - Simple yes/no questions
    """
    
    def __init__(self, api_key: str):
        """Initialize the quick answer tool."""
        self.client = genai.Client(api_key=api_key)
        self.model_name = "models/gemini-2.5-flash"
    
    def _evaluate_math(self, query: str) -> Optional[str]:
        """
        Try to evaluate as a mathematical expression.
        Returns the result if successful, None otherwise.
        """
        # Clean the query - remove common words and keep only math expression
        math_query = query.lower().strip()
        math_query = re.sub(r'\b(what is|calculate|solve|find|compute)\b', '', math_query, flags=re.IGNORECASE).strip()
        math_query = re.sub(r'\?', '', math_query).strip()
        
        # Check if it looks like a math expression
        if not re.match(r'^[\d\s\+\-\*\/\(\)\.\%]+$', math_query):
            return None
        
        # Handle percentage calculations (e.g., "15% of 200")
        percent_match = re.match(r'(\d+\.?\d*)\s*%\s*of\s*(\d+\.?\d*)', query, re.IGNORECASE)
        if percent_match:
            percentage = float(percent_match.group(1))
            number = float(percent_match.group(2))
            result = (percentage / 100) * number
            return str(int(result) if result.is_integer() else round(result, 2))
        
        try:
            # Replace common symbols
            math_query = math_query.replace('×', '*').replace('÷', '/')
            
            # Evaluate safely
            result = eval(math_query, {"__builtins__": {}}, {})
            
            # Format result
            if isinstance(result, (int, float)):
                return str(int(result) if isinstance(result, float) and result.is_integer() else result)
            return str(result)
        except:
            return None
    
    async def run(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Provide quick answer to simple queries.
        
        Args:
            query: The user's query
            context: Optional context (e.g., detected_language)
        
        Returns:
            Dict with quick answer
        """
        context = context or {}
        detected_language = context.get('detected_language', 'en')
        
        # Try to evaluate as math first
        math_result = self._evaluate_math(query)
        if math_result is not None:
            return {
                "answer": math_result,
                "query_type": "calculation"
            }
        
        # Prepare prompt for non-math quick answers
        prompt = f"""Answer this question with a short, direct answer (1-2 sentences max).

Question: {query}

Answer:"""
        
        try:
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=[
                    types.Content(
                        role="user",
                        parts=[types.Part(text=prompt)]
                    )
                ],
                config=types.GenerateContentConfig(
                    temperature=0.0,  # Zero temperature for deterministic answers
                    max_output_tokens=250,  # Short but complete responses
                )
            )
            
            answer = response.text.strip()
            
            return {
                "answer": answer,
                "query_type": "quick_answer"
            }
            
        except Exception as e:
            return {
                "answer": f"I encountered an error: {str(e)}",
                "query_type": "error"
            }
