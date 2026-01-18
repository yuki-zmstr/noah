#!/usr/bin/env python3
"""Test script for Strands streaming with OpenTelemetry context fixes."""

import asyncio
import logging
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import telemetry config first
import src.telemetry_config

from src.services.strands_agent_service import StrandsAgentService
from src.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_strands_streaming():
    """Test Strands streaming functionality."""
    try:
        # Check if Strands is enabled
        if not settings.strands_enabled:
            logger.info("Strands is disabled in configuration")
            return
        
        # Initialize Strands service
        logger.info("Initializing Strands agent service...")
        strands_service = StrandsAgentService()
        
        # Test message
        test_message = "I'm feeling lucky! Surprise me with something new to read."
        test_user_id = "test_user_123"
        
        logger.info(f"Testing streaming with message: {test_message}")
        
        # Test streaming
        chunk_count = 0
        async for chunk in strands_service.stream_conversation(
            user_message=test_message,
            user_id=test_user_id,
            conversation_context={"test": True},
            metadata={"type": "discovery_mode"}
        ):
            chunk_count += 1
            logger.info(f"Chunk {chunk_count}: {chunk}")
            
            # Limit chunks for testing
            if chunk_count >= 10:
                logger.info("Stopping after 10 chunks for testing")
                break
        
        logger.info(f"Streaming test completed successfully with {chunk_count} chunks")
        
    except Exception as e:
        logger.error(f"Error during streaming test: {e}")
        raise


async def main():
    """Main test function."""
    logger.info("Starting Strands streaming test...")
    
    try:
        await test_strands_streaming()
        logger.info("Test completed successfully!")
    except Exception as e:
        logger.error(f"Test failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())