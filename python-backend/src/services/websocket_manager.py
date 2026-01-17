"""WebSocket connection manager for real-time chat."""

import json
import logging
from typing import Dict, List, Optional
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for chat sessions."""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        # session_id -> connection_id
        self.session_connections: Dict[str, str] = {}

    async def connect(self, websocket: WebSocket, connection_id: str):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.active_connections[connection_id] = websocket
        logger.info(f"WebSocket connection established: {connection_id}")

    def disconnect(self, connection_id: str):
        """Remove a WebSocket connection."""
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]

        # Remove from session mapping
        sessions_to_remove = [
            session_id for session_id, conn_id in self.session_connections.items()
            if conn_id == connection_id
        ]
        for session_id in sessions_to_remove:
            del self.session_connections[session_id]

        logger.info(f"WebSocket connection closed: {connection_id}")

    def join_session(self, connection_id: str, session_id: str):
        """Associate a connection with a session."""
        self.session_connections[session_id] = connection_id
        logger.info(f"Connection {connection_id} joined session {session_id}")

    async def send_personal_message(self, message: str, connection_id: str):
        """Send a message to a specific connection."""
        if connection_id in self.active_connections:
            websocket = self.active_connections[connection_id]
            try:
                await websocket.send_text(message)
            except Exception as e:
                logger.error(f"Error sending message to {connection_id}: {e}")
                self.disconnect(connection_id)

    async def send_to_session(self, message: str, session_id: str):
        """Send a message to all connections in a session."""
        if session_id in self.session_connections:
            connection_id = self.session_connections[session_id]
            await self.send_personal_message(message, connection_id)

    async def send_typing_indicator(self, session_id: str, is_typing: bool):
        """Send typing indicator to session."""
        message = json.dumps({
            "type": "typing",
            "is_typing": is_typing,
            "timestamp": datetime.utcnow().isoformat()
        })
        await self.send_to_session(message, session_id)

    async def broadcast(self, message: str):
        """Broadcast a message to all active connections."""
        disconnected = []
        for connection_id, websocket in self.active_connections.items():
            try:
                await websocket.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting to {connection_id}: {e}")
                disconnected.append(connection_id)

        # Clean up disconnected connections
        for connection_id in disconnected:
            self.disconnect(connection_id)

    def get_active_connections_count(self) -> int:
        """Get the number of active connections."""
        return len(self.active_connections)

    def get_session_connections_count(self) -> int:
        """Get the number of session connections."""
        return len(self.session_connections)


# Global connection manager instance
manager = ConnectionManager()
