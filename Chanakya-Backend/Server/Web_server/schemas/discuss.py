"""
Discuss (forum) Pydantic schemas.
"""
from datetime import datetime
from pydantic import BaseModel, Field
from typing import List, Optional


class PostCreate(BaseModel):
    """Create a new post."""
    body: str = Field(..., min_length=1, max_length=2000)
    location: Optional[str] = Field(None, max_length=200)
    tags: List[str] = Field(default_factory=list, max_length=20)


class ReplyCreate(BaseModel):
    """Create a reply to a post."""
    body: str = Field(..., min_length=1, max_length=2000)


class PostResponse(BaseModel):
    """Single post in list or detail."""
    id: str
    author_id: str
    author_name: str
    body: str
    location: Optional[str] = None
    upvote_count: int
    reply_count: int
    tags: List[str]
    created_at: datetime

    class Config:
        from_attributes = True


class ReplyResponse(BaseModel):
    """Single reply."""
    id: str
    post_id: str
    author_id: str
    author_name: str
    body: str
    created_at: datetime

    class Config:
        from_attributes = True


class PostListResponse(BaseModel):
    """Paginated list of posts."""
    posts: List[PostResponse]
    total: int
    skip: int
    limit: int


class PostDetailResponse(BaseModel):
    """Single post with replies."""
    post: PostResponse
    replies: List[ReplyResponse]
