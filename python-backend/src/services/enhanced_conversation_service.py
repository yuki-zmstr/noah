"""Enhanced conversation service with Strands agents integration."""

import json
import logging
import asyncio
from typing import Dict, List, Optional, Any, AsyncGenerator
from datetime import datetime
from sqlalchemy.orm import Session

from src.models.conversation import ConversationSession, ConversationMessage
from src.models.user_profile import UserProfile
from src.services.agent_core import AgentCoreService
from src.services.strands_agent_service import StrandsAgentService
from src.services.ai_response_service import AIResponseService
from src.services.strands_config import strands_config
from src.config import settings

logger = logging.getLogger(__name__)


class EnhancedConversationService:
    """Enhanced conversation service using Strands agents with HTTP streaming."""

    def __init__(self):
        self.agent_core = AgentCoreService()
        self.ai_response_service = AIResponseService()
        
        # Initialize Strands agent service if enabled
        self.strands_service = None
        if settings.strands_enabled and strands_config.openai_api_key:
            try:
                self.strands_service = StrandsAgentService()
                logger.info("Strands agent service initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize Strands agent service: {e}")
                logger.info("Falling back to AWS Agent Core")
        
        # Determine which service to use
        self.use_strands = self.strands_service is not None
        logger.info(f"Using {'Strands agents' if self.use_strands else 'AI Response Service with Agent Core'} for conversation processing")

    async def process_conversation_stream(
        self,
        user_message: str,
        user_id: str,
        session_id: str,
        db: Session,
        metadata: Optional[Dict] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Process a conversation and yield streaming responses."""
        try:
            # Get or create session
            session = await self._get_or_create_session(session_id, user_id, db)
            
            # Store user message
            user_msg = await self._store_message(
                session_id=session_id,
                sender="user",
                content=user_message,
                db=db
            )
            
            # Yield user message confirmation
            yield {
                "type": "user_message_received",
                "message_id": user_msg.message_id,
                "content": user_msg.content,
                "timestamp": user_msg.timestamp.isoformat(),
                "sender": "user"
            }
            
            # Process with appropriate service
            if self.use_strands:
                async for chunk in self._process_with_strands_streaming(
                    session, user_message, db, metadata
                ):
                    yield chunk
            else:
                async for chunk in self._process_with_agent_core_streaming(
                    session, user_message, db, metadata
                ):
                    yield chunk
                    
        except Exception as e:
            logger.error(f"Error processing conversation stream: {e}")
            yield {
                "type": "error",
                "content": "I'm sorry, I encountered an issue processing your message. Please try again!",
                "timestamp": datetime.utcnow().isoformat()
            }

    async def _process_with_strands_streaming(
        self,
        session: ConversationSession,
        user_message: str,
        db: Session,
        metadata: Optional[Dict] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Process message using Strands agents with streaming."""
        try:
            # Extract user_id from session
            user_id = session.user_id
            
            # Get conversation history for context
            conversation_history = await self._get_recent_conversation_history(session.session_id, db)
            
            # Stream response from Strands agent
            full_response_content = ""
            tool_calls = []
            
            async for chunk in self.strands_service.stream_conversation(
                user_message=user_message,
                user_id=user_id,
                conversation_context=session.context,
                metadata=metadata
            ):
                if chunk["type"] == "content_chunk":
                    # Stream content chunk
                    yield {
                        "type": "content_chunk",
                        "content": chunk["content"],
                        "is_final": chunk["is_final"],
                        "timestamp": chunk["timestamp"]
                    }
                    
                    full_response_content += chunk["content"]
                    
                    # Collect tool calls
                    if chunk.get("tool_calls"):
                        tool_calls.extend(chunk["tool_calls"])
                
                elif chunk["type"] == "error":
                    yield {
                        "type": "error",
                        "content": chunk["content"],
                        "timestamp": chunk["timestamp"]
                    }
                    full_response_content = chunk["content"]
                    break
            
            # Process tool calls and send structured data
            recommendations = []
            
            for tool_call in tool_calls:
                if tool_call["name"] == "get_recommendations":
                    recommendations.extend(tool_call.get("result", []))
                elif tool_call["name"] == "discovery_mode":
                    discovery_recs = tool_call.get("result", [])
                    for rec in discovery_recs:
                        rec["is_discovery"] = True
                    recommendations.extend(discovery_recs)
            
            # Send recommendations if available
            if recommendations:
                yield {
                    "type": "recommendations",
                    "recommendations": recommendations,
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            # Store Noah's complete message
            noah_msg = await self._store_message(
                session_id=session.session_id,
                sender="noah",
                content=full_response_content,
                recommendations=recommendations if recommendations else None,
                db=db
            )
            
            # Update session context
            session.last_activity = datetime.utcnow()
            db.commit()
            
            # Send completion signal
            yield {
                "type": "complete",
                "message_id": noah_msg.message_id,
                "timestamp": noah_msg.timestamp.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing with Strands agents: {e}")
            yield {
                "type": "error",
                "content": "I'm sorry, I encountered an issue processing your message. Please try again!",
                "timestamp": datetime.utcnow().isoformat()
            }

    async def _process_with_agent_core_streaming(
        self,
        session: ConversationSession,
        user_message: str,
        db: Session,
        metadata: Optional[Dict] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Process message using AWS Agent Core with streaming (fallback)."""
        try:
            # Analyze user intent and extract entities
            intent = await self.agent_core.analyze_intent(
                user_message,
                session.context,
                metadata
            )
            entities = await self.agent_core.extract_entities(user_message)

            # Generate and stream Noah's response
            async for chunk in self._generate_and_stream_noah_response_agent_core(
                user_message, intent, entities, session, db
            ):
                yield chunk
                
        except Exception as e:
            logger.error(f"Error processing with Agent Core: {e}")
            yield {
                "type": "error",
                "content": "I'm sorry, I encountered an issue processing your message. Please try again!",
                "timestamp": datetime.utcnow().isoformat()
            }

    async def _generate_and_stream_noah_response_agent_core(
        self,
        user_message: str,
        intent: Dict,
        entities: Dict,
        session: ConversationSession,
        db: Session
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Generate Noah's response using AI Response Service and stream it in chunks."""
        intent_type = intent.get("intent", "general_conversation")

        # Get user profile for context
        user_profile = await self._get_user_profile_data(session.user_id, db)
        
        # Get conversation history for context
        conversation_history = await self._get_recent_conversation_history(session.session_id, db)

        if intent_type == "book_recommendation":
            async for chunk in self._handle_and_stream_book_recommendation_ai(
                user_message, intent, entities, session, db, user_profile, conversation_history
            ):
                yield chunk
        elif intent_type == "discovery_mode":
            async for chunk in self._handle_and_stream_discovery_mode_ai(
                user_message, intent, entities, session, db, user_profile, conversation_history
            ):
                yield chunk
        elif intent_type == "purchase_inquiry":
            async for chunk in self._handle_and_stream_purchase_inquiry_ai(
                user_message, intent, entities, session, db, user_profile, conversation_history
            ):
                yield chunk
        elif intent_type == "feedback":
            async for chunk in self._handle_and_stream_feedback_ai(
                user_message, intent, entities, session, db, user_profile, conversation_history
            ):
                yield chunk
        else:
            async for chunk in self._handle_and_stream_general_conversation_ai(
                user_message, intent, session, db, user_profile, conversation_history
            ):
                yield chunk

    async def _stream_text_response(
        self,
        text: str,
        chunk_size: int = 10,
        delay: float = 0.05
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream text response in chunks to simulate typing."""
        words = text.split()
        current_chunk = ""

        for i, word in enumerate(words):
            current_chunk += word + " "

            # Send chunk when we reach chunk_size words or at the end
            if (i + 1) % chunk_size == 0 or i == len(words) - 1:
                yield {
                    "type": "content_chunk",
                    "content": current_chunk.strip(),
                    "is_final": i == len(words) - 1,
                    "timestamp": datetime.utcnow().isoformat()
                }
                current_chunk = ""

                # Add delay between chunks for natural typing effect
                if i < len(words) - 1:
                    await asyncio.sleep(delay)

    # New AI-powered response handlers
    async def _handle_and_stream_book_recommendation_ai(
        self,
        user_message: str,
        intent: Dict,
        entities: Dict,
        session: ConversationSession,
        db: Session,
        user_profile: Optional[Dict] = None,
        conversation_history: Optional[List[Dict]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Handle book recommendation requests with AI-generated streaming responses."""
        # Mock recommendations for now (will be replaced by actual recommendation engine)
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

        # Generate AI response with streaming
        full_response_content = ""
        async for chunk in self.ai_response_service.generate_streaming_response(
            user_message=user_message,
            intent=intent,
            context=session.context or {},
            conversation_history=conversation_history,
            recommendations=recommendations,
            user_profile=user_profile
        ):
            # Stream the content chunk
            yield {
                "type": "content_chunk",
                "content": chunk,
                "is_final": False,
                "timestamp": datetime.utcnow().isoformat()
            }
            full_response_content += chunk

        # Send final content chunk
        yield {
            "type": "content_chunk",
            "content": "",
            "is_final": True,
            "timestamp": datetime.utcnow().isoformat()
        }

        # Send recommendations as structured data
        yield {
            "type": "recommendations",
            "recommendations": recommendations,
            "timestamp": datetime.utcnow().isoformat()
        }

        # Store complete message
        noah_msg = await self._store_message(
            session_id=session.session_id,
            sender="noah",
            content=full_response_content,
            recommendations=recommendations,
            db=db
        )

        # Send completion
        yield {
            "type": "complete",
            "message_id": noah_msg.message_id,
            "timestamp": noah_msg.timestamp.isoformat()
        }

    async def _handle_and_stream_discovery_mode_ai(
        self,
        user_message: str,
        intent: Dict,
        entities: Dict,
        session: ConversationSession,
        db: Session,
        user_profile: Optional[Dict] = None,
        conversation_history: Optional[List[Dict]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Handle discovery mode requests with AI-generated streaming responses."""
        # Mock discovery recommendation
        discovery_recommendation = [
            {
                "id": "book_discovery",
                "title": "Klara and the Sun",
                "author": "Kazuo Ishiguro",
                "description": "A thought-provoking story told from the perspective of an artificial friend.",
                "interestScore": 0.75,
                "readingLevel": "Intermediate",
                "estimatedReadingTime": 300,
                "is_discovery": True
            }
        ]

        # Generate AI response with streaming
        full_response_content = ""
        async for chunk in self.ai_response_service.generate_streaming_response(
            user_message=user_message,
            intent=intent,
            context=session.context or {},
            conversation_history=conversation_history,
            recommendations=discovery_recommendation,
            user_profile=user_profile
        ):
            # Stream the content chunk
            yield {
                "type": "content_chunk",
                "content": chunk,
                "is_final": False,
                "timestamp": datetime.utcnow().isoformat()
            }
            full_response_content += chunk

        # Send final content chunk
        yield {
            "type": "content_chunk",
            "content": "",
            "is_final": True,
            "timestamp": datetime.utcnow().isoformat()
        }

        # Send discovery recommendation
        yield {
            "type": "recommendations",
            "recommendations": discovery_recommendation,
            "timestamp": datetime.utcnow().isoformat()
        }

        # Update session context
        if session.context:
            session.context["discovery_mode_active"] = True

        # Store complete message
        noah_msg = await self._store_message(
            session_id=session.session_id,
            sender="noah",
            content=full_response_content,
            recommendations=discovery_recommendation,
            db=db
        )

        # Send completion
        yield {
            "type": "complete",
            "message_id": noah_msg.message_id,
            "timestamp": noah_msg.timestamp.isoformat()
        }

    async def _handle_and_stream_purchase_inquiry_ai(
        self,
        user_message: str,
        intent: Dict,
        entities: Dict,
        session: ConversationSession,
        db: Session,
        user_profile: Optional[Dict] = None,
        conversation_history: Optional[List[Dict]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Handle purchase inquiry with AI-generated streaming responses."""
        # Generate AI response with streaming
        full_response_content = ""
        async for chunk in self.ai_response_service.generate_streaming_response(
            user_message=user_message,
            intent=intent,
            context=session.context or {},
            conversation_history=conversation_history,
            user_profile=user_profile
        ):
            # Stream the content chunk
            yield {
                "type": "content_chunk",
                "content": chunk,
                "is_final": False,
                "timestamp": datetime.utcnow().isoformat()
            }
            full_response_content += chunk

        # Send final content chunk
        yield {
            "type": "content_chunk",
            "content": "",
            "is_final": True,
            "timestamp": datetime.utcnow().isoformat()
        }

        # Store complete message
        noah_msg = await self._store_message(
            session_id=session.session_id,
            sender="noah",
            content=full_response_content,
            db=db
        )

        # Send completion
        yield {
            "type": "complete",
            "message_id": noah_msg.message_id,
            "timestamp": noah_msg.timestamp.isoformat()
        }

    async def _handle_and_stream_feedback_ai(
        self,
        user_message: str,
        intent: Dict,
        entities: Dict,
        session: ConversationSession,
        db: Session,
        user_profile: Optional[Dict] = None,
        conversation_history: Optional[List[Dict]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Handle user feedback on recommendations with AI-generated streaming responses."""
        # Generate AI response with streaming
        full_response_content = ""
        async for chunk in self.ai_response_service.generate_streaming_response(
            user_message=user_message,
            intent=intent,
            context=session.context or {},
            conversation_history=conversation_history,
            user_profile=user_profile
        ):
            # Stream the content chunk
            yield {
                "type": "content_chunk",
                "content": chunk,
                "is_final": False,
                "timestamp": datetime.utcnow().isoformat()
            }
            full_response_content += chunk

        # Send final content chunk
        yield {
            "type": "content_chunk",
            "content": "",
            "is_final": True,
            "timestamp": datetime.utcnow().isoformat()
        }

        # Store complete message
        noah_msg = await self._store_message(
            session_id=session.session_id,
            sender="noah",
            content=full_response_content,
            db=db
        )

        # Send completion
        yield {
            "type": "complete",
            "message_id": noah_msg.message_id,
            "timestamp": noah_msg.timestamp.isoformat()
        }

    async def _handle_and_stream_general_conversation_ai(
        self,
        user_message: str,
        intent: Dict,
        session: ConversationSession,
        db: Session,
        user_profile: Optional[Dict] = None,
        conversation_history: Optional[List[Dict]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Handle general conversation with AI-generated streaming responses."""
        # Generate AI response with streaming
        full_response_content = ""
        async for chunk in self.ai_response_service.generate_streaming_response(
            user_message=user_message,
            intent=intent,
            context=session.context or {},
            conversation_history=conversation_history,
            user_profile=user_profile
        ):
            # Stream the content chunk
            yield {
                "type": "content_chunk",
                "content": chunk,
                "is_final": False,
                "timestamp": datetime.utcnow().isoformat()
            }
            full_response_content += chunk

        # Send final content chunk
        yield {
            "type": "content_chunk",
            "content": "",
            "is_final": True,
            "timestamp": datetime.utcnow().isoformat()
        }

        # Store complete message
        noah_msg = await self._store_message(
            session_id=session.session_id,
            sender="noah",
            content=full_response_content,
            db=db
        )

        # Send completion
        yield {
            "type": "complete",
            "message_id": noah_msg.message_id,
            "timestamp": noah_msg.timestamp.isoformat()
        }

    # Legacy hardcoded response handlers (kept for backward compatibility)
    async def _handle_and_stream_book_recommendation(
        self,
        user_message: str,
        entities: Dict,
        session: ConversationSession,
        db: Session
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Handle book recommendation requests with streaming."""
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
        async for chunk in self._stream_text_response(response_content):
            yield chunk

        # Send recommendations as structured data
        yield {
            "type": "recommendations",
            "recommendations": recommendations,
            "timestamp": datetime.utcnow().isoformat()
        }

        # Store complete message
        noah_msg = await self._store_message(
            session_id=session.session_id,
            sender="noah",
            content=response_content,
            recommendations=recommendations,
            db=db
        )

        # Send completion
        yield {
            "type": "complete",
            "message_id": noah_msg.message_id,
            "timestamp": noah_msg.timestamp.isoformat()
        }

    async def _handle_and_stream_discovery_mode(
        self,
        user_message: str,
        entities: Dict,
        session: ConversationSession,
        db: Session
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Handle discovery mode requests with streaming."""
        # Mock discovery recommendation
        discovery_recommendation = [
            {
                "id": "book_discovery",
                "title": "Klara and the Sun",
                "author": "Kazuo Ishiguro",
                "description": "A thought-provoking story told from the perspective of an artificial friend.",
                "interestScore": 0.75,
                "readingLevel": "Intermediate",
                "estimatedReadingTime": 300,
                "is_discovery": True
            }
        ]

        response_content = await self.agent_core.generate_response(
            user_message,
            {"intent": "discovery_mode"},
            session.context or {},
            discovery_recommendation
        )

        # Stream the text response
        async for chunk in self._stream_text_response(response_content):
            yield chunk

        # Send discovery recommendation
        yield {
            "type": "recommendations",
            "recommendations": discovery_recommendation,
            "timestamp": datetime.utcnow().isoformat()
        }

        # Update session context
        if session.context:
            session.context["discovery_mode_active"] = True

        # Store complete message
        noah_msg = await self._store_message(
            session_id=session.session_id,
            sender="noah",
            content=response_content,
            recommendations=discovery_recommendation,
            db=db
        )

        # Send completion
        yield {
            "type": "complete",
            "message_id": noah_msg.message_id,
            "timestamp": noah_msg.timestamp.isoformat()
        }

    async def _handle_and_stream_purchase_inquiry(
        self,
        user_message: str,
        entities: Dict,
        session: ConversationSession,
        db: Session
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Handle purchase inquiry with streaming."""
        response_content = "I understand you're interested in that book! While I can't generate purchase links, I'd be happy to help you find more books you might enjoy or discuss what you liked about this recommendation."

        # Stream the text response
        async for chunk in self._stream_text_response(response_content):
            yield chunk

        # Store complete message
        noah_msg = await self._store_message(
            session_id=session.session_id,
            sender="noah",
            content=response_content,
            db=db
        )

        # Send completion
        yield {
            "type": "complete",
            "message_id": noah_msg.message_id,
            "timestamp": noah_msg.timestamp.isoformat()
        }

    async def _handle_and_stream_feedback(
        self,
        user_message: str,
        entities: Dict,
        session: ConversationSession,
        db: Session
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Handle user feedback on recommendations with streaming."""
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
        async for chunk in self._stream_text_response(response_content):
            yield chunk

        # Store complete message
        noah_msg = await self._store_message(
            session_id=session.session_id,
            sender="noah",
            content=response_content,
            db=db
        )

        # Send completion
        yield {
            "type": "complete",
            "message_id": noah_msg.message_id,
            "timestamp": noah_msg.timestamp.isoformat()
        }

    async def _handle_and_stream_general_conversation(
        self,
        user_message: str,
        intent: Dict,
        session: ConversationSession
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Handle general conversation with streaming."""
        response_content = await self.agent_core.generate_response(
            user_message,
            intent,
            session.context or {}
        )

        # Stream the text response
        async for chunk in self._stream_text_response(response_content):
            yield chunk

        # Store complete message
        noah_msg = await self._store_message(
            session_id=session.session_id,
            sender="noah",
            content=response_content,
            db=db
        )

        # Send completion
        yield {
            "type": "complete",
            "message_id": noah_msg.message_id,
            "timestamp": noah_msg.timestamp.isoformat()
        }

    async def get_conversation_history(
        self,
        session_id: str,
        limit: int = 50,
        db: Session = None
    ) -> List[Dict]:
        """Get conversation history for a session."""
        messages = db.query(ConversationMessage).filter(
            ConversationMessage.session_id == session_id
        ).order_by(ConversationMessage.timestamp.desc()).limit(limit).all()

        return [
            {
                "message_id": msg.message_id,
                "sender": msg.sender,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat(),
                "recommendations": msg.recommendations,
                "intent": msg.intent
            }
            for msg in reversed(messages)  # Reverse to get chronological order
        ]

    async def _get_or_create_session(
        self,
        session_id: str,
        user_id: str,
        db: Session
    ) -> ConversationSession:
        """Get existing session or create a new one."""
        session = db.query(ConversationSession).filter(
            ConversationSession.session_id == session_id
        ).first()

        if not session:
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

    async def _get_recent_conversation_history(
        self,
        session_id: str,
        db: Session,
        limit: int = 10
    ) -> List[Dict]:
        """Get recent conversation history for context."""
        messages = db.query(ConversationMessage).filter(
            ConversationMessage.session_id == session_id
        ).order_by(ConversationMessage.timestamp.desc()).limit(limit).all()

        return [
            {
                "sender": msg.sender,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat()
            }
            for msg in reversed(messages)  # Reverse to get chronological order
        ]

    async def _get_user_profile_data(self, user_id: str, db: Session) -> Optional[Dict]:
        """Get user profile data for AI context."""
        try:
            user_profile = db.query(UserProfile).filter(
                UserProfile.user_id == user_id
            ).first()
            
            if user_profile:
                return {
                    "preferences": user_profile.preferences,
                    "reading_levels": user_profile.reading_levels,
                    "last_updated": user_profile.last_updated.isoformat() if user_profile.last_updated else None
                }
            return None
        except Exception as e:
            logger.error(f"Error getting user profile data: {e}")
            return None

    def get_service_info(self) -> Dict[str, Any]:
        """Get information about the conversation service configuration."""
        ai_service_info = self.ai_response_service.get_service_info()
        
        return {
            "service_type": "Strands Agents" if self.use_strands else "AI Response Service with Agent Core",
            "strands_enabled": settings.strands_enabled,
            "strands_available": self.strands_service is not None,
            "ai_response_service": ai_service_info,
            "agent_info": self.strands_service.get_agent_info() if self.strands_service else None,
            "capabilities": [
                "http_streaming_responses",
                "conversation_context",
                "intent_analysis",
                "entity_extraction",
                "dynamic_ai_responses",
                "personality_consistency",
                "conversation_memory",
                "tool_integration" if self.use_strands else "ai_powered_responses"
            ]
        }