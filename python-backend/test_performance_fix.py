#!/usr/bin/env python3
"""
Performance test to verify discovery engine optimizations.
"""
import asyncio
import time
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from src.database import get_db
from src.services.discovery_engine import DiscoveryModeEngine
from src.models.user_profile import UserProfile
from src.models.content import ContentItem
from src.schemas.user_profile import PreferenceModel, LanguageReadingLevels


async def test_discovery_performance():
    """Test discovery engine performance with optimizations."""
    print("Testing discovery engine performance...")
    
    # Get database session
    db = next(get_db())
    
    try:
        # Create test user profile
        test_user_id = "perf_test_user"
        
        # Create minimal test profile
        preferences = PreferenceModel(
            topics=[
                {"topic": "mystery", "weight": 0.8, "confidence": 0.9, 
                 "last_updated": datetime.utcnow().isoformat(), "evolution_trend": "stable"},
                {"topic": "fiction", "weight": 0.7, "confidence": 0.8,
                 "last_updated": datetime.utcnow().isoformat(), "evolution_trend": "increasing"}
            ],
            content_types=[
                {"type": "novel", "preference": 0.9, 
                 "last_updated": datetime.utcnow().isoformat(), "evolution_trend": "stable"}
            ],
            contextual_preferences=[
                {"context": "evening", "preference_adjustments": {},
                 "last_updated": datetime.utcnow().isoformat()}
            ],
            evolution_history=[
                {"timestamp": datetime.utcnow().isoformat(), "change": "initial_setup",
                 "last_updated": datetime.utcnow().isoformat()}
            ]
        )
        
        reading_levels = LanguageReadingLevels(
            english={"level": "advanced", "confidence": 0.9},
            japanese={"level": "intermediate", "confidence": 0.7}
        )
        
        # Check if profile exists, create if not
        existing_profile = db.query(UserProfile).filter(
            UserProfile.user_id == test_user_id
        ).first()
        
        if not existing_profile:
            profile = UserProfile(
                user_id=test_user_id,
                preferences=preferences.dict(),
                reading_levels=reading_levels.dict(),
                created_at=datetime.utcnow(),
                last_updated=datetime.utcnow()
            )
            db.add(profile)
            db.commit()
        
        # Initialize discovery engine
        discovery_engine = DiscoveryModeEngine()
        
        # Test performance
        start_time = time.time()
        
        recommendations = await discovery_engine.generate_discovery_recommendations(
            user_id=test_user_id,
            limit=3,
            language="english",
            db=db
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"Discovery recommendations generated in {duration:.2f} seconds")
        print(f"Number of recommendations: {len(recommendations)}")
        
        # Performance expectations
        if duration < 10:  # Should be much faster than 60 seconds
            print("✅ Performance optimization successful!")
            print(f"   - Time: {duration:.2f}s (target: <10s)")
            print(f"   - Recommendations: {len(recommendations)}")
        else:
            print("❌ Performance still needs improvement")
            print(f"   - Time: {duration:.2f}s (target: <10s)")
        
        # Show sample recommendation
        if recommendations:
            sample = recommendations[0]
            print(f"\nSample recommendation:")
            print(f"   - Title: {sample.get('title', 'N/A')}")
            print(f"   - Divergence Score: {sample.get('divergence_score', 'N/A'):.2f}")
            print(f"   - Discovery Reason: {sample.get('discovery_reason', 'N/A')[:100]}...")
        
    except Exception as e:
        print(f"Error during performance test: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(test_discovery_performance())