"""Conversation processing service with NLU integration."""

import json
import logging
import asyncio
from typing import Dict, List, Optional, Any, AsyncGenerator
from datetime import datetime
from sqlalchemy.orm import Session

from src.models.conversation import ConversationSession, ConversationMessage
from src.models.user_profile import UserProfile
from src.services.agent_core import AgentCoreService
from src.services.websocket_manager import manager

logger = logging.getLogger(__name__)


class ConversationService:
    """Service for processing conversations with NLU capabilities."""

    def __init__(self):
        self.agent_core = AgentCoreService()

    async def process_user_message(
        self,
        session_id: str,
        user_message: str,
        db: Session
    ) -> Dict[str, Any]:
        """Process a user message and generate Noah's response."""
        try:
            # Get or create session
            session = await self._get_or_create_session(session_id, db)

            # Send typing indicator
            await manager.send_typing_indicator(session_id, True)

            # Analyze user intent and extract entities
            intent = await self.agent_core.analyze_intent(
                user_message,
                session.context
            )
            entities = await self.agent_core.extract_entities(user_message)

            # Store user message
            user_msg = await self._store_message(
                session_id=session_id,
                sender="user",
                content=user_message,
                intent=intent,
                db=db
            )

            # Generate Noah's response based on intent
            noah_response = await self._generate_noah_response(
                user_message, intent, entities, session, db
            )

            # Store Noah's message
            noah_msg = await self._store_message(
                session_id=session_id,
                sender="noah",
                content=noah_response["content"],
                intent=intent,
                recommendations=noah_response.get("recommendations"),
                purchase_links=noah_response.get("purchase_links"),
                db=db
            )

            # Update conversation context
            updated_context = await self.agent_core.update_conversation_context(
                session_id, user_message, noah_response["content"], intent
            )

            # Update session context in database
            session.context = updated_context.get(
                "updated_context", session.context)
            session.last_activity = datetime.utcnow()
            db.commit()

            # Stop typing indicator
            await manager.send_typing_indicator(session_id, False)

            return {
                "user_message": {
                    "message_id": user_msg.message_id,
                    "content": user_msg.content,
                    "timestamp": user_msg.timestamp.isoformat(),
                    "sender": "user"
                },
                "noah_response": {
                    "message_id": noah_msg.message_id,
                    "content": noah_msg.content,
                    "timestamp": noah_msg.timestamp.isoformat(),
                    "sender": "noah",
                    "type": noah_response.get("type", "text"),
                    "metadata": {
                        "recommendations": noah_response.get("recommendations"),
                        "purchase_links": noah_response.get("purchase_links")
                    }
                },
                "intent": intent,
                "entities": entities
            }

        except Exception as e:
            logger.error(f"Error processing user message: {e}")
            await manager.send_typing_indicator(session_id, False)

            # Send error response
            error_response = await self._generate_error_response(str(e))
            error_msg = await self._store_message(
                session_id=session_id,
                sender="noah",
                content=error_response,
                db=db
            )

            return {
                "noah_response": {
                    "message_id": error_msg.message_id,
                    "content": error_response,
                    "timestamp": error_msg.timestamp.isoformat(),
                    "sender": "noah",
                    "type": "text"
                },
                "error": str(e)
            }

    async def process_user_message_streaming(
        self,
        session_id: str,
        user_message: str,
        connection_id: str,
        db: Session,
        metadata: Optional[Dict] = None
    ) -> None:
        """Process a user message and stream Noah's response in real-time."""
        try:
            # Get or create session
            session = await self._get_or_create_session(session_id, db)

            # Send typing indicator
            await manager.send_typing_indicator(session_id, True)

            # Analyze user intent and extract entities, considering metadata
            intent = await self.agent_core.analyze_intent(
                user_message,
                session.context,
                metadata
            )
            entities = await self.agent_core.extract_entities(user_message)

            # Store user message
            user_msg = await self._store_message(
                session_id=session_id,
                sender="user",
                content=user_message,
                intent=intent,
                db=db
            )

            # Send user message confirmation
            await manager.send_personal_message(
                json.dumps({
                    "type": "user_message_received",
                    "message_id": user_msg.message_id,
                    "content": user_msg.content,
                    "timestamp": user_msg.timestamp.isoformat(),
                    "sender": "user"
                }),
                connection_id
            )

            # Generate and stream Noah's response
            noah_response = await self._generate_and_stream_noah_response(
                user_message, intent, entities, session, connection_id, db
            )

            # Store complete Noah's message
            noah_msg = await self._store_message(
                session_id=session_id,
                sender="noah",
                content=noah_response["content"],
                intent=intent,
                recommendations=noah_response.get("recommendations"),
                purchase_links=noah_response.get("purchase_links"),
                db=db
            )

            # Update conversation context
            updated_context = await self.agent_core.update_conversation_context(
                session_id, user_message, noah_response["content"], intent
            )

            # Update session context in database
            session.context = updated_context.get(
                "updated_context", session.context)
            session.last_activity = datetime.utcnow()
            db.commit()

            # Send final message completion
            await manager.send_personal_message(
                json.dumps({
                    "type": "noah_message_complete",
                    "message_id": noah_msg.message_id,
                    "timestamp": noah_msg.timestamp.isoformat()
                }),
                connection_id
            )

        except Exception as e:
            logger.error(f"Error processing user message: {e}")
            await manager.send_typing_indicator(session_id, False)

            # Send error response
            error_response = await self._generate_error_response(str(e))
            await self._stream_text_response(error_response, connection_id, "error")

    async def _generate_and_stream_noah_response(
        self,
        user_message: str,
        intent: Dict,
        entities: Dict,
        session: ConversationSession,
        connection_id: str,
        db: Session
    ) -> Dict[str, Any]:
        """Generate Noah's response and stream it in chunks."""
        intent_type = intent.get("intent", "general_conversation")

        if intent_type == "book_recommendation":
            return await self._handle_and_stream_book_recommendation(
                user_message, entities, session, connection_id, db
            )
        elif intent_type == "discovery_mode":
            return await self._handle_and_stream_discovery_mode(
                user_message, entities, session, connection_id, db
            )
        elif intent_type == "purchase_inquiry":
            return await self._handle_and_stream_purchase_inquiry(
                user_message, entities, session, connection_id, db
            )
        elif intent_type == "feedback":
            return await self._handle_and_stream_feedback(
                user_message, entities, session, connection_id, db
            )
        else:
            return await self._handle_and_stream_general_conversation(
                user_message, intent, session, connection_id
            )

    async def _stream_text_response(
        self,
        text: str,
        connection_id: str,
        message_type: str = "noah_message_chunk",
        chunk_size: int = 10,
        delay: float = 0.05
    ) -> None:
        """Stream text response in chunks to simulate typing."""
        words = text.split()
        current_chunk = ""

        for i, word in enumerate(words):
            current_chunk += word + " "

            # Send chunk when we reach chunk_size words or at the end
            if (i + 1) % chunk_size == 0 or i == len(words) - 1:
                await manager.send_personal_message(
                    json.dumps({
                        "type": message_type,
                        "content": current_chunk.strip(),
                        "is_final": i == len(words) - 1,
                        "timestamp": datetime.utcnow().isoformat()
                    }),
                    connection_id
                )
                current_chunk = ""

                # Add delay between chunks for natural typing effect
                if i < len(words) - 1:
                    await asyncio.sleep(delay)

    async def _handle_and_stream_book_recommendation(
        self,
        user_message: str,
        entities: Dict,
        session: ConversationSession,
        connection_id: str,
        db: Session
    ) -> Dict[str, Any]:
        """Handle book recommendation requests with streaming."""
        # Stop typing indicator before starting to stream
        await manager.send_typing_indicator(session.session_id, False)

        # Mock recommendations for now
        recommendations = [
            {
                "id": "book_1",
                "title": "The Seven Husbands of Evelyn Hugo",
                "author": "Taylor Jenkins Reid",
                "description": "A captivating novel about a reclusive Hollywood icon who finally decides to tell her story.",
                "interestScore": 0.92,
                "readingLevel": "Intermediate",
                "estimatedReadingTime": 420
            },
            {
                "id": "book_2",
                "title": "Educated",
                "author": "Tara Westover",
                "description": "A powerful memoir about education, family, and the struggle between loyalty and independence.",
                "interestScore": 0.88,
                "readingLevel": "Advanced",
                "estimatedReadingTime": 380
            }
        ]

        # Generate response content
        response_content = await self.agent_core.generate_response(
            user_message,
            {"intent": "book_recommendation"},
            session.context or {},
            recommendations
        )

        # Stream the text response
        await self._stream_text_response(response_content, connection_id)

        # Send recommendations as structured data
        await manager.send_personal_message(
            json.dumps({
                "type": "noah_recommendations",
                "recommendations": recommendations,
                "timestamp": datetime.utcnow().isoformat()
            }),
            connection_id
        )

        return {
            "content": response_content,
            "type": "recommendation",
            "recommendations": recommendations
        }

    async def _handle_and_stream_discovery_mode(
        self,
        user_message: str,
        entities: Dict,
        session: ConversationSession,
        connection_id: str,
        db: Session
    ) -> Dict[str, Any]:
        """Handle discovery mode requests with streaming."""
        await manager.send_typing_indicator(session.session_id, False)

        # Mock discovery recommendation
        discovery_recommendation = [
            {
                "id": "book_discovery",
                "title": "Klara and the Sun",
                "author": "Kazuo Ishiguro",
                "description": "A thought-provoking story told from the perspective of an artificial friend.",
                "interestScore": 0.75,
                "readingLevel": "Intermediate",
                "estimatedReadingTime": 300
            }
        ]

        response_content = await self.agent_core.generate_response(
            user_message,
            {"intent": "discovery_mode"},
            session.context or {},
            discovery_recommendation
        )

        # Stream the text response
        await self._stream_text_response(response_content, connection_id)

        # Send discovery recommendation
        await manager.send_personal_message(
            json.dumps({
                "type": "noah_recommendations",
                "recommendations": discovery_recommendation,
                "is_discovery": True,
                "timestamp": datetime.utcnow().isoformat()
            }),
            connection_id
        )

        # Update session context
        if session.context:
            session.context["discovery_mode_active"] = True

        return {
            "content": response_content,
            "type": "recommendation",
            "recommendations": discovery_recommendation
        }

    async def _handle_and_stream_purchase_inquiry(
        self,
        user_message: str,
        entities: Dict,
        session: ConversationSession,
        connection_id: str,
        db: Session
    ) -> Dict[str, Any]:
        """Handle purchase inquiry requests with streaming."""
        await manager.send_typing_indicator(session.session_id, False)

        # Mock purchase links
        purchase_links = [
            {
                "id": "amazon_link",
                "type": "amazon",
                "url": "https://amazon.com/example",
                "displayText": "Buy on Amazon",
                "format": "physical",
                "price": "$14.99",
                "availability": "available"
            },
            {
                "id": "search_link",
                "type": "web_search",
                "url": "https://google.com/search?q=book+title",
                "displayText": "Search for more options",
                "availability": "unknown"
            }
        ]

        response_content = await self.agent_core.generate_response(
            user_message,
            {"intent": "purchase_inquiry"},
            session.context or {},
            []
        )

        # Stream the text response
        await self._stream_text_response(response_content, connection_id)

        # Send purchase links
        await manager.send_personal_message(
            json.dumps({
                "type": "noah_purchase_links",
                "purchase_links": purchase_links,
                "timestamp": datetime.utcnow().isoformat()
            }),
            connection_id
        )

        return {
            "content": response_content,
            "type": "purchase_links",
            "purchase_links": purchase_links
        }

    async def _handle_and_stream_feedback(
        self,
        user_message: str,
        entities: Dict,
        session: ConversationSession,
        connection_id: str,
        db: Session
    ) -> Dict[str, Any]:
        """Handle user feedback on recommendations with streaming."""
        await manager.send_typing_indicator(session.session_id, False)

        # Extract feedback information
        book_id = entities.get("book_id")
        feedback_type = entities.get("feedback_type")

        # Generate appropriate response based on feedback
        if feedback_type == "interested":
            response_content = "Great! I'm glad you're interested in that recommendation. I'll remember your preference for similar books. Would you like me to find where you can purchase it?"
        elif feedback_type == "not_interested":
            response_content = "Thanks for letting me know! I'll use this feedback to improve future recommendations. What kind of books would you prefer instead?"
        else:
            response_content = "Thank you for your feedback! This helps me learn your preferences better."

        # Stream the text response
        await self._stream_text_response(response_content, connection_id)

        # TODO: Store feedback in user profile for learning
        # This would integrate with the user profile service to update preferences

        return {
            "content": response_content,
            "type": "text"
        }

    async def _handle_and_stream_general_conversation(
        self,
        user_message: str,
        intent: Dict,
        session: ConversationSession,
        connection_id: str
    ) -> Dict[str, Any]:
        """Handle general conversation with streaming."""
        await manager.send_typing_indicator(session.session_id, False)

        response_content = await self.agent_core.generate_response(
            user_message,
            intent,
            session.context or {}
        )

        # Stream the text response
        await self._stream_text_response(response_content, connection_id)

        return {
            "content": response_content,
            "type": "text"
        }

    async def _get_or_create_session(
        self,
        session_id: str,
        db: Session
    ) -> ConversationSession:
        """Get existing session or create a new one."""
        session = db.query(ConversationSession).filter(
            ConversationSession.session_id == session_id
        ).first()

        if not session:
            # Extract user_id from session_id (format: session_userId_timestamp)
            parts = session_id.split('_')
            user_id = parts[1] if len(parts) >= 2 else "anonymous"

            # Ensure user profile exists
            await self._ensure_user_profile_exists(user_id, db)

            session = ConversationSession(
                session_id=session_id,
                user_id=user_id,
                context={
                    "current_topic": None,
                    "recent_recommendations": [],
                    "user_mood": None,
                    "discovery_mode_active": False,
                    "preferred_language": "english"
                }
            )
            db.add(session)
            db.commit()
            db.refresh(session)

        return session

    async def _ensure_user_profile_exists(self, user_id: str, db: Session) -> UserProfile:
        """Ensure a user profile exists, create if it doesn't."""
        user_profile = db.query(UserProfile).filter(
            UserProfile.user_id == user_id
        ).first()

        if not user_profile:
            # Create a new user profile with default settings
            user_profile = UserProfile(
                user_id=user_id,
                preferences={
                    "topics": [],
                    "content_types": [],
                    "contextual_preferences": [],
                    "evolution_history": []
                },
                reading_levels={
                    "english": {"level": 5.0, "confidence": 0.5},
                    "japanese": {"level": 3.0, "confidence": 0.5}
                }
            )
            db.add(user_profile)
            db.commit()
            db.refresh(user_profile)
            logger.info(f"Created new user profile for user_id: {user_id}")

        return user_profile

    async def _store_message(
        self,
        session_id: str,
        sender: str,
        content: str,
        intent: Optional[Dict] = None,
        recommendations: Optional[List[Dict]] = None,
        purchase_links: Optional[List[Dict]] = None,
        db: Session = None
    ) -> ConversationMessage:
        """Store a message in the database."""
        message_id = f"msg_{datetime.utcnow().timestamp()}_{sender}"

        message = ConversationMessage(
            message_id=message_id,
            session_id=session_id,
            sender=sender,
            content=content,
            intent=intent,
            recommendations=recommendations,
            purchase_links=purchase_links
        )

        db.add(message)
        db.commit()
        db.refresh(message)

        return message

    async def _generate_noah_response(
        self,
        user_message: str,
        intent: Dict,
        entities: Dict,
        session: ConversationSession,
        db: Session
    ) -> Dict[str, Any]:
        """Generate Noah's response based on intent and context."""
        intent_type = intent.get("intent", "general_conversation")

        if intent_type == "book_recommendation":
            return await self._handle_book_recommendation(
                user_message, entities, session, db
            )
        elif intent_type == "discovery_mode":
            return await self._handle_discovery_mode(
                user_message, entities, session, db
            )
        elif intent_type == "purchase_inquiry":
            return await self._handle_purchase_inquiry(
                user_message, entities, session, db
            )
        else:
            return await self._handle_general_conversation(
                user_message, intent, session
            )

    async def _handle_book_recommendation(
        self,
        user_message: str,
        entities: Dict,
        session: ConversationSession,
        db: Session
    ) -> Dict[str, Any]:
        """Handle book recommendation requests."""
        # Mock recommendations for now (to be replaced with actual recommendation engine)
        recommendations = [
            {
                "id": "book_1",
                "title": "The Seven Husbands of Evelyn Hugo",
                "author": "Taylor Jenkins Reid",
                "description": "A captivating novel about a reclusive Hollywood icon who finally decides to tell her story.",
                "interestScore": 0.92,
                "readingLevel": "Intermediate",
                "estimatedReadingTime": 420
            },
            {
                "id": "book_2",
                "title": "Educated",
                "author": "Tara Westover",
                "description": "A powerful memoir about education, family, and the struggle between loyalty and independence.",
                "interestScore": 0.88,
                "readingLevel": "Advanced",
                "estimatedReadingTime": 380
            }
        ]

        response_content = await self.agent_core.generate_response(
            user_message,
            {"intent": "book_recommendation"},
            session.context or {},
            recommendations
        )

        return {
            "content": response_content,
            "type": "recommendation",
            "recommendations": recommendations
        }

    async def _handle_discovery_mode(
        self,
        user_message: str,
        entities: Dict,
        session: ConversationSession,
        db: Session
    ) -> Dict[str, Any]:
        """Handle discovery mode requests."""
        # Mock discovery recommendation
        discovery_recommendation = [
            {
                "id": "book_discovery",
                "title": "Klara and the Sun",
                "author": "Kazuo Ishiguro",
                "description": "A thought-provoking story told from the perspective of an artificial friend.",
                "interestScore": 0.75,
                "readingLevel": "Intermediate",
                "estimatedReadingTime": 300
            }
        ]

        response_content = await self.agent_core.generate_response(
            user_message,
            {"intent": "discovery_mode"},
            session.context or {},
            discovery_recommendation
        )

        # Update session context to indicate discovery mode is active
        if session.context:
            session.context["discovery_mode_active"] = True

        return {
            "content": response_content,
            "type": "recommendation",
            "recommendations": discovery_recommendation
        }

    async def _handle_purchase_inquiry(
        self,
        user_message: str,
        entities: Dict,
        session: ConversationSession,
        db: Session
    ) -> Dict[str, Any]:
        """Handle purchase inquiry requests."""
        # Mock purchase links
        purchase_links = [
            {
                "id": "amazon_link",
                "type": "amazon",
                "url": "https://amazon.com/example",
                "displayText": "Buy on Amazon",
                "format": "physical",
                "price": "$14.99",
                "availability": "available"
            },
            {
                "id": "search_link",
                "type": "web_search",
                "url": "https://google.com/search?q=book+title",
                "displayText": "Search for more options",
                "availability": "unknown"
            }
        ]

        response_content = await self.agent_core.generate_response(
            user_message,
            {"intent": "purchase_inquiry"},
            session.context or {},
            []
        )

        return {
            "content": response_content,
            "type": "purchase_links",
            "purchase_links": purchase_links
        }

    async def _handle_general_conversation(
        self,
        user_message: str,
        intent: Dict,
        session: ConversationSession
    ) -> Dict[str, Any]:
        """Handle general conversation."""
        response_content = await self.agent_core.generate_response(
            user_message,
            intent,
            session.context or {}
        )

        return {
            "content": response_content,
            "type": "text"
        }

    async def _generate_error_response(self, error: str) -> str:
        """Generate a user-friendly error response."""
        return "I'm sorry, I encountered an issue processing your message. Please try again, and I'll do my best to help you with your reading needs!"

    async def get_conversation_history(
        self,
        session_id: str,
        limit: int = 50,
        db: Session = None
    ) -> List[Dict]:
        """Get conversation history for a session."""
        messages = db.query(ConversationMessage).filter(
            ConversationMessage.session_id == session_id
        ).order_by(ConversationMessage.timestamp.asc()).limit(limit).all()

        return [
            {
                "message_id": msg.message_id,
                "sender": msg.sender,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat(),
                "type": "recommendation" if msg.recommendations else "purchase_links" if msg.purchase_links else "text",
                "metadata": {
                    "recommendations": msg.recommendations,
                    "purchase_links": msg.purchase_links
                }
            }
            for msg in messages
        ]
