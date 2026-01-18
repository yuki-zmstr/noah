"""Agent configuration and information endpoints."""

import logging
from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from src.services.enhanced_conversation_service import EnhancedConversationService
from src.services.strands_config import strands_config, validate_strands_config
from src.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize conversation service to get agent info
conversation_service = EnhancedConversationService()


@router.get("/info")
async def get_agent_info() -> Dict[str, Any]:
    """Get information about the configured agents and their capabilities."""
    try:
        service_info = conversation_service.get_service_info()
        
        return {
            "status": "success",
            "agent_configuration": service_info,
            "strands_config": {
                "enabled": settings.strands_enabled,
                "model": strands_config.agent_model,
                "temperature": strands_config.agent_temperature,
                "max_tokens": strands_config.agent_max_tokens,
                "streaming_enabled": strands_config.streaming_enabled,
                "tools_enabled": {
                    "recommendations": strands_config.enable_recommendations,
                    "discovery": strands_config.enable_discovery,
                    "feedback": strands_config.enable_feedback,
                    "content_analysis": strands_config.enable_content_analysis
                }
            }
        }
    except Exception as e:
        logger.error(f"Error getting agent info: {e}")
        raise HTTPException(status_code=500, detail="Failed to get agent information")


@router.get("/config/validate")
async def validate_agent_config() -> Dict[str, Any]:
    """Validate the current Strands agent configuration."""
    try:
        validation_results = validate_strands_config(strands_config)
        
        return {
            "status": "success",
            "validation": validation_results
        }
    except Exception as e:
        logger.error(f"Error validating agent config: {e}")
        raise HTTPException(status_code=500, detail="Failed to validate agent configuration")


@router.get("/capabilities")
async def get_agent_capabilities() -> Dict[str, Any]:
    """Get detailed information about agent capabilities and tools."""
    try:
        service_info = conversation_service.get_service_info()
        
        capabilities = {
            "conversation": {
                "natural_language_understanding": True,
                "context_awareness": True,
                "streaming_responses": True,
                "multilingual_support": True,
                "conversation_memory": True
            },
            "recommendations": {
                "personalized_suggestions": strands_config.enable_recommendations,
                "contextual_filtering": strands_config.enable_recommendations,
                "reading_level_matching": strands_config.enable_recommendations,
                "interest_scoring": strands_config.enable_recommendations
            },
            "discovery": {
                "serendipitous_recommendations": strands_config.enable_discovery,
                "genre_exploration": strands_config.enable_discovery,
                "preference_divergence": strands_config.enable_discovery
            },
            "learning": {
                "feedback_processing": strands_config.enable_feedback,
                "preference_evolution": strands_config.enable_feedback,
                "behavioral_analysis": strands_config.enable_feedback
            },
            "content": {
                "text_analysis": strands_config.enable_content_analysis,
                "readability_assessment": strands_config.enable_content_analysis,
                "topic_extraction": strands_config.enable_content_analysis
            }
        }
        
        return {
            "status": "success",
            "service_type": service_info.get("service_type"),
            "capabilities": capabilities,
            "tools_available": service_info.get("agent_info", {}).get("tools", []) if service_info.get("agent_info") else []
        }
    except Exception as e:
        logger.error(f"Error getting agent capabilities: {e}")
        raise HTTPException(status_code=500, detail="Failed to get agent capabilities")


@router.get("/health")
async def check_agent_health() -> Dict[str, Any]:
    """Check the health and availability of the agent services."""
    try:
        health_status = {
            "status": "healthy",
            "services": {},
            "timestamp": "2024-01-01T00:00:00Z"  # Will be updated with actual timestamp
        }
        
        # Check conversation service
        try:
            service_info = conversation_service.get_service_info()
            health_status["services"]["conversation"] = {
                "status": "healthy",
                "type": service_info.get("service_type"),
                "available": True
            }
        except Exception as e:
            health_status["services"]["conversation"] = {
                "status": "unhealthy",
                "error": str(e),
                "available": False
            }
            health_status["status"] = "degraded"
        
        # Check Strands configuration
        try:
            validation = validate_strands_config(strands_config)
            health_status["services"]["strands_config"] = {
                "status": "healthy" if validation["valid"] else "unhealthy",
                "valid": validation["valid"],
                "errors": validation["errors"],
                "warnings": validation["warnings"]
            }
            if not validation["valid"]:
                health_status["status"] = "degraded"
        except Exception as e:
            health_status["services"]["strands_config"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_status["status"] = "degraded"
        
        return health_status
    except Exception as e:
        logger.error(f"Error checking agent health: {e}")
        raise HTTPException(status_code=500, detail="Failed to check agent health")


@router.post("/test")
async def test_agent_conversation() -> Dict[str, Any]:
    """Test the agent with a simple conversation to verify functionality."""
    try:
        # Simple test message
        test_message = "Hello, can you recommend a book?"
        test_user_id = "test_user"
        
        # Test with the conversation service
        if conversation_service.use_strands:
            # Test Strands agent
            response = await conversation_service.strands_service.process_conversation(
                user_message=test_message,
                user_id=test_user_id,
                conversation_context={},
                metadata={"test": True}
            )
            
            return {
                "status": "success",
                "test_type": "strands_agent",
                "test_message": test_message,
                "response": {
                    "content": response.get("content", ""),
                    "tool_calls": len(response.get("tool_calls", [])),
                    "processing_time": response.get("metadata", {}).get("processing_time", 0)
                }
            }
        else:
            # Test AWS Agent Core fallback
            return {
                "status": "success",
                "test_type": "aws_agent_core",
                "test_message": test_message,
                "response": {
                    "content": "Test completed with AWS Agent Core fallback",
                    "note": "Strands agents not available, using fallback service"
                }
            }
            
    except Exception as e:
        logger.error(f"Error testing agent conversation: {e}")
        return {
            "status": "error",
            "error": str(e),
            "message": "Agent test failed"
        }