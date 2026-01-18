"""AI Response Generation Service using OpenAI API."""

import logging
import json
from typing import Dict, List, Optional, Any, AsyncGenerator
from datetime import datetime
import openai
import asyncio

from src.config import settings

logger = logging.getLogger(__name__)


class AIResponseService:
    """Service for generating dynamic AI responses using OpenAI API."""

    def __init__(self):
        """Initialize AI response service with OpenAI."""
        self.openai_client = None
        
        # Initialize OpenAI client if API key is available
        if settings.openai_api_key:
            try:
                self.openai_client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
                logger.info("OpenAI client initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {e}")
        
        # Determine if we have AI available
        self.has_ai = self.openai_client is not None
        logger.info(f"AI Response Service initialized with OpenAI: {self.has_ai}")

    def _determine_preferred_provider(self) -> str:
        """Determine which AI provider to use based on availability."""
        if self.openai_client:
            return "openai"
        else:
            return "fallback"

    async def generate_response(
        self,
        user_message: str,
        intent: Dict[str, Any],
        context: Dict[str, Any],
        conversation_history: Optional[List[Dict]] = None,
        recommendations: Optional[List[Dict]] = None,
        user_profile: Optional[Dict] = None
    ) -> str:
        """Generate a conversational response using AI."""
        try:
            # Build system prompt for Noah's personality
            system_prompt = self._build_noah_system_prompt()
            
            # Build context-aware user prompt
            user_prompt = self._build_contextual_prompt(
                user_message=user_message,
                intent=intent,
                context=context,
                conversation_history=conversation_history,
                recommendations=recommendations,
                user_profile=user_profile
            )
            
            # Generate response using preferred provider
            if self.has_ai and self.openai_client:
                return await self._generate_openai_response(system_prompt, user_prompt)
            else:
                return self._generate_fallback_response(user_message, intent)
                
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            return self._generate_fallback_response(user_message, intent)

    async def generate_streaming_response(
        self,
        user_message: str,
        intent: Dict[str, Any],
        context: Dict[str, Any],
        conversation_history: Optional[List[Dict]] = None,
        recommendations: Optional[List[Dict]] = None,
        user_profile: Optional[Dict] = None
    ) -> AsyncGenerator[str, None]:
        """Generate a streaming conversational response using AI."""
        try:
            # Build system prompt for Noah's personality
            system_prompt = self._build_noah_system_prompt()
            
            # Build context-aware user prompt
            user_prompt = self._build_contextual_prompt(
                user_message=user_message,
                intent=intent,
                context=context,
                conversation_history=conversation_history,
                recommendations=recommendations,
                user_profile=user_profile
            )
            
            # Generate streaming response using preferred provider
            if self.has_ai and self.openai_client:
                async for chunk in self._generate_openai_streaming_response(system_prompt, user_prompt):
                    yield chunk
            else:
                # Fallback to non-streaming response
                response = self._generate_fallback_response(user_message, intent)
                # Simulate streaming by yielding words
                words = response.split()
                for i, word in enumerate(words):
                    yield word + (" " if i < len(words) - 1 else "")
                    await asyncio.sleep(0.05)  # Small delay for natural typing effect
                
        except Exception as e:
            logger.error(f"Error generating streaming AI response: {e}")
            fallback_response = self._generate_fallback_response(user_message, intent)
            yield fallback_response

    def _build_noah_system_prompt(self) -> str:
        """Build Noah's personality and behavior system prompt."""
        return """You are Noah, an intelligent and enthusiastic reading companion. Your personality traits:

PERSONALITY:
- Warm, friendly, and genuinely excited about books and reading
- Knowledgeable but never condescending or overwhelming
- Supportive of all reading levels and preferences
- Curious about user preferences and reading goals
- Encouraging and positive about the reading journey

CONVERSATION STYLE:
- Use natural, conversational language
- Ask thoughtful follow-up questions to understand preferences better
- Explain recommendations with genuine enthusiasm
- Remember and reference previous conversations when relevant
- Be concise but engaging - avoid overly long responses

CORE RESPONSIBILITIES:
1. Provide personalized book recommendations based on user preferences
2. Help users discover new genres and authors through "discovery mode"
3. Process feedback to improve future recommendations
4. Maintain engaging conversations about books, reading, and literature
5. Support users in their reading journey regardless of their level

RESPONSE GUIDELINES:
- Always respond in character as Noah
- When making recommendations, explain why you think the user might enjoy each book
- Be encouraging about reading goals and progress
- If you don't have specific book information, focus on helping the user describe what they're looking for
- Keep responses conversational and avoid being too formal or robotic

Remember: You're not just providing information - you're being a supportive reading companion who genuinely cares about helping users find their next great read."""

    def _build_contextual_prompt(
        self,
        user_message: str,
        intent: Dict[str, Any],
        context: Dict[str, Any],
        conversation_history: Optional[List[Dict]] = None,
        recommendations: Optional[List[Dict]] = None,
        user_profile: Optional[Dict] = None
    ) -> str:
        """Build a contextual prompt with all relevant information."""
        prompt_parts = []
        
        # Add conversation context
        if context:
            prompt_parts.append("CURRENT CONTEXT:")
            if context.get("current_topic"):
                prompt_parts.append(f"- Current topic: {context['current_topic']}")
            if context.get("user_mood"):
                prompt_parts.append(f"- User mood: {context['user_mood']}")
            if context.get("discovery_mode_active"):
                prompt_parts.append("- Discovery mode is active (user wants to explore new genres)")
            if context.get("preferred_language"):
                prompt_parts.append(f"- Preferred language: {context['preferred_language']}")
            prompt_parts.append("")
        
        # Add user profile information
        if user_profile:
            prompt_parts.append("USER PROFILE:")
            if user_profile.get("preferences"):
                prefs = user_profile["preferences"]
                if prefs.get("topics"):
                    topics = [t.get("topic", str(t)) for t in prefs["topics"][:5]]  # Top 5 topics
                    prompt_parts.append(f"- Favorite topics: {', '.join(topics)}")
                if prefs.get("content_types"):
                    types = [t.get("type", str(t)) for t in prefs["content_types"][:3]]
                    prompt_parts.append(f"- Preferred content types: {', '.join(types)}")
            
            if user_profile.get("reading_levels"):
                levels = user_profile["reading_levels"]
                if levels.get("english"):
                    prompt_parts.append(f"- English reading level: {levels['english'].get('level', 'Unknown')}")
                if levels.get("japanese"):
                    prompt_parts.append(f"- Japanese reading level: {levels['japanese'].get('level', 'Unknown')}")
            prompt_parts.append("")
        
        # Add recent conversation history
        if conversation_history and len(conversation_history) > 0:
            prompt_parts.append("RECENT CONVERSATION:")
            for msg in conversation_history[-5:]:  # Last 5 messages
                sender = msg.get("sender", "unknown")
                content = msg.get("content", "")[:200]  # Truncate long messages
                prompt_parts.append(f"- {sender.title()}: {content}")
            prompt_parts.append("")
        
        # Add intent information
        intent_type = intent.get("intent", "general_conversation")
        confidence = intent.get("confidence", 0.0)
        prompt_parts.append(f"DETECTED INTENT: {intent_type} (confidence: {confidence:.2f})")
        
        if intent.get("entities"):
            entities = intent["entities"]
            if entities:
                prompt_parts.append("EXTRACTED ENTITIES:")
                for entity_type, values in entities.items():
                    if values:
                        prompt_parts.append(f"- {entity_type}: {', '.join(values)}")
        prompt_parts.append("")
        
        # Add recommendations if available
        if recommendations:
            prompt_parts.append("AVAILABLE RECOMMENDATIONS:")
            for i, rec in enumerate(recommendations[:3], 1):  # Show up to 3 recommendations
                title = rec.get("title", "Unknown Title")
                author = rec.get("author", "Unknown Author")
                description = rec.get("description", "")[:100]  # Truncate description
                prompt_parts.append(f"{i}. {title} by {author}")
                if description:
                    prompt_parts.append(f"   {description}...")
            prompt_parts.append("")
        
        # Add the user's current message
        prompt_parts.append(f"USER MESSAGE: {user_message}")
        prompt_parts.append("")
        prompt_parts.append("Please respond as Noah, keeping in mind all the context above. Be conversational, helpful, and enthusiastic about helping with reading recommendations.")
        
        return "\n".join(prompt_parts)

    async def _generate_openai_response(self, system_prompt: str, user_prompt: str) -> str:
        """Generate response using OpenAI API."""
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=500,
                temperature=0.7,
                presence_penalty=0.1,
                frequency_penalty=0.1
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating OpenAI response: {e}")
            raise

    async def _generate_openai_streaming_response(self, system_prompt: str, user_prompt: str) -> AsyncGenerator[str, None]:
        """Generate streaming response using OpenAI API."""
        try:
            stream = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=500,
                temperature=0.7,
                presence_penalty=0.1,
                frequency_penalty=0.1,
                stream=True
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"Error generating OpenAI streaming response: {e}")
            raise

    def _generate_fallback_response(self, user_message: str, intent: Dict[str, Any]) -> str:
        """Generate fallback response when AI services are unavailable."""
        intent_type = intent.get("intent", "general_conversation")
        
        fallback_responses = {
            "book_recommendation": "I'd love to help you find your next great read! What genres or topics are you interested in? Are you looking for something light and fun, or perhaps something more thought-provoking?",
            
            "discovery_mode": "How exciting - let's explore something completely new! I'll help you discover books outside your usual preferences. This is one of my favorite things to do - finding hidden gems that surprise readers!",
            
            "feedback": "Thank you so much for sharing your thoughts! Your feedback helps me understand your preferences better. Tell me more about what you liked or didn't like - it really helps me make better recommendations for you.",
            
            "purchase_inquiry": "I understand you're interested in getting that book! While I can't generate purchase links directly, I'd be happy to help you find more information about it or suggest similar books you might enjoy.",
            
            "general_conversation": "Hi there! I'm Noah, your reading companion, and I'm absolutely thrilled to help you discover amazing books! Whether you're looking for your next favorite novel, want to explore a new genre, or just want to chat about books, I'm here for you. What's on your reading mind today?"
        }
        
        return fallback_responses.get(intent_type, fallback_responses["general_conversation"])

    async def generate_contextual_response_templates(
        self,
        intent_type: str,
        context: Dict[str, Any],
        user_profile: Optional[Dict] = None
    ) -> Dict[str, str]:
        """Generate dynamic response templates based on context and user profile."""
        try:
            # Build a prompt for generating response templates
            template_prompt = f"""Generate 3 different response templates for a reading assistant named Noah responding to a user with intent: {intent_type}

Context: {json.dumps(context, indent=2)}
User Profile: {json.dumps(user_profile or {}, indent=2)}

Each template should:
1. Be conversational and friendly
2. Reflect Noah's enthusiastic personality about books
3. Be appropriate for the given context and user profile
4. Include placeholders like {{book_title}}, {{author}}, {{genre}} where relevant

Return as JSON with keys: template1, template2, template3"""

            if self.preferred_provider == "openai" and self.openai_client:
                response = await self.openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant that generates conversational templates for a reading companion AI."},
                        {"role": "user", "content": template_prompt}
                    ],
                    max_tokens=400,
                    temperature=0.8
                )
                
                # Try to parse JSON response
                try:
                    return json.loads(response.choices[0].message.content)
                except json.JSONDecodeError:
                    # Fallback if JSON parsing fails
                    pass
            
            # Fallback templates
            return self._get_fallback_templates(intent_type)
            
        except Exception as e:
            logger.error(f"Error generating contextual templates: {e}")
            return self._get_fallback_templates(intent_type)

    def _get_fallback_templates(self, intent_type: str) -> Dict[str, str]:
        """Get fallback response templates."""
        templates = {
            "book_recommendation": {
                "template1": "I'm excited to help you find your next great read! Based on what you've told me, I think you might really enjoy {book_title} by {author}. {reason}",
                "template2": "Oh, I have the perfect suggestion for you! {book_title} by {author} sounds like exactly what you're looking for. {reason}",
                "template3": "Let me recommend {book_title} by {author} - I think this could be your next favorite book! {reason}"
            },
            "discovery_mode": {
                "template1": "Time for an adventure! Let's try something completely different - {book_title} by {author}. It's outside your usual preferences, but {reason}",
                "template2": "I love discovery mode! Here's something that might surprise you: {book_title} by {author}. {reason}",
                "template3": "Ready to explore? {book_title} by {author} is quite different from what you usually read, but {reason}"
            },
            "general_conversation": {
                "template1": "I'm so glad you're here! As your reading companion, I'm excited to help you discover amazing books. What kind of reading adventure are we going on today?",
                "template2": "Hello! I'm Noah, and I absolutely love helping people find their perfect next read. Tell me, what's caught your reading interest lately?",
                "template3": "Welcome! There's nothing I enjoy more than connecting readers with books they'll love. What can I help you discover today?"
            }
        }
        
        return templates.get(intent_type, templates["general_conversation"])

    def get_service_info(self) -> Dict[str, Any]:
        """Get information about the AI response service configuration."""
        return {
            "service_name": "AI Response Service",
            "provider": "openai" if self.has_ai else "fallback",
            "openai_available": self.openai_client is not None,
            "capabilities": [
                "dynamic_response_generation",
                "streaming_responses",
                "contextual_awareness",
                "personality_consistency",
                "conversation_memory",
                "template_generation"
            ],
            "model": "gpt-4o-mini" if self.has_ai else "fallback"
        }