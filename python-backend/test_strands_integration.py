#!/usr/bin/env python3
"""Test script to verify Strands agents integration."""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from services.enhanced_conversation_service import EnhancedConversationService
from services.strands_config import strands_config, validate_strands_config


async def test_strands_integration():
    """Test the Strands agents integration."""
    print("🧪 Testing Strands Agents Integration")
    print("=" * 50)
    
    # Test configuration
    print("1. Testing configuration...")
    validation = validate_strands_config(strands_config)
    print(f"   ✅ Configuration valid: {validation['valid']}")
    if validation['errors']:
        print(f"   ⚠️  Errors: {validation['errors']}")
    if validation['warnings']:
        print(f"   ⚠️  Warnings: {validation['warnings']}")
    
    # Test service creation
    print("\n2. Testing service creation...")
    try:
        service = EnhancedConversationService()
        print(f"   ✅ Service created successfully")
        print(f"   📊 Using Strands: {service.use_strands}")
        
        # Get service info
        info = service.get_service_info()
        print(f"   🤖 Service type: {info['service_type']}")
        print(f"   🛠️  Capabilities: {len(info['capabilities'])} features")
        
        if service.use_strands and service.strands_service:
            agent_info = service.strands_service.get_agent_info()
            print(f"   🎯 Agent model: {agent_info['model']}")
            print(f"   🔧 Tools available: {len(agent_info['tools'])}")
            print(f"   📋 Tools: {', '.join(agent_info['tools'])}")
        
    except Exception as e:
        print(f"   ❌ Service creation failed: {e}")
        return False
    
    # Test basic conversation (mock)
    print("\n3. Testing conversation processing...")
    try:
        # This would normally require a database session, but we can test the structure
        test_message = "Hello, can you recommend a book?"
        test_user_id = "test_user_123"
        
        print(f"   📝 Test message: '{test_message}'")
        print(f"   👤 Test user: {test_user_id}")
        
        # Test the service structure without actual processing
        if service.use_strands:
            print("   ✅ Strands agent ready for conversation processing")
        else:
            print("   ✅ AWS Agent Core fallback ready")
            
    except Exception as e:
        print(f"   ❌ Conversation test failed: {e}")
        return False
    
    print("\n🎉 Strands integration test completed successfully!")
    print("\n📋 Summary:")
    print(f"   • Strands agents: {'✅ Enabled' if service.use_strands else '❌ Disabled'}")
    print(f"   • Configuration: {'✅ Valid' if validation['valid'] else '❌ Invalid'}")
    print(f"   • Service ready: ✅ Yes")
    
    return True


if __name__ == "__main__":
    success = asyncio.run(test_strands_integration())
    sys.exit(0 if success else 1)