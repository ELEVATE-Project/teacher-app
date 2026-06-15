"""
Image Generator
===============

Generates educational diagrams from text prompts.
Supports configurable image generation APIs with graceful error handling.
"""

import logging
import os
import re
import base64
import httpx
from typing import Optional, Dict, Any
from abc import ABC, abstractmethod

# Handle both relative and absolute imports
try:
    from ..models.schemas import DiagramResult
except ImportError:
    from pydantic import BaseModel, Field
    
    class DiagramResult(BaseModel):
        """Result from diagram generation."""
        success: bool = Field(..., description="Whether generation succeeded")
        image_url: Optional[str] = Field(None, description="URL of generated image")
        image_base64: Optional[str] = Field(None, description="Base64 encoded image data")
        prompt_used: str = Field(..., description="Prompt used for generation")
        error: Optional[str] = Field(None, description="Error message if failed")

logger = logging.getLogger(__name__)


# =============================================================================
# Image Generation API Interfaces
# =============================================================================

class ImageGenerationAPI(ABC):
    """Abstract base class for image generation APIs."""
    
    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> DiagramResult:
        """Generate an image from a prompt."""
        pass


class PlaceholderImageAPI(ImageGenerationAPI):
    """
    Placeholder implementation that returns a success result without actual generation.
    Used for testing and development when no real API is configured.
    """
    
    async def generate(self, prompt: str, **kwargs) -> DiagramResult:
        """Return a placeholder result indicating no real API is configured."""
        logger.info(f"PlaceholderImageAPI: Would generate image for prompt: {prompt[:100]}...")
        return DiagramResult(
            success=True,
            image_url=None,
            image_base64=None,
            prompt_used=prompt,
            error="No image generation API configured. Using placeholder."
        )


class OpenAIImageAPI(ImageGenerationAPI):
    """
    OpenAI DALL-E image generation API implementation.
    Requires OPENAI_API_KEY environment variable.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.base_url = "https://api.openai.com/v1/images/generations"
    
    async def generate(self, prompt: str, **kwargs) -> DiagramResult:
        """Generate an image using OpenAI DALL-E."""
        if not self.api_key:
            return DiagramResult(
                success=False,
                prompt_used=prompt,
                error="OpenAI API key not configured"
            )
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    self.base_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": kwargs.get("model", "dall-e-3"),
                        "prompt": prompt,
                        "n": 1,
                        "size": kwargs.get("size", "1024x1024"),
                        "response_format": "url"
                    }
                )
                
                if response.status_code != 200:
                    return DiagramResult(
                        success=False,
                        prompt_used=prompt,
                        error=f"OpenAI API error: {response.status_code} - {response.text}"
                    )
                
                data = response.json()
                image_url = data.get("data", [{}])[0].get("url")
                
                return DiagramResult(
                    success=True,
                    image_url=image_url,
                    prompt_used=prompt
                )
                
        except httpx.TimeoutException:
            return DiagramResult(
                success=False,
                prompt_used=prompt,
                error="Image generation timed out"
            )
        except Exception as e:
            logger.error(f"OpenAI image generation failed: {e}")
            return DiagramResult(
                success=False,
                prompt_used=prompt,
                error=f"Image generation failed: {str(e)}"
            )


class StabilityAIImageAPI(ImageGenerationAPI):
    """
    Stability AI image generation API implementation.
    Requires STABILITY_API_KEY environment variable.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("STABILITY_API_KEY")
        self.base_url = "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image"
    
    async def generate(self, prompt: str, **kwargs) -> DiagramResult:
        """Generate an image using Stability AI."""
        if not self.api_key:
            return DiagramResult(
                success=False,
                prompt_used=prompt,
                error="Stability AI API key not configured"
            )
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    self.base_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                        "Accept": "application/json"
                    },
                    json={
                        "text_prompts": [{"text": prompt, "weight": 1}],
                        "cfg_scale": 7,
                        "height": 1024,
                        "width": 1024,
                        "samples": 1,
                        "steps": 30
                    }
                )
                
                if response.status_code != 200:
                    return DiagramResult(
                        success=False,
                        prompt_used=prompt,
                        error=f"Stability AI API error: {response.status_code}"
                    )
                
                data = response.json()
                artifacts = data.get("artifacts", [])
                if artifacts:
                    image_base64 = artifacts[0].get("base64")
                    return DiagramResult(
                        success=True,
                        image_base64=image_base64,
                        prompt_used=prompt
                    )
                
                return DiagramResult(
                    success=False,
                    prompt_used=prompt,
                    error="No image generated"
                )
                
        except httpx.TimeoutException:
            return DiagramResult(
                success=False,
                prompt_used=prompt,
                error="Image generation timed out"
            )
        except Exception as e:
            logger.error(f"Stability AI image generation failed: {e}")
            return DiagramResult(
                success=False,
                prompt_used=prompt,
                error=f"Image generation failed: {str(e)}"
            )


# =============================================================================
# Image Generator Class
# =============================================================================

