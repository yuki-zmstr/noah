"""HTTP streaming chat endpoints using Strands agents."""

import json
import logging
import time
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.database import get_db
from src.services.enhanced_conversation_service import EnhancedConversationService
from src.services.monitoring_service import monitoring_service
from src.services.logging_config import performance_logger
from src.models.conversation import ConversationSession, ConversationMessage
from src.models.user_profile import UserProfile
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize conversation service
conversation_service = EnhancedConversationService()


class ChatRequest(BaseModel):
    message: str
    session_id: str
    user_id: str
    metadata: Optional[Dict[str, Any]] = None


class ConversationHistoryRequest(BaseModel):
    session_id: str
    limit: Optional[int] = 50


@router.post("/stream")
async def stream_chat_response(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """Stream chat response using Strands agents."""
    start_time = time.time()
    
    try:
        # Track chat interaction start
        monitoring_service.track_user_engagement(
            user_id=request.user_id,
            action="chat_message_sent",
            session_id=request.session_id,
            metadata={"message_length": len(request.message)}
        )
        
        # Get or create session (handled by conversation service)
        # Store user message (handled by conversation service)
        
        # Create streaming response
        async def generate_stream():
            response_start_time = time.time()
            chunk_count = 0
            
            try:
                # Stream response from enhanced conversation service
                async for chunk in conversation_service.process_conversation_stream(
                    user_message=request.message,
                    user_id=request.user_id,
                    session_id=request.session_id,
                    db=db,
                    metadata=request.metadata
                ):
                    chunk_count += 1
                    yield f"data: {json.dumps(chunk)}\n\n"
                
                # Track successful completion
                response_time_ms = (time.time() - response_start_time) * 1000
                
                monitoring_service.track_chat_interaction(
                    user_id=request.user_id,
                    message_type="streaming_response",
                    response_time_ms=response_time_ms,
                    success=True
                )
                
                performance_logger.log_user_interaction(
                    user_id=request.user_id,
                    action="chat_stream_completed",
                    duration_ms=response_time_ms,
                    metadata={
                        "chunk_count": chunk_count,
                        "session_id": request.session_id
                    }
                )
                    
            except Exception as e:
                logger.error(f"Error in stream generation: {e}")
                
                # Track streaming error
                monitoring_service.track_chat_interaction(
                    user_id=request.user_id,
                    message_type="streaming_response",
                    success=False,
                    error_type=type(e).__name__
                )
                
                error_data = {
                    "type": "error",
                    "content": "I'm sorry, I encountered an issue processing your message. Please try again!",
                    "timestamp": datetime.utcnow().isoformat()
                }
                yield f"data: {json.dumps(error_data)}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream",
            }
        )
        
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        
        logger.error(f"Error starting chat stream: {e}")
        
        # Track chat stream initialization error
        monitoring_service.track_chat_interaction(
            user_id=request.user_id,
            message_type="stream_initialization",
            response_time_ms=duration_ms,
            success=False,
            error_type=type(e).__name__
        )
        
        raise HTTPException(status_code=500, detail="Failed to start chat stream")


@router.post("/history")
async def get_conversation_history(
    request: ConversationHistoryRequest,
    db: Session = Depends(get_db)
):
    """Get conversation history for a session."""
    try:
        history = await conversation_service.get_conversation_history(
            request.session_id, request.limit, db
        )
        
        return {
            "status": "success",
            "session_id": request.session_id,
            "messages": history,
            "total_messages": len(history)
        }
        
    except Exception as e:
        logger.error(f"Error getting conversation history: {e}")
        raise HTTPException(status_code=500, detail="Failed to get conversation history")


@router.post("/preferences/update")
async def update_preferences_notification(
    user_id: str,
    preference_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Handle preference updates (replaces WebSocket preference notifications)."""
    try:
        from src.services.user_profile_service import user_profile_engine
        from src.services.recommendation_engine import contextual_recommendation_engine
        
        # Get updated transparency data
        transparency_data = await user_profile_engine.get_preference_transparency(user_id, db)
        
        response = {
            "status": "success",
            "user_id": user_id,
            "updated_preferences": transparency_data,
            "timestamp": preference_data.get("timestamp", datetime.utcnow().isoformat())
        }
        
        # If this is a significant preference change, include fresh recommendations
        if preference_data.get("type") in ["topic", "content_type", "reading_level"]:
            try:
                recommendations = await contextual_recommendation_engine.generate_contextual_recommendations(
                    user_id, limit=5, db=db
                )
                
                if recommendations:
                    response["new_recommendations"] = recommendations
                    
            except Exception as e:
                logger.error(f"Failed to refresh recommendations for {user_id}: {e}")
        
        return response
        
    except Exception as e:
        logger.error(f"Error handling preference update for {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to process preference update")