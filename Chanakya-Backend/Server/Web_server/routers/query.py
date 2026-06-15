"""
Query router for orchestrator integration.
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Depends, UploadFile, File, Form
from fastapi.responses import JSONResponse
import structlog
import json
import time
from datetime import datetime
from typing import List, Optional
from services.orchestrator_service import orchestrator_service
from services.chat_service import ChatService
from services.vision_service import get_vision_service
from services.pdf_compiler_service import compile_pdf_async
from schemas.query import QueryRequest, QueryResponse
from routers.users import get_current_user_id
from config import settings

logger = structlog.get_logger(__name__)

router = APIRouter()


@router.post("/vision")
async def analyze_image(
    image: UploadFile = File(...),
    query: str = Form(default="Please analyze this image"),
    session_id: Optional[str] = Form(default=None),
    user_id: str = Depends(get_current_user_id)
):
    """
    Analyze an uploaded image using Gemini Vision API.
    
    Args:
        image: The uploaded image file
        query: User's question about the image
        session_id: Optional session ID for chat history
        user_id: Current user ID from authentication
        
    Returns:
        Analysis result from Gemini Vision
    """
    start_time = time.time()
    
    try:
        # Validate file type
        allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
        if image.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed: {', '.join(allowed_types)}"
            )
        
        # Check file size (max 10MB)
        contents = await image.read()
        if len(contents) > 10 * 1024 * 1024:
            raise HTTPException(
                status_code=400,
                detail="Image too large. Maximum size is 10MB."
            )
        
        logger.info("Analyzing image",
                   filename=image.filename,
                   size=len(contents),
                   mime_type=image.content_type,
                   query=query[:100])
        
        # Get vision service
        vision_service = get_vision_service(settings.GEMINI_API_KEY)
        
        # Analyze the image
        result = await vision_service.analyze_image(
            image_data=contents,
            mime_type=image.content_type,
            query=query
        )
        
        processing_time_ms = (time.time() - start_time) * 1000
        
        # Save to chat history if session_id provided
        if session_id and result.get("success"):
            # Save user message (with image indicator)
            await ChatService.save_message(
                session_id=session_id,
                user_id=user_id,
                role="user",
                content=f"[Image: {image.filename}] {query}"
            )
            
            # Save assistant response
            await ChatService.save_message(
                session_id=session_id,
                user_id=user_id,
                role="assistant",
                content=result.get("analysis", ""),
                tool_used="vision_analysis",
                confidence=result.get("confidence", 0.9),
                metadata={
                    "tool_used": "vision_analysis",
                    "image_filename": image.filename,
                    "result": {"response": result.get("analysis", "")},
                    "confidence": result.get("confidence", 0.9),
                    "processing_time_ms": processing_time_ms
                }
            )
        
        logger.info("Image analysis complete", 
                   processing_time_ms=processing_time_ms,
                   success=result.get("success"))
        
        return {
            "success": result.get("success", False),
            "tool_used": "vision_analysis",
            "reasoning": "Image analysis using Gemini Vision",
            "result": {
                "response": result.get("analysis", ""),
                "image_filename": image.filename
            },
            "confidence": result.get("confidence", 0.9),
            "processing_time_ms": processing_time_ms,
            "timestamp": datetime.utcnow().isoformat(),
            "error": result.get("error")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Image analysis failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Image analysis failed: {str(e)}"
        )


PDF_MAX_SIZE_BYTES = 20 * 1024 * 1024  # 20MB


@router.post("/pdf")
async def upload_pdf(
    pdf: UploadFile = File(...),
    session_id: Optional[str] = Form(default=None),
    user_id: str = Depends(get_current_user_id)
):
    """
    Upload a PDF for compilation (type detection, text/vision pipeline, section consolidation).
    Returns document_id and summary; chat can then answer questions over this document.
    """
    try:
        if pdf.content_type != "application/pdf":
            raise HTTPException(
                status_code=400,
                detail="Invalid file type. Only PDF is allowed."
            )
        contents = await pdf.read()
        if len(contents) > PDF_MAX_SIZE_BYTES:
            raise HTTPException(
                status_code=400,
                detail="PDF too large. Maximum size is 20MB."
            )
        logger.info("Compiling PDF", filename=pdf.filename or "upload.pdf", size=len(contents))
        document_id, summary = await compile_pdf_async(contents, document_id=None, db_path=None)
        if session_id:
            await ChatService.save_message(
                session_id=session_id,
                user_id=user_id,
                role="user",
                content=f"[PDF: {pdf.filename or 'document.pdf'}]"
            )
            response_content = f"Document ready. You can ask questions about it.\n\n**Summary:**\n{summary}"
            await ChatService.save_message(
                session_id=session_id,
                user_id=user_id,
                role="assistant",
                content=response_content,
                tool_used="document_ready",
                confidence=0.95,
                metadata={
                    "tool_used": "document_ready",
                    "document_id": document_id,
                    "summary": summary,
                    "filename": pdf.filename or "document.pdf",
                    "result": {"summary": summary, "document_id": document_id},
                }
            )
        return {
            "success": True,
            "document_id": document_id,
            "summary": summary,
            "tool_used": "document_ready",
        }
    except HTTPException:
        raise
    except ValueError as e:
        logger.error("PDF compile validation error: %s", e)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("PDF compilation failed: %s", e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"PDF processing failed: {str(e)}"
        )


@router.post("/query", response_model=QueryResponse)
async def process_query(
    query_request: QueryRequest,
    user_id: str = Depends(get_current_user_id)
) -> QueryResponse:
    """
    Process a query using the orchestrator and save to chat history.
    
    Args:
        query_request: The query request with query text and context
        user_id: Current user ID from authentication token
        
    Returns:
        QueryResponse with the orchestrator's response
    """
    try:
        logger.info("Received query request", 
                   query=query_request.query[:100], 
                   user_id=user_id,
                   session_id=query_request.session_id)

        if query_request.session_id:
            await ChatService.get_or_create_session(
                session_id=query_request.session_id,
                user_id=user_id,
                ragflow_context=query_request.context or {},
            )
        
        if not orchestrator_service.is_ready():
            raise HTTPException(
                status_code=503,
                detail="Orchestrator service is not ready. Please try again later."
            )
        
        # Save user message to chat history
        if query_request.session_id:
            logger.info("Saving user message to chat history",
                       session_id=query_request.session_id,
                       user_id=user_id)
            await ChatService.save_message(
                session_id=query_request.session_id,
                user_id=user_id,
                role="user",
                content=query_request.query
            )
            logger.info("User message saved successfully")
        
        # Process the query
        response = await orchestrator_service.process_query(query_request)
        
        # Save assistant response to chat history
        if query_request.session_id and response.success:
            logger.info("Saving assistant response to chat history",
                       session_id=query_request.session_id,
                       user_id=user_id,
                       tool_used=response.tool_used)
            
            # Extract text response for storage
            response_text = ""
            if isinstance(response.result, dict):
                # Prefer summary for resource_finder so history shows readable text
                if response.tool_used == "resource_finder" and response.result.get("summary"):
                    response_text = response.result.get("summary")
                else:
                    response_text = response.result.get("response", str(response.result))
            else:
                response_text = str(response.result)
            
            await ChatService.save_message(
                session_id=query_request.session_id,
                user_id=user_id,
                role="assistant",
                content=response_text,
                tool_used=response.tool_used,
                confidence=response.confidence,
                metadata={
                    "tool_used": response.tool_used,
                    "reasoning": response.reasoning,
                    "result": response.result,  # Save the full result for formatting
                    "resources": getattr(response, "resources", None),  # For expert_teacher + needs_resources
                    "confidence": response.confidence,
                    "processing_time_ms": response.processing_time_ms,
                    "timestamp": response.timestamp.isoformat() if response.timestamp else None
                }
            )
            logger.info("Assistant response saved successfully")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in process_query: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for streaming query responses.
    
    Client sends JSON: {"query": "...", "context": {...}, "session_id": "..."}
    Server streams back JSON responses with partial results.
    """
    await websocket.accept()
    logger.info("WebSocket connection established")
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            
            try:
                # Parse the incoming message
                message = json.loads(data)
                query_request = QueryRequest(**message)
                
                logger.info("WebSocket query received", query=query_request.query[:100])
                
                # Check if orchestrator is ready
                if not orchestrator_service.is_ready():
                    await websocket.send_json({
                        "error": "Orchestrator service not ready",
                        "success": False
                    })
                    continue
                
                # Process the query
                response = await orchestrator_service.process_query(query_request)
                
                # Send complete response
                await websocket.send_json({
                    "success": response.success,
                    "tool_used": response.tool_used,
                    "reasoning": response.reasoning,
                    "result": response.result,
                    "confidence": response.confidence,
                    "processing_time_ms": response.processing_time_ms,
                    "timestamp": response.timestamp.isoformat(),
                    "error": response.error
                })
                
                logger.info("WebSocket response sent", tool_used=response.tool_used)
                
            except json.JSONDecodeError:
                await websocket.send_json({
                    "error": "Invalid JSON format",
                    "success": False
                })
                logger.error("Invalid JSON received on WebSocket")
                
            except Exception as e:
                await websocket.send_json({
                    "error": f"Error processing query: {str(e)}",
                    "success": False
                })
                logger.error(f"Error processing WebSocket query: {str(e)}")
                
    except WebSocketDisconnect:
        logger.info("WebSocket connection closed")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        try:
            await websocket.close()
        except:
            pass


