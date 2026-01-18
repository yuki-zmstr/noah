"""Strands Agents framework integration service."""

import logging
import asyncio
from contextlib import asynccontextmanager
from typing import Dict, List, Optional, Any, AsyncGenerator
from datetime import datetime

from strands import Agent
from strands.tools import tool

from src.config import settings
from src.services.recommendation_engine import ContextualRecommendationEngine
from src.services.discovery_engine import DiscoveryModeEngine
from src.services.content_service import ContentService
from src.services.user_profile_service import UserProfileEngine

logger = logging.getLogger(__name__)


class StrandsAgentService:
    """Service for managing Strands agents for conversation and recommendation."""

    def __init__(self):
        """Initialize Strands agent service."""
        self.recommendation_engine = ContextualRecommendationEngine()
        self.discovery_engine = DiscoveryModeEngine()
        self.content_service = ContentService()
        self.user_profile_service = UserProfileEngine()
        
        # Create tool functions
        self._create_tools()
        
        # Initialize the main Noah agent
        self.noah_agent = self._create_noah_agent()
        
        logger.info("Strands Agent Service initialized")

    def _create_tools(self):
        """Create tool functions for the agent."""
        
        @tool
        async def get_recommendations(
            user_id: str,
            preferences: Optional[Dict] = None,
            context: Optional[Dict] = None,
            limit: int = 3
        ) -> List[Dict]:
            """Get personalized book recommendations for a user based on their profile and preferences.
            
            Args:
                user_id: User identifier
                preferences: Optional preference overrides
                context: Optional context (mood, time available, etc.)
                limit: Number of recommendations to return (default: 3)
                
            Returns:
                List of book recommendations with titles, authors, and descriptions
            """
            try:
                from src.services.database import db_service
                
                # Use database session context manager
                with db_service.get_session() as db:
                    # Get user profile
                    user_profile = await self.user_profile_service.get_or_create_profile(user_id, db)
                    
                    # Generate recommendations using the recommendation engine
                    recommendations = await self.recommendation_engine.generate_contextual_recommendations(
                        user_id=user_id,
                        context=context or {},
                        limit=limit,
                        db=db
                    )
                    
                    return recommendations
            except Exception as e:
                logger.error(f"Error getting recommendations: {e}")
                return []

        @tool
        async def discovery_mode(
            user_id: str,
            divergence_level: float = 0.7,
            limit: int = 2
        ) -> List[Dict]:
            """Get discovery mode recommendations that suggest books outside the user's typical preferences.
            
            Args:
                user_id: User identifier
                divergence_level: How much to diverge from preferences (0.0-1.0, default: 0.7)
                limit: Number of discovery recommendations (default: 2)
                
            Returns:
                List of discovery book recommendations that expand user's reading horizons
            """
            try:
                from src.services.database import db_service
                
                # Use database session context manager
                with db_service.get_session() as db:
                    # Get user profile
                    user_profile = await self.user_profile_service.get_or_create_profile(user_id, db)
                    
                    # Generate discovery recommendations
                    recommendations = await self.discovery_engine.generate_discovery_recommendations(
                        user_id=user_id,
                        limit=limit,
                        db=db
                    )
                    
                    return recommendations
            except Exception as e:
                logger.error(f"Error getting discovery recommendations: {e}")
                return []

        @tool
        async def process_feedback(
            user_id: str,
            book_id: str,
            feedback_type: str,
            rating: Optional[float] = None,
            comments: Optional[str] = None
        ) -> Dict:
            """Process user feedback on a book recommendation to improve future suggestions.
            
            Args:
                user_id: User identifier
                book_id: Book identifier
                feedback_type: Type of feedback (interested, not_interested, purchased, etc.)
                rating: Optional rating (1-5 scale)
                comments: Optional user comments
                
            Returns:
                Status of feedback processing
            """
            try:
                from src.services.feedback_service import FeedbackService
                
                feedback_service = FeedbackService()
                result = await feedback_service.process_feedback(
                    user_id=user_id,
                    book_id=book_id,
                    feedback_type=feedback_type,
                    rating=rating,
                    comments=comments
                )
                
                return result
            except Exception as e:
                logger.error(f"Error processing feedback: {e}")
                return {"status": "error", "message": str(e)}

        @tool
        async def analyze_content(
            content_text: str,
            language: str = "english"
        ) -> Dict:
            """Analyze book content for reading level, topics, and complexity.
            
            Args:
                content_text: Text content to analyze
                language: Language of the content (default: english)
                
            Returns:
                Analysis results including reading level, topics, and complexity metrics
            """
            try:
                analysis = await self.content_service.analyze_content(
                    content=content_text,
                    language=language
                )
                
                return analysis
            except Exception as e:
                logger.error(f"Error analyzing content: {e}")
                return {}

        # Store tools as instance variables for agent creation
        self.get_recommendations = get_recommendations
        self.discovery_mode = discovery_mode
        self.process_feedback = process_feedback
        self.analyze_content = analyze_content

    def _create_noah_agent(self) -> Agent:
        """Create the main Noah reading agent with Strands framework."""
        
        system_prompt = """You are Noah, an intelligent and friendly reading companion. Your role is to:

1. Help users discover books they'll love through personalized recommendations
2. Understand their reading preferences and adapt over time
3. Provide "discovery mode" suggestions that expand their reading horizons
4. Process feedback to improve future recommendations
5. Maintain engaging, natural conversations about books and reading

Key personality traits:
- Enthusiastic about books and reading
- Knowledgeable but not overwhelming
- Supportive of all reading levels and preferences
- Curious about user preferences and reading goals
- Helpful in finding the right book for any situation

Always respond in a conversational, friendly tone. When making recommendations, explain why you think the user might enjoy each book. Be encouraging and supportive of their reading journey.

You have access to several tools to help users:
- get_recommendations: Get personalized book recommendations
- discovery_mode: Find books outside usual preferences
- process_feedback: Handle user feedback on recommendations
- analyze_content: Analyze book content for recommendations

Use these tools when appropriate to provide the best possible reading assistance."""

        # Create agent with tools
        agent = Agent(
            model=settings.strands_agent_model,
            system_prompt=system_prompt,
            tools=[
                self.get_recommendations,
                self.discovery_mode,
                self.process_feedback,
                self.analyze_content
            ],
            name="noah_reading_agent",
            description="Noah is an intelligent reading companion that provides personalized book recommendations and reading assistance."
        )
        
        return agent

    async def process_conversation(
        self,
        user_message: str,
        user_id: str,
        conversation_context: Optional[Dict] = None,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Process a conversation message using Strands agent."""
        try:
            # Prepare context for the agent
            context_message = f"User ID: {user_id}\n"
            if conversation_context:
                context_message += f"Context: {conversation_context}\n"
            if metadata:
                context_message += f"Metadata: {metadata}\n"
            context_message += f"User message: {user_message}"
            
            # Process message with Noah agent
            response = await self.noah_agent.run_async(context_message)
            
            return {
                "content": response.content,
                "tool_calls": getattr(response, 'tool_calls', []),
                "context": conversation_context or {},
                "metadata": {
                    "model_used": settings.strands_agent_model,
                    "processing_time": 0  # Strands doesn't expose this directly
                }
            }
            
        except Exception as e:
            logger.error(f"Error processing conversation with Strands agent: {e}")
            return {
                "content": "I'm sorry, I encountered an issue processing your message. Please try again, and I'll do my best to help you with your reading needs!",
                "tool_calls": [],
                "context": conversation_context or {},
                "error": str(e)
            }

    def _convert_event(self, event) -> dict | None:
        """Convert Strands events to frontend-compatible JSON format."""
        try:
            # Log raw event for debugging
            logger.debug(f"Processing event: {type(event)} - {event}")
            
            # Handle different event formats
            if isinstance(event, dict):
                # Direct dictionary event
                inner_event = event.get('event')
                if inner_event:
                    return self._process_inner_event(inner_event)
                
                # Check if this is already a processed event
                if event.get('type') == 'text' and 'data' in event:
                    return event
                    
            elif hasattr(event, 'get'):
                # Object with get method
                inner_event = event.get('event')
                if inner_event:
                    return self._process_inner_event(inner_event)
            
            # Handle raw string content (fallback)
            elif isinstance(event, str) and event.strip():
                return {'type': 'text', 'data': event}
            
            return None
        except Exception as e:
            logger.error(f"Error converting event: {e}, event: {event}")
            return None
    
    def _process_inner_event(self, inner_event) -> dict | None:
        """Process the inner event structure."""
        try:
            # Detect text deltas
            content_block_delta = inner_event.get('contentBlockDelta')
            if content_block_delta:
                delta = content_block_delta.get('delta', {})
                text = delta.get('text')
                if text:
                    return {'type': 'text', 'data': text}
            
            # Detect tool use start
            content_block_start = inner_event.get('contentBlockStart')
            if content_block_start:
                start = content_block_start.get('start', {})
                tool_use = start.get('toolUse')
                if tool_use:
                    tool_name = tool_use.get('name', 'unknown')
                    return {'type': 'tool_use', 'tool_name': tool_name}
            
            # Detect message completion
            message_stop = inner_event.get('messageStop')
            if message_stop:
                return {'type': 'complete'}
            
            return None
        except Exception:
            return None

    @asynccontextmanager
    async def _safe_stream_context(self, stream_generator):
        """Context manager to safely handle stream generators and cleanup."""
        try:
            yield stream_generator
        except GeneratorExit:
            logger.debug("Stream generator exited gracefully")
        except Exception as e:
            logger.error(f"Error in stream context: {e}")
            raise
        finally:
            # Attempt to close the generator safely
            try:
                if hasattr(stream_generator, 'aclose'):
                    await stream_generator.aclose()
                elif hasattr(stream_generator, 'close'):
                    stream_generator.close()
            except Exception as cleanup_error:
                # Suppress cleanup errors to avoid masking the original error
                logger.debug(f"Error during stream cleanup: {cleanup_error}")
                pass

    async def stream_conversation(
        self,
        user_message: str,
        user_id: str,
        conversation_context: Optional[Dict] = None,
        metadata: Optional[Dict] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream a conversation response using Strands agent."""
        try:
            # Prepare context for the agent
            context_message = f"User ID: {user_id}\n"
            if conversation_context:
                context_message += f"Context: {conversation_context}\n"
            if metadata:
                context_message += f"Metadata: {metadata}\n"
            context_message += f"User message: {user_message}"
            
            # Track content to prevent duplicates
            accumulated_content = ""
            last_chunk_time = 0
            duplicate_threshold = 0.1  # 100ms threshold for duplicate detection
            
            # Create and use the stream generator with safe context management
            stream_generator = self.noah_agent.stream_async(context_message)
            
            async with self._safe_stream_context(stream_generator) as safe_stream:
                try:
                    async for chunk in safe_stream:
                        try:
                            # Convert the raw Strands event to a clean format
                            converted_event = self._convert_event(chunk)
                            
                            if converted_event:
                                if converted_event['type'] == 'text':
                                    content = converted_event['data']
                                    current_time = datetime.utcnow().timestamp()
                                    
                                    # Skip empty content
                                    if not content or not content.strip():
                                        continue
                                    
                                    # Check if this content is already part of what we've sent
                                    if content in accumulated_content:
                                        logger.debug(f"Skipping duplicate content: {content}")
                                        continue
                                    
                                    # Check for rapid duplicates (same content within threshold)
                                    if (current_time - last_chunk_time) < duplicate_threshold:
                                        if content == getattr(self, '_last_content', ''):
                                            logger.debug(f"Skipping rapid duplicate: {content}")
                                            continue
                                    
                                    # Update tracking
                                    accumulated_content += content
                                    self._last_content = content
                                    last_chunk_time = current_time
                                    
                                    yield {
                                        "type": "content_chunk",
                                        "content": content,
                                        "is_final": False,
                                        "tool_calls": [],
                                        "timestamp": datetime.utcnow().isoformat()
                                    }
                                    
                                elif converted_event['type'] == 'tool_use':
                                    # Log tool usage but don't yield it as content
                                    logger.info(f"Tool being used: {converted_event['tool_name']}")
                                    
                                elif converted_event['type'] == 'complete':
                                    yield {
                                        "type": "content_chunk",
                                        "content": "",
                                        "is_final": True,
                                        "tool_calls": [],
                                        "timestamp": datetime.utcnow().isoformat()
                                    }
                                    break
                                    
                        except (GeneratorExit, asyncio.CancelledError):
                            # Handle graceful shutdown
                            logger.debug("Stream processing cancelled or exited")
                            break
                        except Exception as chunk_error:
                            # Log chunk processing errors but continue
                            logger.warning(f"Error processing chunk: {chunk_error}")
                            continue
                            
                except (GeneratorExit, asyncio.CancelledError):
                    # Handle graceful shutdown
                    logger.debug("Stream iteration cancelled or exited")
                    
        except Exception as e:
            logger.error(f"Error streaming conversation with Strands agent: {e}")
            yield {
                "type": "error",
                "content": "I'm sorry, I encountered an issue processing your message. Please try again!",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    async def update_agent_context(
        self,
        user_id: str,
        conversation_history: List[Dict],
        user_preferences: Optional[Dict] = None
    ) -> None:
        """Update agent context with conversation history and user preferences."""
        try:
            # Strands agents maintain context automatically through conversation
            # We can add messages to provide context if needed
            context_info = {
                "user_id": user_id,
                "conversation_history": conversation_history[-10:],  # Keep last 10 messages
                "user_preferences": user_preferences or {},
                "last_updated": datetime.utcnow().isoformat()
            }
            
            # Add context as a system message if needed
            logger.info(f"Context updated for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error updating agent context: {e}")

    def get_agent_info(self) -> Dict[str, Any]:
        """Get information about the configured Strands agent."""
        return {
            "agent_name": "noah_reading_agent",
            "description": "Noah is an intelligent reading companion that provides personalized book recommendations and reading assistance.",
            "model": settings.strands_agent_model,
            "tools": [
                "get_recommendations",
                "discovery_mode", 
                "process_feedback",
                "analyze_content"
            ],
            "capabilities": [
                "personalized_recommendations",
                "discovery_mode",
                "feedback_processing",
                "content_analysis",
                "natural_conversation"
            ]
        }