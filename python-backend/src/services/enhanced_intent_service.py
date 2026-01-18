"""Enhanced Intent Recognition and Entity Extraction Service."""

import logging
import re
from typing import Dict, List, Optional, Any
from datetime import datetime
import openai

from src.config import settings

logger = logging.getLogger(__name__)


class EnhancedIntentService:
    """Enhanced intent recognition and entity extraction using AI."""

    def __init__(self):
        """Initialize enhanced intent service."""
        self.openai_client = None
        
        # Initialize OpenAI client if available
        if settings.openai_api_key:
            try:
                self.openai_client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
                logger.info("OpenAI client initialized for intent recognition")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {e}")
        
        self.has_ai = self.openai_client is not None

    async def analyze_intent(
        self,
        message: str,
        context: Optional[Dict] = None,
        conversation_history: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """Analyze user message intent with enhanced AI capabilities."""
        try:
            if self.has_ai:
                return await self._ai_intent_analysis(message, context, conversation_history)
            else:
                return self._enhanced_fallback_intent_analysis(message, context)
        except Exception as e:
            logger.error(f"Error in intent analysis: {e}")
            return self._enhanced_fallback_intent_analysis(message, context)

    async def extract_entities(
        self,
        message: str,
        intent_context: Optional[Dict] = None
    ) -> Dict[str, List[str]]:
        """Extract entities with enhanced AI capabilities."""
        try:
            if self.has_ai:
                return await self._ai_entity_extraction(message, intent_context)
            else:
                return self._enhanced_fallback_entity_extraction(message)
        except Exception as e:
            logger.error(f"Error in entity extraction: {e}")
            return self._enhanced_fallback_entity_extraction(message)

    async def _ai_intent_analysis(
        self,
        message: str,
        context: Optional[Dict] = None,
        conversation_history: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """AI-powered intent analysis."""
        prompt = self._build_intent_analysis_prompt(message, context, conversation_history)
        
        try:
            if self.openai_client:
                response = await self.openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are an expert at analyzing user intents for a reading assistant. Return JSON only."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=200,
                    temperature=0.1
                )
                
                import json
                result = json.loads(response.choices[0].message.content)
                return result
                
        except Exception as e:
            logger.error(f"AI intent analysis failed: {e}")
            
        # Fallback to enhanced rule-based analysis
        return self._enhanced_fallback_intent_analysis(message, context)

    async def _ai_entity_extraction(
        self,
        message: str,
        intent_context: Optional[Dict] = None
    ) -> Dict[str, List[str]]:
        """AI-powered entity extraction."""
        prompt = f"""Extract entities from this message about books/reading:
Message: "{message}"
Intent context: {intent_context or {}}

Extract these entity types:
- book_titles: Book titles mentioned
- authors: Author names mentioned  
- genres: Genres or categories mentioned
- languages: Languages mentioned (english, japanese)
- reading_preferences: Reading preferences or moods
- feedback_indicators: Words indicating likes/dislikes

Return as JSON with arrays for each entity type."""

        try:
            if self.openai_client:
                response = await self.openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are an expert at extracting entities from text. Return JSON only."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=300,
                    temperature=0.1
                )
                
                import json
                result = json.loads(response.choices[0].message.content)
                return result
                
        except Exception as e:
            logger.error(f"AI entity extraction failed: {e}")
            
        # Fallback to enhanced rule-based extraction
        return self._enhanced_fallback_entity_extraction(message)

    def _build_intent_analysis_prompt(
        self,
        message: str,
        context: Optional[Dict] = None,
        conversation_history: Optional[List[Dict]] = None
    ) -> str:
        """Build prompt for AI intent analysis."""
        prompt_parts = [
            "Analyze the user's intent in this message to a reading assistant named Noah.",
            f"Message: \"{message}\"",
            ""
        ]
        
        if context:
            prompt_parts.extend([
                "Context:",
                f"- Current topic: {context.get('current_topic', 'None')}",
                f"- Discovery mode active: {context.get('discovery_mode_active', False)}",
                f"- User mood: {context.get('user_mood', 'Unknown')}",
                ""
            ])
        
        if conversation_history:
            prompt_parts.append("Recent conversation:")
            for msg in conversation_history[-3:]:
                sender = msg.get('sender', 'unknown')
                content = msg.get('content', '')[:100]
                prompt_parts.append(f"- {sender}: {content}")
            prompt_parts.append("")
        
        prompt_parts.extend([
            "Possible intents:",
            "- book_recommendation: User wants book suggestions",
            "- discovery_mode: User wants to explore new genres/authors",
            "- feedback: User is giving feedback on recommendations",
            "- purchase_inquiry: User wants to buy/find a book",
            "- reading_progress: User discussing their reading progress",
            "- general_conversation: General chat about books/reading",
            "",
            "Return JSON format:",
            '{"intent": "intent_name", "confidence": 0.0-1.0, "reasoning": "brief explanation", "context_clues": ["clue1", "clue2"]}'
        ])
        
        return "\n".join(prompt_parts)

    def _enhanced_fallback_intent_analysis(self, message: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Enhanced fallback intent analysis with better pattern matching."""
        message_lower = message.lower()
        
        # Check context for hints
        if context:
            if context.get("discovery_mode_active"):
                discovery_keywords = ["more", "another", "different", "surprise", "new"]
                if any(word in message_lower for word in discovery_keywords):
                    return {
                        "intent": "discovery_mode",
                        "confidence": 0.8,
                        "reasoning": "Discovery mode active and user wants more suggestions",
                        "context_clues": ["discovery_mode_active"]
                    }
        
        # Enhanced pattern matching with confidence scoring
        patterns = {
            "book_recommendation": {
                "keywords": ["recommend", "suggest", "book", "read", "looking for", "want to read", "good book"],
                "phrases": ["what should i read", "any recommendations", "suggest a book", "recommend something"],
                "confidence": 0.85
            },
            "discovery_mode": {
                "keywords": ["surprise", "lucky", "discover", "new", "different", "explore", "random"],
                "phrases": ["feeling lucky", "something new", "outside my comfort zone", "surprise me"],
                "confidence": 0.8
            },
            "feedback": {
                "keywords": ["loved", "hated", "liked", "disliked", "enjoyed", "boring", "amazing", "terrible"],
                "phrases": ["not for me", "really enjoyed", "didn't like", "was great", "wasn't good"],
                "confidence": 0.75
            },
            "purchase_inquiry": {
                "keywords": ["buy", "purchase", "get", "order", "where", "find", "available"],
                "phrases": ["where can i", "how to buy", "want to get", "is it available"],
                "confidence": 0.8
            },
            "reading_progress": {
                "keywords": ["reading", "finished", "started", "progress", "chapter", "page"],
                "phrases": ["currently reading", "just finished", "halfway through", "started reading"],
                "confidence": 0.7
            }
        }
        
        best_match = {"intent": "general_conversation", "confidence": 0.5, "reasoning": "No specific intent detected"}
        
        for intent, pattern_data in patterns.items():
            score = 0
            matched_clues = []
            
            # Check keywords
            for keyword in pattern_data["keywords"]:
                if keyword in message_lower:
                    score += 1
                    matched_clues.append(f"keyword: {keyword}")
            
            # Check phrases
            for phrase in pattern_data["phrases"]:
                if phrase in message_lower:
                    score += 2  # Phrases are weighted higher
                    matched_clues.append(f"phrase: {phrase}")
            
            if score > 0:
                confidence = min(pattern_data["confidence"] * (score / len(pattern_data["keywords"])), 0.95)
                if confidence > best_match["confidence"]:
                    best_match = {
                        "intent": intent,
                        "confidence": confidence,
                        "reasoning": f"Matched {score} patterns for {intent}",
                        "context_clues": matched_clues
                    }
        
        return best_match

    def _enhanced_fallback_entity_extraction(self, message: str) -> Dict[str, List[str]]:
        """Enhanced fallback entity extraction with better pattern matching."""
        entities = {
            "book_titles": [],
            "authors": [],
            "genres": [],
            "languages": [],
            "reading_preferences": [],
            "feedback_indicators": []
        }
        
        message_lower = message.lower()
        
        # Language detection
        language_patterns = {
            "japanese": ["japanese", "japan", "manga", "light novel", "kanji", "hiragana"],
            "english": ["english", "american", "british", "western"]
        }
        
        for lang, keywords in language_patterns.items():
            if any(keyword in message_lower for keyword in keywords):
                entities["languages"].append(lang)
        
        # Genre detection
        genre_patterns = [
            "fiction", "non-fiction", "mystery", "thriller", "romance", "fantasy", "sci-fi", 
            "science fiction", "biography", "memoir", "history", "philosophy", "poetry",
            "young adult", "ya", "children", "horror", "comedy", "drama", "adventure"
        ]
        
        for genre in genre_patterns:
            if genre in message_lower:
                entities["genres"].append(genre)
        
        # Reading preferences
        preference_patterns = [
            "light reading", "heavy", "complex", "simple", "short", "long", "quick read",
            "page turner", "thought provoking", "entertaining", "educational", "inspiring"
        ]
        
        for pref in preference_patterns:
            if pref in message_lower:
                entities["reading_preferences"].append(pref)
        
        # Feedback indicators
        positive_feedback = ["love", "like", "enjoy", "great", "amazing", "wonderful", "fantastic", "excellent"]
        negative_feedback = ["hate", "dislike", "boring", "terrible", "awful", "bad", "not good", "didn't like"]
        
        for word in positive_feedback:
            if word in message_lower:
                entities["feedback_indicators"].append(f"positive: {word}")
        
        for word in negative_feedback:
            if word in message_lower:
                entities["feedback_indicators"].append(f"negative: {word}")
        
        # Simple book title extraction (quoted text or capitalized phrases)
        # Look for quoted text
        quoted_matches = re.findall(r'"([^"]*)"', message)
        entities["book_titles"].extend(quoted_matches)
        
        # Look for "by [Author]" patterns
        author_matches = re.findall(r'by\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', message)
        entities["authors"].extend(author_matches)
        
        return entities

    def analyze_conversation_flow(
        self,
        current_intent: Dict[str, Any],
        conversation_history: List[Dict],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze conversation flow for context-aware responses."""
        flow_analysis = {
            "conversation_stage": "initial",
            "user_engagement": "neutral",
            "topic_progression": [],
            "recommendations_given": 0,
            "feedback_received": 0
        }
        
        if not conversation_history:
            return flow_analysis
        
        # Analyze recent messages
        recent_intents = []
        recommendations_count = 0
        feedback_count = 0
        
        for msg in conversation_history[-10:]:  # Last 10 messages
            if msg.get("intent"):
                intent_type = msg["intent"].get("intent", "unknown")
                recent_intents.append(intent_type)
                
                if intent_type == "book_recommendation":
                    recommendations_count += 1
                elif intent_type == "feedback":
                    feedback_count += 1
        
        # Determine conversation stage
        if len(conversation_history) < 3:
            flow_analysis["conversation_stage"] = "initial"
        elif recommendations_count > 2:
            flow_analysis["conversation_stage"] = "recommendation_focused"
        elif feedback_count > 1:
            flow_analysis["conversation_stage"] = "feedback_gathering"
        else:
            flow_analysis["conversation_stage"] = "exploration"
        
        # Analyze user engagement
        if feedback_count > recommendations_count * 0.5:
            flow_analysis["user_engagement"] = "high"
        elif len(recent_intents) > 5:
            flow_analysis["user_engagement"] = "moderate"
        else:
            flow_analysis["user_engagement"] = "low"
        
        flow_analysis["recommendations_given"] = recommendations_count
        flow_analysis["feedback_received"] = feedback_count
        flow_analysis["topic_progression"] = list(set(recent_intents))
        
        return flow_analysis

    def get_service_info(self) -> Dict[str, Any]:
        """Get service information."""
        return {
            "service_name": "Enhanced Intent Service",
            "ai_available": self.has_ai,
            "openai_available": self.openai_client is not None,
            "capabilities": [
                "enhanced_intent_recognition",
                "sophisticated_entity_extraction", 
                "conversation_flow_analysis",
                "context_aware_analysis",
                "multi_turn_conversation_support"
            ],
            "supported_intents": [
                "book_recommendation",
                "discovery_mode", 
                "feedback",
                "purchase_inquiry",
                "reading_progress",
                "general_conversation"
            ],
            "supported_entities": [
                "book_titles",
                "authors",
                "genres", 
                "languages",
                "reading_preferences",
                "feedback_indicators"
            ]
        }