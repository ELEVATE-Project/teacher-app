"""
FastAPI application entry point.
"""
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
server_dir = os.path.dirname(current_dir)

# Add Web_server and Server directories to path
sys.path.insert(0, current_dir)
sys.path.insert(0, server_dir)

# Load environment variables from .env file
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

# Apply OpenRouter patch to google.genai
import importlib
import openrouter_patch
importlib.reload(openrouter_patch)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from database import connect_to_mongo, close_mongo_connection
from config import settings
from routers import (
    auth_router, users_router, query_router, chat_router,
    sarvam_router, module_router, classes_router, students_router,
    questions_router, sessions_router, analytics_router, reflection_router,
    listening_router, discuss_router
)
from services import orchestrator_service
# pyrefly: ignore [missing-import]
import structlog

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    await connect_to_mongo()
    
    # Initialize orchestrator
    try:
        logger.info("Initializing orchestrator service")
        orchestrator_service.initialize()
        logger.info("Orchestrator service initialized successfully")
    except Exception as e:
        import traceback
        print("="*80)
        print("❌ ORCHESTRATOR INITIALIZATION FAILED:")
        traceback.print_exc()
        print("="*80)
        logger.error(f"Failed to initialize orchestrator: {str(e)}")
        logger.warning("Continuing without orchestrator - /api/query endpoints will return 503")
    
    yield
    
    # Shutdown
    await close_mongo_connection()
    logger.info("Application shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="Chanakya Unified API",
    description="Unified Backend API for Chanakya - AI-powered classroom companion with Sahayak Pro feedback system",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers - Original Chanakya API
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(users_router, prefix="/api/users", tags=["Users"])
app.include_router(query_router, prefix="/api/query", tags=["Query"])
app.include_router(chat_router, prefix="/api/chat", tags=["Chat History"])
app.include_router(sarvam_router, prefix="/api/sarvam", tags=["Sarvam AI"])
app.include_router(module_router, prefix="/api/module", tags=["MODULE - Lesson Builder"])

# Include routers - Sahayak Pro (Feedback System)
app.include_router(classes_router, prefix="/api/classes", tags=["Classes"])
app.include_router(students_router, prefix="/api/students", tags=["Students"])
app.include_router(questions_router, prefix="/api/questions", tags=["Questions"])
app.include_router(sessions_router, prefix="/api/sessions", tags=["Sessions"])
app.include_router(analytics_router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(reflection_router, prefix="/api/reflection", tags=["Reflection"])
app.include_router(listening_router, prefix="/api/listening", tags=["Active Listening"])
app.include_router(discuss_router, prefix="/api/discuss", tags=["Discuss"])


from fastapi import Body, HTTPException

@app.post("/api/admin/auth/login")
async def admin_login_endpoint(body: dict = Body(...)):
    email = body.get("email")
    password = body.get("password")
    
    # Fallback to standard DB auth
    from services.auth_service import AuthService
    from schemas.auth import LoginRequest
    try:
        user_response, token = await AuthService.login(LoginRequest(email=email, password=password))
        from models.user import User
        from bson import ObjectId
        user_doc = await User.get(ObjectId(user_response.id))
        role = user_doc.role if user_doc else "teacher"
        
        if role not in ("admin", "super_admin"):
            raise HTTPException(status_code=403, detail="Admin access required")
            
        return {
            "success": True,
            "message": "Login successful",
            "accToken": token,
            "admin": {
                "id": user_response.id,
                "name": user_response.name,
                "email": user_response.email,
                "role": role
            }
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        logger.error(f"Login failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=401, detail="Login failed")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to Chanakya Unified API",
        "version": "2.0.0",
        "docs": "/docs",
        "features": [
            "AI-powered classroom companion",
            "Smart student feedback system",
            "Teaching reflection analysis"
        ]
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "orchestrator_ready": orchestrator_service.is_ready()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.DEBUG
    )
