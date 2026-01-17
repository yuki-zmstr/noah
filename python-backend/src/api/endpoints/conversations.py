"""Conversation API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import uuid
from datetime import datetime

from src.database import get_db
from src.models.conversation import ConversationSession, ConversationMessage
from src.schemas.conversation import (
    ConversationSessionCreate,
    ConversationSessionResponse,
    ConversationMessageCreate,
    ConversationMessageResponse
)

router = APIRouter()


@router.post("/test-message")
async def test_message_functionality(
    message: dict,
    db: Session = Depends(get_db)
):
    """
    Test endpoint for basic message functionality with hardcoded responses.
    This endpoint is used to validate production deployment.
    """
    user_message = message.get("content", "").lower()
    user_id = message.get("user_id", "test-user")

    # Hardcoded responses for testing
    if "hello" in user_message or "hi" in user_message:
        response = "Hello! I'm Noah, your reading agent. I'm here to help you discover amazing books!"
    elif "book" in user_message or "recommend" in user_message:
        response = "I'd love to recommend some books! What genres do you enjoy reading?"
    elif "help" in user_message:
        response = "I can help you find books, get reading recommendations, and discover new authors. What would you like to explore?"
    elif "test" in user_message:
        response = "Test successful! The production deployment is working correctly. 🎉"
    else:
        response = "I'm Noah, your AI reading companion! I'm currently in test mode. Try saying 'hello', 'recommend a book', or 'help'."

    # Create a test session if it doesn't exist
    session_id = f"test-session-{user_id}"
    session = db.query(ConversationSession).filter(
        ConversationSession.session_id == session_id
    ).first()

    if not session:
        session = ConversationSession(
            session_id=session_id,
            user_id=user_id,
            context={"test_mode": True},
            is_persistent=False
        )
        db.add(session)
        db.commit()
        db.refresh(session)

    # Store the user message
    user_msg = ConversationMessage(
        message_id=str(uuid.uuid4()),
        session_id=session_id,
        sender="user",
        content=message.get("content", ""),
        intent={"type": "test_message"}
    )
    db.add(user_msg)

    # Store the bot response
    bot_msg = ConversationMessage(
        message_id=str(uuid.uuid4()),
        session_id=session_id,
        sender="noah",
        content=response,
        intent={"type": "test_response"}
    )
    db.add(bot_msg)

    db.commit()

    return {
        "status": "success",
        "user_message": message.get("content", ""),
        "bot_response": response,
        "session_id": session_id,
        "timestamp": datetime.utcnow().isoformat(),
        "test_mode": True
    }


@router.get("/health")
async def conversation_health_check():
    """Health check for conversation service."""
    return {
        "status": "healthy",
        "service": "conversation",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.post("/sessions", response_model=ConversationSessionResponse)
async def create_conversation_session(
    session: ConversationSessionCreate,
    db: Session = Depends(get_db)
):
    """Create a new conversation session."""
    # Check if session already exists
    existing_session = db.query(ConversationSession).filter(
        ConversationSession.session_id == session.session_id
    ).first()

    if existing_session:
        raise HTTPException(status_code=400, detail="Session already exists")

    # Create new session
    db_session = ConversationSession(
        session_id=session.session_id,
        user_id=session.user_id,
        context=session.context.dict() if session.context else None,
        is_persistent=session.is_persistent
    )

    db.add(db_session)
    db.commit()
    db.refresh(db_session)

    return db_session


@router.get("/sessions/{session_id}", response_model=ConversationSessionResponse)
async def get_conversation_session(
    session_id: str,
    db: Session = Depends(get_db)
):
    """Get conversation session by ID."""
    session = db.query(ConversationSession).filter(
        ConversationSession.session_id == session_id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return session


@router.post("/messages", response_model=ConversationMessageResponse)
async def create_message(
    message: ConversationMessageCreate,
    db: Session = Depends(get_db)
):
    """Create a new conversation message."""
    # Verify session exists
    session = db.query(ConversationSession).filter(
        ConversationSession.session_id == message.session_id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Create message
    db_message = ConversationMessage(
        message_id=message.message_id,
        session_id=message.session_id,
        sender=message.sender,
        content=message.content,
        intent=message.intent,
        recommendations=message.recommendations,
        purchase_links=message.purchase_links
    )

    db.add(db_message)
    db.commit()
    db.refresh(db_message)

    return db_message


@router.get("/sessions/{session_id}/messages", response_model=List[ConversationMessageResponse])
async def get_session_messages(
    session_id: str,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Get messages for a conversation session."""
    messages = db.query(ConversationMessage).filter(
        ConversationMessage.session_id == session_id
    ).order_by(ConversationMessage.timestamp.desc()).offset(offset).limit(limit).all()

    return messages


@router.get("/users/{user_id}/sessions", response_model=List[ConversationSessionResponse])
async def get_user_sessions(
    user_id: str,
    db: Session = Depends(get_db)
):
    """Get all conversation sessions for a user."""
    sessions = db.query(ConversationSession).filter(
        ConversationSession.user_id == user_id
    ).order_by(ConversationSession.last_activity.desc()).all()

    return sessions
