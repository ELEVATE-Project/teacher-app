"""
Resource Finder Tool
====================

Searches the web for educational resources, videos, and documentation
using Tavily API. Returns curated links for teachers to use in classroom.
"""

import os
import aiohttp
import structlog
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field

from .base import BaseTool
from ..schemas import ResourceFinderOutput, ResourceLink

logger = structlog.get_logger(__name__)


# ============================================================================
# Tavily Search Types (local definitions to avoid circular imports)
# ============================================================================

@dataclass
class SearchResult:
    """A single search result."""
    title: str
    url: str
    content: str
    score: float = 0.0
    published_date: Optional[str] = None


@dataclass 
class TavilySearchResponse:
    """Response from Tavily search."""
    query: str
    results: List[SearchResult] = field(default_factory=list)
    answer: Optional[str] = None
    response_time: float = 0.0


# ============================================================================
# Tavily Search Service (inline to avoid circular imports)
# ============================================================================

class TavilySearchService:
    """Service for searching the web using Tavily API."""
    
    BASE_URL = "https://api.tavily.com"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("TAVILY_API_KEY")
        if not self.api_key:
            raise ValueError("TAVILY_API_KEY is required")
    
    async def search(
        self,
        query: str,
        search_depth: str = "basic",
        max_results: int = 5,
        include_answer: bool = True,
        include_domains: Optional[List[str]] = None,
        exclude_domains: Optional[List[str]] = None,
        topic: str = "general"
    ) -> TavilySearchResponse:
        """Search the web using Tavily."""
        payload = {
            "api_key": self.api_key,
            "query": query,
            "search_depth": search_depth,
            "max_results": max_results,
            "include_answer": include_answer,
            "topic": topic
        }
        
        if include_domains:
            payload["include_domains"] = include_domains
        if exclude_domains:
            payload["exclude_domains"] = exclude_domains
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.BASE_URL}/search",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Tavily API error: {response.status} - {error_text}")
                        return TavilySearchResponse(query=query, results=[])
                    
                    data = await response.json()
                    
                    results = []
                    for item in data.get("results", []):
                        results.append(SearchResult(
                            title=item.get("title", ""),
                            url=item.get("url", ""),
                            content=item.get("content", ""),
                            score=item.get("score", 0.0),
                            published_date=item.get("published_date")
                        ))
                    
                    return TavilySearchResponse(
                        query=query,
                        results=results,
                        answer=data.get("answer"),
                        response_time=data.get("response_time", 0.0)
                    )
                    
        except Exception as e:
            logger.error(f"Tavily search failed: {e}")
            return TavilySearchResponse(query=query, results=[])
    
    async def search_videos(self, query: str, max_results: int = 5) -> TavilySearchResponse:
        """Search for educational videos on YouTube and other platforms."""
        video_query = f"{query} educational video tutorial"
        return await self.search(
            query=video_query,
            max_results=max_results,
            include_domains=["youtube.com", "vimeo.com", "khanacademy.org", "ted.com", "coursera.org"],
            include_answer=False
        )
    
    async def search_educational_resources(self, query: str, max_results: int = 5) -> TavilySearchResponse:
        """Search for educational resources like PDFs, articles, lesson plans."""
        resource_query = f"{query} educational resources lesson plan teaching materials"
        return await self.search(
            query=resource_query,
            max_results=max_results,
            search_depth="advanced",
            include_domains=[
                "ncert.nic.in", "diksha.gov.in", "cbse.gov.in",
                "teacherspayteachers.com", "education.com", "khanacademy.org",
                "byjus.com", "vedantu.com", "toppr.com"
            ],
            include_answer=True
        )