@router.get("/tools")
async def get_tools() -> JSONResponse:
    """
    Get list of available tools from the orchestrator.
    
    Returns:
        JSON response with list of available tools and their descriptions
    """
    try:
        if not orchestrator_service.is_ready():
            return JSONResponse(
                status_code=503,
                content={
                    "error": "Orchestrator service not ready",
                    "tools": []
                }
            )
        
        tools = orchestrator_service.get_available_tools()
        
        logger.info(f"Retrieved {len(tools)} available tools")
        
        return JSONResponse(
            content={
                "success": True,
                "count": len(tools),
                "tools": tools
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting tools: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving tools: {str(e)}"
        )


@router.get("/status")
async def get_status() -> JSONResponse:
    """
    Get orchestrator service status.
    
    Returns:
        JSON response with service status and availability
    """
    is_ready = orchestrator_service.is_ready()
    
    return JSONResponse(
        content={
            "status": "ready" if is_ready else "not_ready",
            "initialized": orchestrator_service.initialized,
            "available": is_ready
        }
    )


@router.get("/history")
async def get_chat_history(limit: int = 20, user_id: str = Depends(get_current_user_id)) -> JSONResponse:
    """
    Get recent chat history sessions.
    
    Args:
        limit: Maximum number of sessions to return (default: 20)
        
    Returns:
        JSON response with list of recent chat sessions
    """
    try:
        if not orchestrator_service.is_ready():
            return JSONResponse(
                status_code=503,
                content={
                    "error": "Orchestrator service not ready",
                    "sessions": []
                }
            )
        
        sessions = await orchestrator_service.get_recent_sessions(limit)
        
        logger.info(f"Retrieved {len(sessions)} chat history sessions")
        
        return JSONResponse(
            content={
                "success": True,
                "count": len(sessions),
                "sessions": sessions
            }
        )
        
    except Exception as e:
        logger.error(f"Error fetching chat history: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "error": f"Error fetching chat history: {str(e)}",
                "sessions": []
            }
        )


