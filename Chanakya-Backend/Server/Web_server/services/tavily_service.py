"""
Tavily Search Service
=====================

Service for searching the web using Tavily API.
Provides educational resources, videos, and relevant links.
"""

import os
import aiohttp
import structlog
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field

logger = structlog.get_logger(__name__)


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


class TavilySearchService:
    """
    Service for searching the web using Tavily API.
    
    Tavily provides AI-optimized search results perfect for 
    educational content retrieval.
    """
    
    BASE_URL = "https://api.tavily.com"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Tavily search service.
        
        Args:
            api_key: Tavily API key. If None, reads from TAVILY_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("TAVILY_API_KEY")
        if not self.api_key:
            raise ValueError("TAVILY_API_KEY is required")
        
        logger.info("TavilySearchService initialized")
    
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
        """
        Search the web using Tavily.
        
        Args:
            query: Search query
            search_depth: "basic" or "advanced" (advanced gives more detailed results)
            max_results: Maximum number of results to return
            include_answer: Whether to include AI-generated answer
            include_domains: List of domains to include
            exclude_domains: List of domains to exclude  
            topic: Search topic - "general" or "news"
            
        Returns:
            TavilySearchResponse with results
        """
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
    
    async def search_videos(
        self,
        query: str,
        max_results: int = 5
    ) -> TavilySearchResponse:
        """
        Search for educational videos on YouTube and other platforms.
        
        Args:
            query: Topic to search videos for
            max_results: Maximum number of results
            
        Returns:
            TavilySearchResponse with video results
        """
        video_query = f"{query} educational video tutorial"
        
        return await self.search(
            query=video_query,
            max_results=max_results,
            include_domains=["youtube.com", "vimeo.com", "khanacademy.org", "ted.com", "coursera.org"],
            include_answer=False
        )
    
    async def search_educational_resources(
        self,
        query: str,
        max_results: int = 5
    ) -> TavilySearchResponse:
        """
        Search for educational resources like PDFs, articles, lesson plans.
        
        Args:
            query: Topic to search resources for
            max_results: Maximum number of results
            
        Returns:
            TavilySearchResponse with educational resources
        """
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
    
    async def search_all(
        self,
        query: str,
        max_results_per_type: int = 3
    ) -> Dict[str, Any]:
        """
        Search for all types of resources: web, videos, and educational materials.
        
        Args:
            query: Topic to search for
            max_results_per_type: Max results for each category
            
        Returns:
            Dictionary with categorized results
        """
        import asyncio
        
        # Run all searches in parallel
        web_task = self.search(query, max_results=max_results_per_type)
        video_task = self.search_videos(query, max_results=max_results_per_type)
        edu_task = self.search_educational_resources(query, max_results=max_results_per_type)
        
        web_results, video_results, edu_results = await asyncio.gather(
            web_task, video_task, edu_task
        )
        
        return {
            "query": query,
            "web_results": web_results,
            "video_results": video_results,
            "educational_resources": edu_results
        }


# Singleton instance
_tavily_service: Optional[TavilySearchService] = None


def get_tavily_service() -> TavilySearchService:
    """Get or create Tavily search service instance."""
    global _tavily_service
    if _tavily_service is None:
        _tavily_service = TavilySearchService()
    return _tavily_service
