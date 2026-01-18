"""
Final System Validation Tests for Noah Reading Agent

This test suite validates the core functionality and integration
of the Noah Reading Agent system according to task 15.2 requirements.
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock

from src.services.content_processor import ContentProcessor
from src.services.user_profile_service import UserProfileEngine
from src.services.recommendation_engine import ContextualRecommendationEngine
from src.services.discovery_engine import DiscoveryEngine
from src.services.conversation_service import ConversationService
from src.schemas.content import ContentMetadata
from src.schemas.user_profile import PreferenceModel, LanguageReadingLevels


class TestSystemValidation:
    """Test suite for final system validation."""

    @pytest.fixture
    def content_processor(self):
        """Create content processor instance."""
        return ContentProcessor()

    @pytest.fixture
    def user_profile_engine(self):
        """Create user profile engine instance."""
        return UserProfileEngine()

    @pytest.fixture
    def recommendation_engine(self):
        """Create recommendation engine instance."""
        return ContextualRecommendationEngine()

    @pytest.fixture
    def discovery_engine(self):
        """Create discovery engine instance."""
        return DiscoveryEngine()

    @pytest.fixture
    def conversation_service(self):
        """Create conversation service instance."""
        return ConversationService()

    @pytest.fixture
    def sample_english_content(self):
        """Sample English content for testing."""
        return {
            "title": "The Art of Reading",
            "content": "Reading is a fundamental skill that opens doors to knowledge and imagination. It allows us to explore different worlds, learn new concepts, and develop critical thinking abilities. Through reading, we can gain insights into various cultures, historical events, and scientific discoveries.",
            "language": "english"
        }

    @pytest.fixture
    def sample_japanese_content(self):
        """Sample Japanese content for testing."""
        return {
            "title": "読書の芸術",
            "content": "読書は知識と想像力への扉を開く基本的なスキルです。それは私たちが異なる世界を探索し、新しい概念を学び、批判的思考能力を発達させることを可能にします。読書を通じて、私たちは様々な文化、歴史的出来事、科学的発見についての洞察を得ることができます。",
            "language": "japanese"
        }

    @pytest.fixture
    def sample_metadata(self):
        """Sample content metadata."""
        return ContentMetadata(
            author="Test Author",
            source="Test Source",
            publish_date=datetime.utcnow(),
            content_type="article",
            estimated_reading_time=5,
            tags=["education", "reading"]
        )

    def test_multilingual_content_processing(self, content_processor, sample_english_content, sample_japanese_content, sample_metadata):
        """Test that multilingual content processing works correctly."""
        # Test English content processing
        english_analysis = content_processor.analyze_content(
            content=sample_english_content["content"],
            language=sample_english_content["language"],
            metadata=sample_metadata,
            title=sample_english_content["title"]
        )
        
        assert english_analysis is not None
        assert len(english_analysis.topics) > 0
        assert "reading_level" in english_analysis.reading_level
        assert len(english_analysis.embedding) > 0
        
        # Test Japanese content processing
        japanese_analysis = content_processor.analyze_content(
            content=sample_japanese_content["content"],
            language=sample_japanese_content["language"],
            metadata=sample_metadata,
            title=sample_japanese_content["title"]
        )
        
        assert japanese_analysis is not None
        assert len(japanese_analysis.topics) > 0
        assert "reading_level" in japanese_analysis.reading_level
        assert len(japanese_analysis.embedding) > 0

    def test_user_profile_creation_and_management(self, user_profile_engine):
        """Test user profile creation and management functionality."""
        with patch('src.services.database.get_session') as mock_session:
            mock_db = Mock()
            mock_session.return_value.__enter__.return_value = mock_db
            mock_db.query.return_value.filter.return_value.first.return_value = None
            
            # Test creating new user profile
            profile = user_profile_engine.get_or_create_profile("test_user", mock_db)
            
            assert profile is not None
            assert profile.user_id == "test_user"
            assert "topics" in profile.preferences
            assert "english" in profile.reading_levels
            assert "japanese" in profile.reading_levels

    def test_recommendation_generation(self, recommendation_engine):
        """Test recommendation generation functionality."""
        with patch('src.services.database.get_session') as mock_session:
            mock_db = Mock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            # Mock user profile
            mock_profile = Mock()
            mock_profile.preferences = {
                "topics": [{"topic": "education", "weight": 0.8}],
                "content_types": [],
                "contextual_preferences": [],
                "evolution_history": []
            }
            mock_profile.reading_levels = {
                "english": {"level": 5.0, "confidence": 0.8},
                "japanese": {"level": 3.0, "confidence": 0.6}
            }
            
            mock_db.query.return_value.filter.return_value.first.return_value = mock_profile
            mock_db.query.return_value.filter.return_value.all.return_value = []
            
            # Test recommendation generation
            recommendations = recommendation_engine.generate_contextual_recommendations(
                user_id="test_user",
                context={"available_time": 30, "device_type": "mobile"},
                limit=5,
                db=mock_db
            )
            
            assert isinstance(recommendations, list)

    def test_discovery_mode_functionality(self, discovery_engine):
        """Test discovery mode functionality."""
        with patch('src.services.database.get_session') as mock_session:
            mock_db = Mock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            # Mock user profile with established preferences
            mock_profile = Mock()
            mock_profile.preferences = {
                "topics": [{"topic": "science", "weight": 0.9}],
                "content_types": [],
                "contextual_preferences": [],
                "evolution_history": []
            }
            mock_profile.reading_levels = {
                "english": {"level": 6.0, "confidence": 0.9}
            }
            
            mock_db.query.return_value.filter.return_value.first.return_value = mock_profile
            mock_db.query.return_value.filter.return_value.all.return_value = []
            
            # Test discovery recommendations
            discovery_recs = discovery_engine.generate_discovery_recommendations(
                user_id="test_user",
                limit=3,
                db=mock_db
            )
            
            assert isinstance(discovery_recs, list)

    @pytest.mark.asyncio
    async def test_conversational_interface(self, conversation_service):
        """Test conversational interface functionality."""
        with patch('src.services.database.get_session') as mock_session:
            mock_db = Mock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            # Mock session and user profile creation
            mock_db.query.return_value.filter.return_value.first.return_value = None
            mock_db.add = Mock()
            mock_db.commit = Mock()
            mock_db.refresh = Mock()
            
            # Test processing user message
            result = await conversation_service.process_user_message(
                session_id="test_session_user123_123456",
                user_message="Can you recommend some books about science?",
                db=mock_db
            )
            
            assert "noah_response" in result
            assert "user_message" in result
            assert result["noah_response"]["sender"] == "noah"
            assert result["user_message"]["sender"] == "user"

    def test_preference_transparency_and_control(self, user_profile_engine):
        """Test preference transparency and control features."""
        with patch('src.services.database.get_session') as mock_session:
            mock_db = Mock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            # Mock user profile with preferences
            mock_profile = Mock()
            mock_profile.preferences = {
                "topics": [
                    {"topic": "science", "weight": 0.8, "confidence": 0.9},
                    {"topic": "history", "weight": 0.6, "confidence": 0.7}
                ],
                "content_types": [],
                "contextual_preferences": [],
                "evolution_history": []
            }
            
            mock_db.query.return_value.filter.return_value.first.return_value = mock_profile
            mock_db.query.return_value.filter.return_value.all.return_value = []
            
            # Test getting preference transparency
            transparency = user_profile_engine.get_preference_transparency("test_user", mock_db)
            
            assert "learned_preferences" in transparency
            assert "derivation_explanations" in transparency
            assert "confidence_scores" in transparency

    def test_performance_requirements(self, content_processor, sample_english_content, sample_metadata):
        """Test that system meets basic performance requirements."""
        import time
        
        # Test content processing performance
        start_time = time.time()
        
        analysis = content_processor.analyze_content(
            content=sample_english_content["content"],
            language=sample_english_content["language"],
            metadata=sample_metadata,
            title=sample_english_content["title"]
        )
        
        processing_time = time.time() - start_time
        
        # Content processing should complete within reasonable time (5 seconds)
        assert processing_time < 5.0
        assert analysis is not None

    def test_error_handling_and_resilience(self, content_processor, sample_metadata):
        """Test error handling and system resilience."""
        # Test handling of empty content
        analysis = content_processor.analyze_content(
            content="",
            language="english",
            metadata=sample_metadata,
            title="Empty Content Test"
        )
        assert analysis is not None
        
        # Test handling of very short content
        analysis = content_processor.analyze_content(
            content="Hi.",
            language="english",
            metadata=sample_metadata,
            title="Short Content Test"
        )
        assert analysis is not None
        
        # Test handling of unsupported language
        with pytest.raises(ValueError, match="Unsupported language"):
            content_processor.analyze_content(
                content="Bonjour le monde",
                language="french",
                metadata=sample_metadata,
                title="French Content Test"
            )

    def test_data_isolation_and_privacy(self, user_profile_engine):
        """Test user data isolation and privacy requirements."""
        with patch('src.services.database.get_session') as mock_session:
            mock_db = Mock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            # Mock different user profiles
            user1_profile = Mock()
            user1_profile.user_id = "user1"
            user1_profile.preferences = {"topics": [{"topic": "science", "weight": 0.8}]}
            
            user2_profile = Mock()
            user2_profile.user_id = "user2"
            user2_profile.preferences = {"topics": [{"topic": "art", "weight": 0.9}]}
            
            # Test that user data is properly isolated
            mock_db.query.return_value.filter.return_value.first.side_effect = [user1_profile, user2_profile]
            
            profile1 = user_profile_engine.get_or_create_profile("user1", mock_db)
            profile2 = user_profile_engine.get_or_create_profile("user2", mock_db)
            
            # Verify data isolation
            assert profile1.user_id != profile2.user_id
            assert profile1.preferences != profile2.preferences

    def test_system_integration_workflow(self, content_processor, user_profile_engine, recommendation_engine, sample_english_content, sample_metadata):
        """Test complete system integration workflow."""
        with patch('src.services.database.get_session') as mock_session:
            mock_db = Mock()
            mock_session.return_value.__enter__.return_value = mock_db
            mock_db.query.return_value.filter.return_value.first.return_value = None
            mock_db.query.return_value.filter.return_value.all.return_value = []
            
            # Step 1: Process content
            analysis = content_processor.analyze_content(
                content=sample_english_content["content"],
                language=sample_english_content["language"],
                metadata=sample_metadata,
                title=sample_english_content["title"]
            )
            assert analysis is not None
            
            # Step 2: Create user profile
            profile = user_profile_engine.get_or_create_profile("integration_test_user", mock_db)
            assert profile is not None
            
            # Step 3: Generate recommendations
            recommendations = recommendation_engine.generate_contextual_recommendations(
                user_id="integration_test_user",
                context={"available_time": 20},
                limit=3,
                db=mock_db
            )
            assert isinstance(recommendations, list)


class TestSystemOptimization:
    """Test suite for system optimization validation."""

    def test_memory_usage_optimization(self):
        """Test that system uses memory efficiently."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Create multiple content processor instances
        processors = [ContentProcessor() for _ in range(5)]
        
        current_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = current_memory - initial_memory
        
        # Memory increase should be reasonable (less than 100MB for 5 instances)
        assert memory_increase < 100
        
        # Clean up
        del processors

    def test_concurrent_processing_capability(self, content_processor, sample_metadata):
        """Test system's ability to handle concurrent requests."""
        import concurrent.futures
        import threading
        
        def process_content(content_id):
            return content_processor.analyze_content(
                content=f"This is test content number {content_id}. It contains multiple sentences for analysis.",
                language="english",
                metadata=sample_metadata,
                title=f"Test Content {content_id}"
            )
        
        # Test concurrent processing
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(process_content, i) for i in range(5)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # All requests should complete successfully
        assert len(results) == 5
        assert all(result is not None for result in results)

    @pytest.fixture
    def sample_metadata(self):
        """Sample content metadata."""
        return ContentMetadata(
            author="Test Author",
            source="Test Source",
            publish_date=datetime.utcnow(),
            content_type="article",
            estimated_reading_time=5,
            tags=["test"]
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])