@router.get("/history/{session_id}")
async def get_session_history(session_id: str, user_id: str = Depends(get_current_user_id)) -> JSONResponse:
    """
    Get message history for a specific session.
    
    Args:
        session_id: The session ID to retrieve
        
    Returns:
        JSON response with session messages
    """
    try:
        if not orchestrator_service.is_ready():
            return JSONResponse(
                status_code=503,
                content={
                    "error": "Orchestrator service not ready",
                    "messages": []
                }
            )
        
        messages = await orchestrator_service.get_session_messages(session_id)
        
        logger.info(f"Retrieved {len(messages)} messages for session {session_id}")
        
        return JSONResponse(
            content={
                "success": True,
                "session_id": session_id,
                "count": len(messages),
                "messages": messages
            }
        )
        
    except Exception as e:
        logger.error(f"Error fetching session history: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "error": f"Error fetching session history: {str(e)}",
                "messages": []
            }
        )


@router.delete("/history/{session_id}")
async def delete_session(session_id: str, user_id: str = Depends(get_current_user_id)) -> JSONResponse:
    """
    Delete a chat session and its history.
    
    Args:
        session_id: The session ID to delete
        
    Returns:
        JSON response with deletion status
    """
    try:
        if not orchestrator_service.is_ready():
            return JSONResponse(
                status_code=503,
                content={
                    "error": "Orchestrator service not ready",
                    "success": False
                }
            )
        
        success = await orchestrator_service.delete_session(session_id)
        
        logger.info(f"Deleted session {session_id}: {success}")
        
        return JSONResponse(
            content={
                "success": success,
                "message": "Session deleted successfully" if success else "Session not found"
            }
        )
        
    except Exception as e:
        logger.error(f"Error deleting session: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "error": f"Error deleting session: {str(e)}",
                "success": False
            }
        )
