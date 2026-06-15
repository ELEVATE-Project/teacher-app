"""
Discuss (forum) document models for MongoDB using Beanie.
"""
from datetime import datetime
from typing import List, Optional
from beanie import Document
from pydantic import Field


class DiscussPost(Document):
    """Forum post: teacher question with optional location and upvotes."""
    author_id: str = Field(..., description="User ID of the author")
    body: str = Field(..., min_length=1, max_length=2000, description="Question text")
    location: Optional[str] = Field(default=None, max_length=200)
    upvote_ids: List[str] = Field(default_factory=list, description="User IDs who upvoted")
    tags: List[str] = Field(default_factory=list, max_length=20)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "discuss_posts"


class DiscussReply(Document):
    """Reply to a discuss post."""
    post_id: str = Field(..., description="ID of the DiscussPost")
    author_id: str = Field(..., description="User ID of the author")
    body: str = Field(..., min_length=1, max_length=4000)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "discuss_replies"