class ImageGenerator:
    """
    Generates educational diagrams from prompts.
    
    Supports multiple image generation APIs with configurable backend.
    Includes prompt enhancement for educational content.
    """
    
    # Supported API backends
    SUPPORTED_APIS = {
        "placeholder": PlaceholderImageAPI,
        "openai": OpenAIImageAPI,
        "stability": StabilityAIImageAPI,
    }
    
    # Class level complexity mappings
    CLASS_LEVEL_COMPLEXITY = {
        "Class_1": "very simple, cartoon-like, colorful, minimal text",
        "Class_2": "very simple, cartoon-like, colorful, minimal text",
        "Class_3": "simple, cartoon-like, colorful, basic labels",
        "Class_4": "simple, cartoon-like, colorful, basic labels",
        "Class_5": "simple, cartoon-like, colorful, basic labels",
        "Class_6": "clear, organized, moderate detail, labeled",
        "Class_7": "clear, organized, moderate detail, labeled",
        "Class_8": "clear, organized, some complexity, well-labeled",
        "Class_9": "detailed, can include formulas, comprehensive labels",
        "Class_10": "detailed, can include formulas, comprehensive labels",
    }
    
    # Educational style keywords
    EDUCATIONAL_STYLE_KEYWORDS = [
        "educational diagram",
        "clear and simple",
        "labeled",
        "white background",
        "clean lines",
        "no text watermarks",
        "suitable for classroom",
    ]
    
    def __init__(
        self,
        api_backend: str = "placeholder",
        api_key: Optional[str] = None
    ):
        """
        Initialize the image generator.
        
        Args:
            api_backend: Which API to use ("placeholder", "openai", "stability")
            api_key: API key for the selected backend (optional, can use env vars)
        """
        self.api_backend = api_backend.lower()
        
        if self.api_backend not in self.SUPPORTED_APIS:
            logger.warning(
                f"Unknown API backend '{api_backend}', falling back to placeholder"
            )
            self.api_backend = "placeholder"
        
        # Initialize the API client
        api_class = self.SUPPORTED_APIS[self.api_backend]
        if api_key and self.api_backend != "placeholder":
            self.api_client = api_class(api_key=api_key)
        else:
            self.api_client = api_class() if self.api_backend == "placeholder" else api_class()
        
        logger.info(f"ImageGenerator initialized with {self.api_backend} backend")
    
    async def generate_diagram(
        self,
        prompt: str,
        style: str = "educational",
        class_level: str = "Class_8"
    ) -> DiagramResult:
        """
        Generates an educational diagram from the prompt.
        
        Args:
            prompt: Description of the diagram to generate
            style: Visual style (educational, simple, detailed)
            class_level: Target audience level (e.g., "Class_6", "Class_10")
            
        Returns:
            DiagramResult with image URL/base64 and metadata, or error info
        """
        if not prompt or not prompt.strip():
            return DiagramResult(
                success=False,
                prompt_used=prompt or "",
                error="Empty prompt provided"
            )
        
        try:
            # Enhance the prompt for educational content
            enhanced_prompt = self._enhance_prompt_for_education(
                prompt=prompt,
                class_level=class_level,
                style=style
            )
            
            logger.info(f"Generating diagram for class {class_level}: {prompt[:100]}...")
            
            # Call the API
            result = await self.api_client.generate(enhanced_prompt)
            
            # Update the prompt_used to show the enhanced version
            result.prompt_used = enhanced_prompt
            
            if result.success:
                logger.info("Diagram generation successful")
            else:
                logger.warning(f"Diagram generation failed: {result.error}")
            
            return result
            
        except Exception as e:
            logger.error(f"Unexpected error in diagram generation: {e}")
            return DiagramResult(
                success=False,
                prompt_used=prompt,
                error=f"Unexpected error: {str(e)}"
            )
    
    def _enhance_prompt_for_education(
        self,
        prompt: str,
        class_level: str,
        style: str = "educational"
    ) -> str:
        """
        Enhances prompt with educational diagram best practices.
        
        Adds: clear labels, simple colors, appropriate complexity for class level.
        
        Args:
            prompt: Original diagram prompt
            class_level: Target class level (e.g., "Class_6")
            style: Visual style preference
            
        Returns:
            Enhanced prompt string
        """
        # Get complexity level for the class
        complexity = self.CLASS_LEVEL_COMPLEXITY.get(
            class_level,
            "clear, organized, moderate detail, labeled"
        )
        
        # Build enhanced prompt
        enhanced_parts = []
        
        # Add style prefix
        if style == "educational":
            enhanced_parts.append("Educational diagram:")
        elif style == "simple":
            enhanced_parts.append("Simple, minimalist diagram:")
        elif style == "detailed":
            enhanced_parts.append("Detailed educational illustration:")
        else:
            enhanced_parts.append("Educational diagram:")
        
        # Add the original prompt
        enhanced_parts.append(prompt.strip())
        
        # Add complexity guidance
        enhanced_parts.append(f"Style: {complexity}.")
        
        # Add educational style keywords
        style_keywords = ", ".join(self.EDUCATIONAL_STYLE_KEYWORDS[:4])
        enhanced_parts.append(f"Requirements: {style_keywords}.")
        
        return " ".join(enhanced_parts)
    
    def get_supported_apis(self) -> list:
        """Return list of supported API backends."""
        return list(self.SUPPORTED_APIS.keys())
    
    def get_current_api(self) -> str:
        """Return the currently configured API backend."""
        return self.api_backend
