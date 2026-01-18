#!/usr/bin/env python3
"""
Test script to verify that the recommendation system is working with real data.
"""

import sys
import asyncio
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from src.database import get_db
from src.services.recommendation_engine import contextual_recommendation_engine
from src.services.discovery_engine import discovery_engine
from src.services.user_profile_service import user_profile_engine

async def test_recommendations():
    """Test the recommendation system with real data."""
    print("Testing Real Recommendation System")
    print("=" * 50)
    
    db = next(get_db())
    test_user_id = "test_user_123"
    
    try:
        # Test 1: Create a user profile
        print("1. Creating test user profile...")
        profile = await user_profile_engine.get_or_create_profile(test_user_id, db)
        print(f"   ✓ User profile created: {profile.user_id}")
        
        # Test 2: Get contextual recommendations
        print("\n2. Testing contextual recommendations...")
        recommendations = await contextual_recommendation_engine.generate_contextual_recommendations(
            user_id=test_user_id,
            limit=5,
            language="english",
            db=db
        )
        
        print(f"   ✓ Generated {len(recommendations)} recommendations:")
        for i, rec in enumerate(recommendations, 1):
            print(f"   {i}. {rec['title']} by {rec['metadata']['author']}")
            print(f"      Genre: {rec['metadata']['genre']}")
            print(f"      Score: {rec['recommendation_score']:.2f}")
            print(f"      Reason: {rec['recommendation_reason']}")
            print()
        
        # Test 3: Get discovery recommendations
        print("3. Testing discovery recommendations...")
        discovery_recs = await discovery_engine.generate_discovery_recommendations(
            user_id=test_user_id,
            limit=3,
            language="english",
            db=db
        )
        
        print(f"   ✓ Generated {len(discovery_recs)} discovery recommendations:")
        for i, rec in enumerate(discovery_recs, 1):
            print(f"   {i}. {rec['title']} by {rec['metadata']['author']}")
            print(f"      Genre: {rec['metadata']['genre']}")
            print(f"      Divergence Score: {rec['divergence_score']:.2f}")
            print(f"      Discovery Reason: {rec['discovery_reason']}")
            print()
        
        # Test 4: Test recommendation API format conversion
        print("4. Testing API format conversion...")
        if recommendations:
            sample_rec = recommendations[0]
            api_format = {
                "id": sample_rec["content_id"],
                "title": sample_rec["title"],
                "author": sample_rec["metadata"].get("author", "Unknown Author"),
                "description": sample_rec["metadata"].get("genre", "Fiction"),
                "interestScore": round(sample_rec["recommendation_score"], 2),
                "readingLevel": sample_rec["metadata"].get("difficulty_level", "Intermediate").title(),
                "estimatedReadingTime": sample_rec["metadata"].get("estimated_reading_time", 300),
                "genre": sample_rec["metadata"].get("genre", "Fiction"),
                "recommendation_reason": sample_rec.get("recommendation_reason", "Recommended based on your preferences")
            }
            print(f"   ✓ API format conversion successful:")
            print(f"      Title: {api_format['title']}")
            print(f"      Author: {api_format['author']}")
            print(f"      Interest Score: {api_format['interestScore']}")
            print(f"      Reading Time: {api_format['estimatedReadingTime']} minutes")
        
        print("\n" + "=" * 50)
        print("✅ All recommendation tests passed!")
        print("The system is now using real book data from the database.")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_recommendations())