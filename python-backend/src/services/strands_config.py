"""Configuration service for Strands agents integration."""

import os
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

from src.config import settings


class StrandsConfig(BaseModel):
    """Configuration for Strands agents."""
    
    # Agent configuration
    agent_name: str = Field(default="noah_reading_agent", description="Name of the main agent")
    agent_model: str = Field(default="gpt-4o-mini", description="Model to use for the agent")
    agent_temperature: float = Field(default=0.7, description="Temperature for response generation")
    agent_max_tokens: int = Field(default=1000, description="Maximum tokens per response")
    
    # API configuration
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key")
    anthropic_api_key: Optional[str] = Field(default=None, description="Anthropic API key")
    
    # Tool configuration
    enable_recommendations: bool = Field(default=True, description="Enable recommendation tool")
    enable_discovery: bool = Field(default=True, description="Enable discovery mode tool")
    enable_purchase_links: bool = Field(default=True, description="Enable purchase link generation")
    enable_feedback: bool = Field(default=True, description="Enable feedback processing")
    enable_content_analysis: bool = Field(default=True, description="Enable content analysis")
    
    # Conversation configuration
    max_conversation_history: int = Field(default=10, description="Maximum conversation history to maintain")
    streaming_enabled: bool = Field(default=True, description="Enable streaming responses")
    streaming_chunk_size: int = Field(default=10, description="Words per streaming chunk")
    streaming_delay: float = Field(default=0.05, description="Delay between streaming chunks")
    
    # Performance configuration
    cache_enabled: bool = Field(default=True, description="Enable response caching")
    cache_ttl: int = Field(default=300, description="Cache TTL in seconds")
    timeout: int = Field(default=30, description="Request timeout in seconds")
    
    class Config:
        env_prefix = "STRANDS_"


def get_strands_config() -> StrandsConfig:
    """Get Strands configuration from environment variables and settings."""
    
    # Get API keys from environment or settings
    openai_key = os.getenv("OPENAI_API_KEY") or getattr(settings, "openai_api_key", None)
    anthropic_key = os.getenv("ANTHROPIC_API_KEY") or getattr(settings, "anthropic_api_key", None)
    
    config_data = {
        "openai_api_key": openai_key,
        "anthropic_api_key": anthropic_key,
    }
    
    # Add any environment-specific overrides
    if hasattr(settings, "strands_config"):
        config_data.update(settings.strands_config)
    
    return StrandsConfig(**config_data)


def validate_strands_config(config: StrandsConfig) -> Dict[str, Any]:
    """Validate Strands configuration and return validation results."""
    
    validation_results = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "config_summary": {}
    }
    
    # Check API keys
    if not config.openai_api_key and not config.anthropic_api_key:
        validation_results["errors"].append("No API keys configured for Strands agents")
        validation_results["valid"] = False
    
    if config.openai_api_key and not config.openai_api_key.startswith("sk-"):
        validation_results["warnings"].append("OpenAI API key format may be invalid")
    
    # Check model configuration
    if config.agent_temperature < 0 or config.agent_temperature > 2:
        validation_results["errors"].append("Agent temperature must be between 0 and 2")
        validation_results["valid"] = False
    
    if config.agent_max_tokens < 1 or config.agent_max_tokens > 4000:
        validation_results["warnings"].append("Agent max_tokens should be between 1 and 4000")
    
    # Check conversation configuration
    if config.max_conversation_history < 1:
        validation_results["errors"].append("max_conversation_history must be at least 1")
        validation_results["valid"] = False
    
    if config.streaming_chunk_size < 1:
        validation_results["errors"].append("streaming_chunk_size must be at least 1")
        validation_results["valid"] = False
    
    # Generate config summary
    validation_results["config_summary"] = {
        "agent_model": config.agent_model,
        "tools_enabled": {
            "recommendations": config.enable_recommendations,
            "discovery": config.enable_discovery,
            "purchase_links": config.enable_purchase_links,
            "feedback": config.enable_feedback,
            "content_analysis": config.enable_content_analysis
        },
        "streaming_enabled": config.streaming_enabled,
        "cache_enabled": config.cache_enabled,
        "api_keys_configured": {
            "openai": bool(config.openai_api_key),
            "anthropic": bool(config.anthropic_api_key)
        }
    }
    
    return validation_results


# Global configuration instance
strands_config = get_strands_config()