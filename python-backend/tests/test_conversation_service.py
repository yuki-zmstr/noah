"""Tests for conversation service."""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.orm import Session

from src.services.conversation_service import ConversationService
from src.models.conversation import ConversationSession


@pytest.fixture
def conversation_service():
    """Create a conversation service instance."""
    service = ConversationService()
    # Mock the agent core service
    service.agent_core = AsyncMock()
    return service


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    db = MagicMock(spec=Session)
    return db


@pytest.mark.asyncio
async def test_get_or_create_session_new(conversation_service, mock_db):
    """Test creating a new conversation session."""
    # Mock database query to return None (no existing session)
    mock_db.query.return_value.filter.return_value.first.return_value = None

    session_id = "session_testuser_123456"

    # Call the method
    session = await conversation_service._get_or_create_session(session_id, mock_db)

    # Verify session was created
    assert session.session_id == session_id
    assert session.user_id == "testuser"
    assert session.context is not None

    # Verify database operations
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once()


@pytest.mark.asyncio
async def test_get_or_create_session_existing(conversation_service, mock_db):
    """Test getting an existing conversation session."""
    # Mock existing session
    existing_session = ConversationSession(
        session_id="session_testuser_123456",
        user_id="testuser",
        context={"test": "context"}
    )
    mock_db.query.return_value.filter.return_value.first.return_value = existing_session

    session_id = "session_testuser_123456"

    # Call the method
    session = await conversation_service._get_or_create_session(session_id, mock_db)

    # Verify existing session was returned
    assert session == existing_session

    # Verify no new session was created
    mock_db.add.assert_not_called()


@pytest.mark.asyncio
async def test_stream_text_response(conversation_service):
    """Test streaming text response functionality."""
    # Mock the manager
    from src.services import conversation_service as conv_service_module
    conv_service_module.manager = AsyncMock()

    connection_id = "test_connection"
    text = "Hello world this is a test message"

    # Call the streaming method
    await conversation_service._stream_text_response(text, connection_id, chunk_size=2)

    # Verify messages were sent
    assert conv_service_module.manager.send_personal_message.call_count > 0

    # Check that the last message is marked as final
    calls = conv_service_module.manager.send_personal_message.call_args_list
    last_call = calls[-1]
    import json
    last_message = json.loads(last_call[0][0])
    assert last_message["is_final"] is True


@pytest.mark.asyncio
async def test_handle_and_stream_book_recommendation(conversation_service, mock_db):
    """Test handling book recommendation with streaming."""
    # Mock the manager and agent core
    from src.services import conversation_service as conv_service_module
    conv_service_module.manager = AsyncMock()

    conversation_service.agent_core.generate_response = AsyncMock(
        return_value="Here are some great book recommendations for you!"
    )

    # Mock session
    session = ConversationSession(
        session_id="test_session",
        user_id="test_user",
        context={}
    )

    connection_id = "test_connection"
    user_message = "Can you recommend some books?"
    entities = {"book_title": [], "author": [], "genre": []}

    # Call the method
    result = await conversation_service._handle_and_stream_book_recommendation(
        user_message, entities, session, connection_id, mock_db
    )

    # Verify response structure
    assert result["type"] == "recommendation"
    assert "recommendations" in result
    assert len(result["recommendations"]) > 0

    # Verify agent core was called
    conversation_service.agent_core.generate_response.assert_called_once()

    # Verify streaming messages were sent
    # Text + recommendations
    assert conv_service_module.manager.send_personal_message.call_count >= 2


def test_fallback_intent_analysis():
    """Test fallback intent analysis."""
    from src.services.agent_core import AgentCoreService

    agent_core = AgentCoreService()

    # Test book recommendation intent
    result = agent_core._fallback_intent_analysis(
        "Can you recommend a good book?")
    assert result["intent"] == "book_recommendation"
    assert result["confidence"] > 0

    # Test purchase inquiry intent
    result = agent_core._fallback_intent_analysis("Where can I buy this book?")
    assert result["intent"] == "purchase_inquiry"

    # Test discovery mode intent
    result = agent_core._fallback_intent_analysis("I'm feeling lucky!")
    assert result["intent"] == "discovery_mode"

    # Test general conversation
    result = agent_core._fallback_intent_analysis("Hello there!")
    assert result["intent"] == "general_conversation"


def test_fallback_entity_extraction():
    """Test fallback entity extraction."""
    from src.services.agent_core import AgentCoreService

    agent_core = AgentCoreService()

    # Test language detection
    result = agent_core._fallback_entity_extraction(
        "I want to read Japanese books")
    assert "japanese" in result["language"]

    result = agent_core._fallback_entity_extraction("English novels are great")
    assert "english" in result["language"]

    # Test empty extraction
    result = agent_core._fallback_entity_extraction("Hello")
    assert all(len(entities) == 0 for entities in result.values()
               if entities != result["language"])
