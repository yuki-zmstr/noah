"""WebSocket endpoints for real-time chat."""

import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any

from src.database import get_db
from src.services.websocket_manager import manager
from src.services.conversation_service import ConversationService
from src.services.user_profile_service import user_profile_engine
from src.services.recommendation_engine import contextual_recommendation_engine

logger = logging.getLogger(__name__)
router = APIRouter()

conversation_service = ConversationService()


async def handle_preference_update(user_id: str, preference_data: Dict[str, Any], 
                                   connection_id: str, db: Session):
    """Handle preference update and send real-time notifications."""
    try:
        # Get updated transparency data
        transparency_data = await user_profile_engine.get_preference_transparency(user_id, db)
        
        # Send preference update confirmation
        await manager.send_personal_message(
            json.dumps({
                "type": "preference_update",
                "user_id": user_id,
                "updated_preferences": transparency_data,
                "timestamp": preference_data.get("timestamp", "")
            }),
            connection_id
        )
        
        # If this is a significant preference change, refresh recommendations
        if preference_data.get("type") in ["topic", "content_type", "reading_level"]:
            try:
                # Get fresh recommendations
                recommendations = await contextual_recommendation_engine.generate_contextual_recommendations(
                    user_id, limit=5, db=db
                )
                
                if recommendations:
                    await manager.send_personal_message(
                        json.dumps({
                            "type": "recommendation_refresh",
                            "user_id": user_id,
                            "new_recommendations": recommendations,
                            "timestamp": preference_data.get("timestamp", "")
                        }),
                        connection_id
                    )
            except Exception as e:
                logger.error(f"Failed to refresh recommendations for {user_id}: {e}")
                
    except Exception as e:
        logger.error(f"Error handling preference update for {user_id}: {e}")
        await manager.send_personal_message(
            json.dumps({
                "type": "error",
                "message": "Failed to process preference update"
            }),
            connection_id
        )


@router.websocket("/ws/{connection_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    connection_id: str,
    db: Session = Depends(get_db)
):
    """WebSocket endpoint for real-time chat communication."""
    await manager.connect(websocket, connection_id)

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()

            try:
                message_data = json.loads(data)
                message_type = message_data.get("type", "message")

                if message_type == "join_session":
                    # Handle session join
                    session_id = message_data.get("sessionId")
                    user_id = message_data.get("userId")

                    if session_id:
                        manager.join_session(connection_id, session_id)

                        # Send confirmation
                        await manager.send_personal_message(
                            json.dumps({
                                "type": "session_joined",
                                "sessionId": session_id,
                                "userId": user_id
                            }),
                            connection_id
                        )

                        # Load and send conversation history
                        history = await conversation_service.get_conversation_history(
                            session_id, limit=50, db=db
                        )

                        await manager.send_personal_message(
                            json.dumps({
                                "type": "conversation_history",
                                "messages": history
                            }),
                            connection_id
                        )

                elif message_type == "user_message":
                    # Handle user message with streaming
                    session_id = message_data.get("sessionId")
                    content = message_data.get("content")
                    metadata = message_data.get("metadata", {})

                    if session_id and content:
                        # Process the message with streaming, including metadata
                        await conversation_service.process_user_message_streaming(
                            session_id, content, connection_id, db, metadata
                        )

                elif message_type == "preference_update":
                    # Handle preference update notifications
                    user_id = message_data.get("userId")
                    preference_data = message_data.get("preferenceData")

                    if user_id and preference_data:
                        # Process preference update and potentially refresh recommendations
                        await handle_preference_update(user_id, preference_data, connection_id, db)

                elif message_type == "ping":
                    # Handle ping for connection health check
                    await manager.send_personal_message(
                        json.dumps({"type": "pong"}),
                        connection_id
                    )

            except json.JSONDecodeError:
                logger.error(
                    f"Invalid JSON received from {connection_id}: {data}")
                await manager.send_personal_message(
                    json.dumps({
                        "type": "error",
                        "message": "Invalid message format"
                    }),
                    connection_id
                )
            except Exception as e:
                logger.error(
                    f"Error processing message from {connection_id}: {e}")
                await manager.send_personal_message(
                    json.dumps({
                        "type": "error",
                        "message": "Error processing your message"
                    }),
                    connection_id
                )

    except WebSocketDisconnect:
        manager.disconnect(connection_id)
        logger.info(f"WebSocket disconnected: {connection_id}")
    except Exception as e:
        logger.error(f"WebSocket error for {connection_id}: {e}")
        manager.disconnect(connection_id)


@router.get("/ws/stats")
async def websocket_stats():
    """Get WebSocket connection statistics."""
    return {
        "active_connections": manager.get_active_connections_count(),
        "session_connections": manager.get_session_connections_count()
    }