class ResourceFinderTool(BaseTool):
    """
    Tool that searches for educational resources using Tavily.
    
    Provides:
    - Web articles and documentation
    - YouTube and educational videos  
    - Lesson plans and teaching materials
    - PDFs and study resources
    """
    
    name = "resource_finder"
    description = "Searches the web for educational resources, videos, and materials"
    
    # Keywords that trigger this tool
    TRIGGER_KEYWORDS = [
        "resources", "videos", "video", "youtube", "links", "link",
        "articles", "article", "documentation", "docs", "materials",
        "pdf", "pdfs", "lesson plan", "lesson plans", "teaching materials",
        "web search", "search for", "find me", "give me links",
        "additional resources", "more resources", "related videos",
        "tutorials", "tutorial", "online resources", "websites"
    ]
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Resource Finder Tool.
        
        Args:
            api_key: Tavily API key. If None, reads from TAVILY_API_KEY env var.
        """
        tavily_key = api_key or os.getenv("TAVILY_API_KEY")
        if not tavily_key:
            logger.warning("TAVILY_API_KEY not set - resource finder will be disabled")
            self.tavily = None
        else:
            self.tavily = TavilySearchService(api_key=tavily_key)
        
        logger.info("ResourceFinderTool initialized")
    
    @classmethod
    def should_trigger(cls, query: str) -> bool:
        """
        Check if the query should trigger this tool.
        
        Args:
            query: User's query
            
        Returns:
            True if query contains resource-related keywords
        """
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in cls.TRIGGER_KEYWORDS)
    
    @classmethod
    def extract_topic(cls, query: str) -> str:
        """
        Extract the main topic from a query that includes resource requests.
        
        Args:
            query: Full query like "explain photosynthesis and give me youtube videos"
            
        Returns:
            Extracted topic like "photosynthesis"
        """
        # Remove common resource-related phrases
        clean_query = query.lower()
        
        remove_phrases = [
            "give me", "find me", "search for", "get me", "show me",
            "youtube videos", "videos about", "resources for", "links to",
            "additional resources", "related videos", "and also",
            "also give", "also find", "with resources", "with videos",
            "lesson plans for", "teaching materials for", "pdfs for",
            "and give me", "and find", "and search"
        ]
        
        for phrase in remove_phrases:
            clean_query = clean_query.replace(phrase, " ")
        
        # Remove remaining trigger keywords
        for keyword in cls.TRIGGER_KEYWORDS:
            clean_query = clean_query.replace(keyword, " ")
        
        # Clean up extra spaces
        clean_query = " ".join(clean_query.split()).strip()
        
        return clean_query if clean_query else query
    
    def _convert_to_resource_link(self, result: SearchResult, resource_type: str) -> ResourceLink:
        """Convert a Tavily SearchResult to ResourceLink."""
        return ResourceLink(
            title=result.title,
            url=result.url,
            description=result.content[:200] + "..." if len(result.content) > 200 else result.content,
            resource_type=resource_type
        )
    
    async def run(self, query: str, context: Optional[dict] = None) -> dict:
        """
        Run method required by BaseTool.
        
        Args:
            query: Topic to search for
            context: Optional context
            
        Returns:
            Dictionary output
        """
        result = await self.execute(query, context)
        return result.model_dump() if hasattr(result, 'model_dump') else result
    
    async def execute(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> ResourceFinderOutput:
        """
        Search for educational resources on the given topic.
        
        Args:
            query: Topic or query to search for
            context: Optional context (can include specific resource types)
            
        Returns:
            ResourceFinderOutput with categorized resources
        """
        if not self.tavily:
            logger.error("Tavily service not initialized - API key missing")
            return ResourceFinderOutput(
                query=query,
                summary="Resource search is currently unavailable. Please check API configuration.",
                total_results=0
            )
        
        try:
            # Extract the topic from the query
            topic = self.extract_topic(query)
            if not topic:
                topic = query
            
            logger.info(f"Searching resources for topic: {topic}")
            
            # Determine what types of resources to search
            query_lower = query.lower()
            
            search_videos = any(kw in query_lower for kw in ["video", "youtube", "tutorial"])
            search_edu = any(kw in query_lower for kw in ["lesson plan", "materials", "pdf", "resources"])
            search_web = True  # Always search web
            
            # If no specific type mentioned, search all
            if not search_videos and not search_edu:
                search_videos = True
                search_edu = True
            
            web_resources = []
            video_resources = []
            educational_resources = []
            summary = ""
            
            # Search web resources
            if search_web:
                web_results = await self.tavily.search(
                    query=f"{topic} educational explanation",
                    max_results=3,
                    include_answer=True
                )
                summary = web_results.answer or ""
                for result in web_results.results:
                    web_resources.append(self._convert_to_resource_link(result, "article"))
            
            # Search videos
            if search_videos:
                video_results = await self.tavily.search_videos(topic, max_results=3)
                for result in video_results.results:
                    video_resources.append(self._convert_to_resource_link(result, "video"))
            
            # Search educational resources
            if search_edu:
                edu_results = await self.tavily.search_educational_resources(topic, max_results=3)
                for result in edu_results.results:
                    educational_resources.append(self._convert_to_resource_link(result, "educational"))
            
            total = len(web_resources) + len(video_resources) + len(educational_resources)
            
            logger.info(f"Found {total} resources for: {topic}")
            
            return ResourceFinderOutput(
                query=topic,
                summary=summary,
                web_resources=web_resources,
                video_resources=video_resources,
                educational_resources=educational_resources,
                total_results=total,
                confidence=0.9 if total > 0 else 0.5
            )
            
        except Exception as e:
            logger.error(f"Resource search failed: {e}")
            return ResourceFinderOutput(
                query=query,
                summary=f"Search failed: {str(e)}",
                total_results=0,
                confidence=0.0
            )
    
    def format_response(self, output: ResourceFinderOutput) -> str:
        """
        Format the output as a readable string for the teacher.
        
        Args:
            output: ResourceFinderOutput from execute()
            
        Returns:
            Formatted string with resources
        """
        lines = []
        
        if output.summary:
            lines.append(f"**Summary**: {output.summary}\n")
        
        if output.video_resources:
            lines.append("🎥 **Videos:**")
            for i, video in enumerate(output.video_resources, 1):
                lines.append(f"  {i}. [{video.title}]({video.url})")
            lines.append("")
        
        if output.educational_resources:
            lines.append("📚 **Educational Resources:**")
            for i, res in enumerate(output.educational_resources, 1):
                lines.append(f"  {i}. [{res.title}]({res.url})")
            lines.append("")
        
        if output.web_resources:
            lines.append("🔗 **Related Articles:**")
            for i, web in enumerate(output.web_resources, 1):
                lines.append(f"  {i}. [{web.title}]({web.url})")
            lines.append("")
        
        if not lines:
            lines.append("No resources found for this topic.")
        
        return "\n".join(lines)
