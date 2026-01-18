"""Strands Agents framework integration service."""

import logging
from typing import Dict, List, Optional, Any, AsyncGenerator
from datetime import datetime

from strands_agents import Agent, AgentConfig
from strands_agents.tools import Tool
from strands_agents_tools.content import ContentAnalyzer
from strands_agents_tools.conversation import ConversationManager

from src.config import settings
from src.services.recommendation_engine import RecommendationEngine
from src.services.content_service import ContentService
from src.services.user_profile_service import UserProfileService

logger = logging.getLogger(__name__)


class StrandsAgentService:
    """Service for managing Strands agents for conversation and recommendation."""

    def __init__(self):
        """Initialize Strands agent service."""
        self.recommendation_engine = RecommendationEngine()
        self.content_service = ContentService()
        self.user_profile_service = UserProfileService()
        
        # Initialize the main Noah agent
        self.noah_agent = self._create_noah_agent()
        
        logger.info("Strands Agent Service initialized")

    def _create_noah_agent(self) -> Agent:
        """Create the main Noah reading agent with Strands framework."""
        
        # Configure agent with reading-specific capabilities
        config = AgentConfig(
            name="noah_reading_agent",
            description="Noah is an intelligent reading companion that provides personalized book recommendations, reading assistance, and discovery features.",
            model="gpt-4o-mini",  # Use efficient model for conversation
            temperature=0.7,
            max_tokens=1000,
            system_prompt=self._get_noah_system_prompt(),
            tools=[
                self._create_recommendation_tool(),
                self._create_discovery_tool(),
                self._create_purchase_link_tool(),
                self._create_feedback_tool(),
                self._create_content_analysis_tool()
            ]
        )
        
        return Agent(config)

    def _get_noah_system_prompt(self) -> str:
        """Get the system prompt for Noah agent."""
        return """You are Noah, an intelligent and friendly reading companion. Your role is to:

1. Help users discover books they'll love through personalized recommendations
2. Understand their reading preferences and adapt over time
3. Provide "discovery mode" suggestions that expand their reading horizons
4. Generate purchase links when users want to buy books
5. Process feedback to improve future recommendations
6. Maintain engaging, natural conversations about books and reading

Key personality traits:
- Enthusiastic about books and reading
- Knowledgeable but not overwhelming
- Supportive of all reading levels and preferences
- Curious about user preferences and reading goals
- Helpful in finding the right book for any situation

Always respond in a conversational, friendly tone. When making recommendations, explain why you think the user might enjoy each book. Be encouraging and supportive of their reading journey.

Available tools:
- get_recommendations: Get personalized book recommendations
- discovery_mode: Find books outside usual preferences
- generate_purchase_links: Create purchase links for books
- process_feedback: Handle user feedback on recommendations
- analyze_content: Analyze book content for recommendations
"""

    def _create_recommendation_tool(self) -> Tool:
        """Create tool for getting book recommendations."""
        async def get_recommendations(
            user_id: str,
            preferences: Optional[Dict] = None,
            context: Optional[Dict] = None,
            limit: int = 3
        ) -> List[Dict]:
            """Get personalized book recommendations for a user."""
            try:
                # Get user profile
                user_profile = await self.user_profile_service.get_user_profile(user_id)
                
                # Generate recommendations using the recommendation engine
                recommendations = await self.recommendation_engine.generate_recommendations(
                    user_profile=user_profile,
                    context=context or {},
                    preferences_override=preferences,
                    limit=limit
                )
                
                return recommendations
            except Exception as e:
                logger.error(f"Error getting recommendations: {e}")
                return []

        return Tool(
            name="get_recommendations",
            description="Get personalized book recommendations for a user based on their profile and preferences",
            function=get_recommendations,
            parameters={
                "user_id": {"type": "string", "description": "User identifier"},
                "preferences": {"type": "object", "description": "Optional preference overrides"},
                "context": {"type": "object", "description": "Optional context (mood, time available, etc.)"},
                "limit": {"type": "integer", "description": "Number of recommendations to return", "default": 3}
            }
        )

    def _create_discovery_tool(self) -> Tool:
        """Create tool for discovery mode recommendations."""
        async def discovery_mode(
            user_id: str,
            divergence_level: float = 0.7,
            limit: int = 2
        ) -> List[Dict]:
            """Get discovery mode recommendations that diverge from user's typical preferences."""
            try:
                # Get user profile
                user_profile = await self.user_profile_service.get_user_profile(user_id)
                
                # Generate discovery recommendations
                recommendations = await self.recommendation_engine.generate_discovery_recommendations(
                    user_profile=user_profile,
                    divergence_level=divergence_level,
                    limit=limit
                )
                
                return recommendations
            except Exception as e:
                logger.error(f"Error getting discovery recommendations: {e}")
                return []

        return Tool(
            name="discovery_mode",
            description="Get discovery mode recommendations that suggest books outside the user's typical preferences",
            function=discovery_mode,
            parameters={
                "user_id": {"type": "string", "description": "User identifier"},
                "divergence_level": {"type": "number", "description": "How much to diverge from preferences (0.0-1.0)", "default": 0.7},
                "limit": {"type": "integer", "description": "Number of discovery recommendations", "default": 2}
            }
        )

    def _create_purchase_link_tool(self) -> Tool:
        """Create tool for generating purchase links."""
        async def generate_purchase_links(
            book_title: str,
            author: Optional[str] = None,
            isbn: Optional[str] = None
        ) -> List[Dict]:
            """Generate purchase links for a book."""
            try:
                from src.services.purchase_link_generator import PurchaseLinkGenerator
                
                purchase_generator = PurchaseLinkGenerator()
                links = await purchase_generator.generate_links(
                    title=book_title,
                    author=author,
                    isbn=isbn
                )
                
                return links
            except Exception as e:
                logger.error(f"Error generating purchase links: {e}")
                return []

        return Tool(
            name="generate_purchase_links",
            description="Generate purchase links for a specific book",
            function=generate_purchase_links,
            parameters={
                "book_title": {"type": "string", "description": "Title of the book"},
                "author": {"type": "string", "description": "Author of the book (optional)"},
                "isbn": {"type": "string", "description": "ISBN of the book (optional)"}
            }
        )

    def _create_feedback_tool(self) -> Tool:
        """Create tool for processing user feedback."""
        async def process_feedback(
            user_id: str,
            book_id: str,
            feedback_type: str,
            rating: Optional[float] = None,
            comments: Optional[str] = None
        ) -> Dict:
            """Process user feedback on a book recommendation."""
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

        return Tool(
            name="process_feedback",
            description="Process user feedback on book recommendations to improve future suggestions",
            function=process_feedback,
            parameters={
                "user_id": {"type": "string", "description": "User identifier"},
                "book_id": {"type": "string", "description": "Book identifier"},
                "feedback_type": {"type": "string", "description": "Type of feedback (interested, not_interested, purchased, etc.)"},
                "rating": {"type": "number", "description": "Optional rating (1-5 scale)"},
                "comments": {"type": "string", "description": "Optional user comments"}
            }
        )

    def _create_content_analysis_tool(self) -> Tool:
        """Create tool for analyzing book content."""
        async def analyze_content(
            content_text: str,
            language: str = "english"
        ) -> Dict:
            """Analyze book content for complexity, topics, and reading level."""
            try:
                analysis = await self.content_service.analyze_content(
                    content=content_text,
                    language=language
                )
                
                return analysis
            except Exception as e:
                logger.error(f"Error analyzing content: {e}")
                return {}

        return Tool(
            name="analyze_content",
            description="Analyze book content for reading level, topics, and complexity",
            function=analyze_content,
            parameters={
                "content_text": {"type": "string", "description": "Text content to analyze"},
                "language": {"type": "string", "description": "Language of the content", "default": "english"}
            }
        )

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
            context = {
                "user_id": user_id,
                "conversation_context": conversation_context or {},
                "metadata": metadata or {},
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Process message with Noah agent
            response = await self.noah_agent.process_message(
                message=user_message,
                context=context
            )
            
            return {
                "content": response.content,
                "tool_calls": response.tool_calls,
                "context": response.context,
                "metadata": {
                    "model_used": response.model,
                    "tokens_used": response.usage.get("total_tokens", 0) if response.usage else 0,
                    "processing_time": response.processing_time
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
            context = {
                "user_id": user_id,
                "conversation_context": conversation_context or {},
                "metadata": metadata or {},
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Stream response from Noah agent
            async for chunk in self.noah_agent.stream_message(
                message=user_message,
                context=context
            ):
                yield {
                    "type": "content_chunk",
                    "content": chunk.content,
                    "is_final": chunk.is_final,
                    "tool_calls": chunk.tool_calls if hasattr(chunk, 'tool_calls') else [],
                    "timestamp": datetime.utcnow().isoformat()
                }
                
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
            context_update = {
                "user_id": user_id,
                "conversation_history": conversation_history[-10:],  # Keep last 10 messages
                "user_preferences": user_preferences or {},
                "last_updated": datetime.utcnow().isoformat()
            }
            
            await self.noah_agent.update_context(context_update)
            
        except Exception as e:
            logger.error(f"Error updating agent context: {e}")

    def get_agent_info(self) -> Dict[str, Any]:
        """Get information about the configured Strands agent."""
        return {
            "agent_name": self.noah_agent.config.name,
            "description": self.noah_agent.config.description,
            "model": self.noah_agent.config.model,
            "tools": [tool.name for tool in self.noah_agent.config.tools],
            "capabilities": [
                "personalized_recommendations",
                "discovery_mode",
                "purchase_link_generation",
                "feedback_processing",
                "content_analysis",
                "natural_conversation"
            ]
        }