#!/usr/bin/env python3
"""Simple test script to verify the health endpoint works."""

import requests
import sys

def test_health_endpoint():
    """Test the health endpoint locally."""
    try:
        # Test local health endpoint
        response = requests.get('http://localhost:8000/health', timeout=5)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            print("✅ Health check passed!")
            return True
        else:
            print("❌ Health check failed!")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False

if __name__ == "__main__":
    success = test_health_endpoint()
    sys.exit(0 if success else 1)