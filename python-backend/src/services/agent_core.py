"""AWS Agent Core integration service."""

import boto3
import httpx
from typing import Dict, List, Optional, Any
from datetime import datetime

from src.config import settings


class AgentCoreService:
    """Service for integrating with AWS Agent Core."""

    def __init__(self):
        """Initialize AWS Agent Core service."""
        self.endpoint = settings.agent_core_endpoint
        self.api_key = settings.agent_core_api_key
        self.session = boto3.Session(
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            region_name=settings.aws_region
        )

    async def analyze_intent(self, message: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Analyze user message intent using AWS Agent Core."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.endpoint}/analyze-intent",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "message": message,
                        "context": context or {},
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            # Fallback to basic intent analysis
            return self._fallback_intent_analysis(message)

    async def extract_entities(self, message: str) -> Dict[str, List[str]]:
        """Extract entities from user message."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.endpoint}/extract-entities",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "message": message,
                        "entity_types": ["book_title", "author", "genre", "language"]
                    }
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            # Fallback to basic entity extraction
            return self._fallback_entity_extraction(message)

    async def generate_response(
        self,
        user_message: str,
        intent: Dict,
        context: Dict,
        recommendations: Optional[List[Dict]] = None
    ) -> str:
        """Generate conversational response using AWS Agent Core."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.endpoint}/generate-response",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "user_message": user_message,
                        "intent": intent,
                        "context": context,
                        "recommendations": recommendations or [],
                        "persona": "noah_reading_agent"
                    }
                )
                response.raise_for_status()
                return response.json().get("response", "I'm here to help with your reading!")
        except Exception as e:
            # Fallback to basic response generation
            return self._fallback_response_generation(user_message, intent)

    async def update_conversation_context(
        self,
        session_id: str,
        user_message: str,
        agent_response: str,
        intent: Dict
    ) -> Dict:
        """Update conversation context using AWS Agent Core."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.endpoint}/update-context",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "session_id": session_id,
                        "user_message": user_message,
                        "agent_response": agent_response,
                        "intent": intent,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            # Fallback context update
            return {
                "session_id": session_id,
                "updated_context": {
                    "last_intent": intent.get("intent", "unknown"),
                    "last_update": datetime.utcnow().isoformat()
                }
            }

    def _fallback_intent_analysis(self, message: str) -> Dict[str, Any]:
        """Fallback intent analysis when AWS Agent Core is unavailable."""
        message_lower = message.lower()

        # Check for purchase intent first (more specific)
        if any(word in message_lower for word in ["buy", "purchase", "get", "order", "where can i"]):
            return {
                "intent": "purchase_inquiry",
                "confidence": 0.7,
                "entities": {}
            }
        elif any(word in message_lower for word in ["surprise", "lucky", "discover", "new"]):
            return {
                "intent": "discovery_mode",
                "confidence": 0.7,
                "entities": {}
            }
        elif any(word in message_lower for word in ["recommend", "suggest", "book", "read"]):
            return {
                "intent": "book_recommendation",
                "confidence": 0.7,
                "entities": {}
            }
        else:
            return {
                "intent": "general_conversation",
                "confidence": 0.5,
                "entities": {}
            }

    def _fallback_entity_extraction(self, message: str) -> Dict[str, List[str]]:
        """Fallback entity extraction."""
        # Basic keyword-based entity extraction
        entities = {
            "book_title": [],
            "author": [],
            "genre": [],
            "language": []
        }

        # Simple pattern matching (to be enhanced)
        if "japanese" in message.lower():
            entities["language"].append("japanese")
        if "english" in message.lower():
            entities["language"].append("english")

        return entities

    def _fallback_response_generation(self, user_message: str, intent: Dict) -> str:
        """Fallback response generation."""
        intent_type = intent.get("intent", "general_conversation")

        responses = {
            "book_recommendation": "I'd be happy to recommend some books for you! What genres or topics interest you?",
            "purchase_inquiry": "I can help you find where to buy that book. Let me generate some purchase links for you.",
            "discovery_mode": "Let's explore something new! I'll find some books outside your usual preferences.",
            "general_conversation": "I'm Noah, your reading companion. How can I help you discover your next great read?"
        }

        return responses.get(intent_type, responses["general_conversation"])
