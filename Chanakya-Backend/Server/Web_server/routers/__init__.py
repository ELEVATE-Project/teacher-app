"""
API routers.
"""
from .auth import router as auth_router
from .users import router as users_router
from .query import router as query_router
from .chat import router as chat_router
from .sarvam import router as sarvam_router
from .module_router import router as module_router
from .classes import router as classes_router
from .students import router as students_router
from .questions import router as questions_router
from .sessions import router as sessions_router
from .analytics_router import router as analytics_router
from .reflection_router import router as reflection_router
from .listening_router import router as listening_router
from .discuss import router as discuss_router

__all__ = [
    "auth_router",
    "users_router",
    "query_router",
    "chat_router",
    "sarvam_router",
    "module_router",
    "classes_router",
    "students_router",
    "questions_router",
    "sessions_router",
    "analytics_router",
    "reflection_router",
    "listening_router",
    "discuss_router",
]
