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
                        "recommendations": noah_response.get("recommendations")
                    }
                },
                "intent": intent,
                "entities": entities
            }

        except Exception as e:
            logger.error(f"Error processing user message: {e}")

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
        else:
            return await self._handle_general_conversation(
                user_message, intent, session
            )

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
            recommendations=recommendations
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
        # Use real recommendation engine
        from src.services.recommendation_engine import contextual_recommendation_engine
        
        try:
            # Get user ID from session or use default
            user_id = session.user_id if hasattr(session, 'user_id') else "default_user"
            
            # Generate real recommendations
            raw_recommendations = await contextual_recommendation_engine.generate_contextual_recommendations(
                user_id=user_id,
                limit=5,
                language="english",
                db=db
            )
            
            # Convert to expected format
            recommendations = []
            for rec in raw_recommendations:
                recommendations.append({
                    "id": rec["content_id"],
                    "title": rec["title"],
                    "author": rec["metadata"].get("author", "Unknown Author"),
                    "description": rec["metadata"].get("genre", "Fiction"),
                    "interestScore": round(rec["recommendation_score"], 2),
                    "readingLevel": rec["metadata"].get("difficulty_level", "Intermediate").title(),
                    "estimatedReadingTime": rec["metadata"].get("estimated_reading_time", 300),
                    "genre": rec["metadata"].get("genre", "Fiction"),
                    "recommendation_reason": rec.get("recommendation_reason", "Recommended based on your preferences")
                })
            
            # Fallback if no recommendations found
            if not recommendations:
                recommendations = [
                    {
                        "id": "fallback_1",
                        "title": "Popular Fiction Selection",
                        "author": "Various Authors",
                        "description": "A curated selection of popular fiction",
                        "interestScore": 0.75,
                        "readingLevel": "Intermediate",
                        "estimatedReadingTime": 300,
                        "genre": "Fiction",
                        "recommendation_reason": "Popular among readers"
                    }
                ]
                
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            # Fallback recommendations on error
            recommendations = [
                {
                    "id": "error_fallback",
                    "title": "Reading Recommendation",
                    "author": "System",
                    "description": "We're working on personalized recommendations for you",
                    "interestScore": 0.5,
                    "readingLevel": "Intermediate",
                    "estimatedReadingTime": 300,
                    "genre": "General",
                    "recommendation_reason": "System recommendation"
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
        # Use real discovery engine
        from src.services.discovery_engine import discovery_engine
        
        try:
            # Get user ID from session or use default
            user_id = session.user_id if hasattr(session, 'user_id') else "default_user"
            
            # Generate real discovery recommendations
            raw_discovery = await discovery_engine.generate_discovery_recommendations(
                user_id=user_id,
                limit=3,
                language="english",
                db=db
            )
            
            # Convert to expected format
            discovery_recommendation = []
            for rec in raw_discovery:
                discovery_recommendation.append({
                    "id": rec["content_id"],
                    "title": rec["title"],
                    "author": rec["metadata"].get("author", "Unknown Author"),
                    "description": rec.get("discovery_reason", "A serendipitous discovery for you"),
                    "interestScore": round(rec["divergence_score"], 2),
                    "readingLevel": rec["metadata"].get("difficulty_level", "Intermediate").title(),
                    "estimatedReadingTime": rec["metadata"].get("estimated_reading_time", 300),
                    "genre": rec["metadata"].get("genre", "Fiction"),
                    "is_discovery": True,
                    "discovery_reason": rec.get("discovery_reason", "Explores new territory for you")
                })
            
            # Fallback if no discovery recommendations found
            if not discovery_recommendation:
                discovery_recommendation = [
                    {
                        "id": "discovery_fallback",
                        "title": "Literary Discovery",
                        "author": "Various Authors",
                        "description": "A curated discovery selection",
                        "interestScore": 0.65,
                        "readingLevel": "Intermediate",
                        "estimatedReadingTime": 300,
                        "genre": "Literary Fiction",
                        "is_discovery": True,
                        "discovery_reason": "Expands your reading horizons"
                    }
                ]
                
        except Exception as e:
            logger.error(f"Error generating discovery recommendations: {e}")
            # Fallback discovery recommendation on error
            discovery_recommendation = [
                {
                    "id": "discovery_error_fallback",
                    "title": "Discovery Mode",
                    "author": "System",
                    "description": "We're working on discovery recommendations for you",
                    "interestScore": 0.5,
                    "readingLevel": "Intermediate",
                    "estimatedReadingTime": 300,
                    "genre": "General",
                    "is_discovery": True,
                    "discovery_reason": "System discovery"
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
                "type": "recommendation" if msg.recommendations else "text",
                "metadata": {
                    "recommendations": msg.recommendations
                }
            }
            for msg in messages
        ]
