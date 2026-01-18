"""Integration tests for core systems checkpoint - Task 6."""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.orm import Session

from src.services.conversation_service import ConversationService
from src.services.content_processor import ContentProcessor
from src.services.user_profile_service import UserProfileEngine
from src.models.conversation import ConversationSession, ConversationMessage
from src.models.user_profile import UserProfile
from src.models.content import ContentItem
from src.schemas.content import ContentMetadata


class TestCoreSystemsIntegration:
    """Test integration between chat, content processing, and user profiles."""

    @pytest.fixture
    def conversation_service(self):
        """Create conversation service with mocked dependencies."""
        service = ConversationService()
        service.agent_core = AsyncMock()
        return service

    @pytest.fixture
    def content_processor(self):
        """Create content processor instance."""
        return ContentProcessor()

    @pytest.fixture
    def user_profile_engine(self):
        """Create user profile engine instance."""
        return UserProfileEngine()

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = MagicMock(spec=Session)
        return db

    @pytest.fixture
    def sample_english_content(self):
        """Sample English content for testing."""
        return {
            "content": """
            The implementation of sophisticated algorithms requires comprehensive understanding 
            of computational complexity theory. Furthermore, the optimization of performance 
            characteristics necessitates careful consideration of algorithmic trade-offs.
            Machine learning models demonstrate remarkable capabilities in pattern recognition
            and data analysis tasks.
            """,
            "metadata": ContentMetadata(
                author="Dr. Computer Science",
                source="Academic Journal",
                publish_date=datetime.utcnow(),
                content_type="article",
                estimated_reading_time=10,
                tags=["computer science", "algorithms", "machine learning"]
            ),
            "title": "Advanced Algorithms in Computer Science"
        }

    @pytest.fixture
    def sample_japanese_content(self):
        """Sample Japanese content for testing."""
        return {
            "content": """
            高度なアルゴリズムの実装には、計算複雑性理論の包括的な理解が必要である。
            さらに、性能特性の最適化には、アルゴリズムのトレードオフを慎重に検討する必要がある。
            機械学習モデルは、パターン認識とデータ分析タスクにおいて驚くべき能力を示している。
            """,
            "metadata": ContentMetadata(
                author="コンピュータサイエンス博士",
                source="学術雑誌",
                publish_date=datetime.utcnow(),
                content_type="article",
                estimated_reading_time=8,
                tags=["コンピュータサイエンス", "アルゴリズム", "機械学習"]
            ),
            "title": "コンピュータサイエンスの高度なアルゴリズム"
        }

    @pytest.mark.asyncio
    async def test_conversation_with_content_processing_integration(
        self, conversation_service, content_processor, mock_db, sample_english_content
    ):
        """Test conversation service integrating with content processing."""

        # Mock agent core responses
        conversation_service.agent_core.analyze_intent.return_value = {
            "intent": "book_recommendation",
            "confidence": 0.9
        }
        conversation_service.agent_core.extract_entities.return_value = {
            "book_title": [],
            "author": [],
            "genre": ["computer science"],
            "language": ["english"]
        }
        conversation_service.agent_core.generate_response.return_value = (
            "Based on your interest in computer science, here are some recommendations:"
        )

        # Mock database operations
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        # Process content to simulate having analyzed content available
        # Create a mock metadata object with title for the content processor
        content_with_title = type('MockMetadata', (), {
            **sample_english_content["metadata"].__dict__,
            'title': sample_english_content["title"]
        })()

        analysis = content_processor.analyze_content(
            sample_english_content["content"],
            "english",
            content_with_title
        )

        # Verify content analysis worked
        assert analysis is not None
        assert analysis.reading_level["level"] in [
            "beginner", "intermediate", "advanced", "expert"]
        assert len(analysis.topics) > 0
        assert len(analysis.embedding) > 0

        # Test conversation processing
        session_id = "session_testuser_123456"
        user_message = "Can you recommend some computer science books?"

        response = await conversation_service.process_user_message(
            session_id, user_message, mock_db
        )

        # Verify conversation response
        assert response is not None
        assert "noah_response" in response
        assert response["noah_response"]["type"] == "recommendation"
        assert "recommendations" in response["noah_response"]["metadata"]

        # Verify database interactions
        mock_db.add.assert_called()
        mock_db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_multilingual_content_processing(
        self, content_processor, sample_english_content, sample_japanese_content
    ):
        """Test multilingual content processing capabilities."""

        # Test English content processing
        english_analysis = content_processor.analyze_content(
            sample_english_content["content"],
            "english",
            sample_english_content["metadata"]
        )

        assert english_analysis is not None
        assert "flesch_kincaid" in english_analysis.reading_level
        assert english_analysis.reading_level["level"] in [
            "advanced", "expert"]  # Complex content
        assert english_analysis.complexity["lexical_diversity"] > 0
        assert len(english_analysis.topics) > 0

        # Test Japanese content processing
        japanese_analysis = content_processor.analyze_content(
            sample_japanese_content["content"],
            "japanese",
            sample_japanese_content["metadata"]
        )

        assert japanese_analysis is not None
        assert "kanji_density" in japanese_analysis.reading_level
        # High kanji content
        assert japanese_analysis.reading_level["kanji_density"] > 0.4
        assert japanese_analysis.reading_level["level"] in [
            "advanced", "expert"]
        assert len(japanese_analysis.topics) > 0

        # Verify both have embeddings
        assert len(english_analysis.embedding) > 0
        assert len(japanese_analysis.embedding) > 0
        assert len(english_analysis.embedding) == len(
            japanese_analysis.embedding)  # Same model

    @pytest.mark.asyncio
    async def test_user_profile_integration_with_content(
        self, user_profile_engine, content_processor, mock_db, sample_english_content
    ):
        """Test user profile engine integration with content analysis."""

        # Mock database operations for user profile
        mock_profile = UserProfile(
            user_id="test_user_123",
            preferences={
                "topics": [],
                "content_types": [],
                "contextual_preferences": [],
                "evolution_history": []
            },
            reading_levels={
                "english": {"level": 8.0, "confidence": 0.5, "assessment_count": 0},
                "japanese": {"level": 0.3, "confidence": 0.5, "assessment_count": 0}
            }
        )

        mock_db.query.return_value.filter.return_value.first.return_value = mock_profile
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        # Process content first
        content_analysis = content_processor.analyze_content(
            sample_english_content["content"],
            "english",
            sample_english_content["metadata"]
        )

        # Test reading level assessment
        performance_metrics = {
            "completion_rate": 0.85,
            "reading_speed": 220.0,  # Slower than average for complex content
            "pause_patterns": [{"duration": 10}, {"duration": 15}],
            "interactions": [{"type": "highlight"}, {"type": "note"}]
        }

        new_level = await user_profile_engine.assess_reading_level(
            "test_user_123",
            "english",
            content_analysis.dict(),
            performance_metrics,
            mock_db
        )

        # Verify reading level assessment
        assert new_level is not None
        assert "level" in new_level
        assert "confidence" in new_level
        assert new_level["assessment_count"] == 1

        # Test preference updates from feedback
        feedback_data = {
            "type": "explicit",
            "value": 0.8,  # Positive feedback
            "context": {"device_type": "desktop", "time_of_day": "afternoon"}
        }

        # Mock content item for feedback processing
        mock_content = ContentItem(
            id="content_123",
            title="Test Article",
            content=sample_english_content["content"],
            language="english",
            content_metadata=sample_english_content["metadata"].dict(),
            analysis=content_analysis.dict()
        )
        mock_db.query.return_value.filter.return_value.first.return_value = mock_content

        await user_profile_engine.update_preferences_from_feedback(
            "test_user_123", "content_123", feedback_data, mock_db
        )

        # Verify database operations
        mock_db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_conversation_flow_with_recommendations(
        self, conversation_service, mock_db
    ):
        """Test complete conversation flow with basic recommendation requests."""

        # Mock agent core for different conversation types
        conversation_service.agent_core.analyze_intent.side_effect = [
            {"intent": "book_recommendation", "confidence": 0.9},
            {"intent": "discovery_mode", "confidence": 0.8},
            {"intent": "purchase_inquiry", "confidence": 0.7}
        ]
        conversation_service.agent_core.extract_entities.return_value = {
            "book_title": [], "author": [], "genre": [], "language": ["english"]
        }
        conversation_service.agent_core.generate_response.side_effect = [
            "Here are some great book recommendations for you!",
            "I'm feeling adventurous! Here's something different:",
            "Here are some places where you can find this book:"
        ]

        # Mock database operations
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        session_id = "session_testuser_123456"

        # Test 1: Book recommendation request
        response1 = await conversation_service.process_user_message(
            session_id, "Can you recommend some books?", mock_db
        )

        assert response1["noah_response"]["type"] == "recommendation"
        assert "recommendations" in response1["noah_response"]["metadata"]
        assert len(response1["noah_response"]
                   ["metadata"]["recommendations"]) > 0

        # Test 2: Discovery mode request
        response2 = await conversation_service.process_user_message(
            session_id, "I'm feeling lucky!", mock_db
        )

        assert response2["noah_response"]["type"] == "recommendation"
        assert "recommendations" in response2["noah_response"]["metadata"]

        # Test 3: Purchase inquiry
        response3 = await conversation_service.process_user_message(
            session_id, "Where can I buy this book?", mock_db
        )

        assert response3["noah_response"]["type"] == "text"

        # Verify all interactions were stored
        assert mock_db.add.call_count >= 6  # 3 user messages + 3 noah responses

    @pytest.mark.asyncio
    async def test_error_handling_integration(
        self, conversation_service, content_processor, mock_db
    ):
        """Test error handling across integrated systems."""

        # Test conversation service error handling
        conversation_service.agent_core.analyze_intent.side_effect = Exception(
            "NLU service unavailable")

        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        response = await conversation_service.process_user_message(
            "session_test", "Hello", mock_db
        )

        # Should return error response but not crash
        assert "error" in response
        assert response["noah_response"]["type"] == "text"

        # Test content processor error handling
        invalid_metadata = ContentMetadata(
            author="Test",
            source="Test",
            publish_date=datetime.utcnow(),
            content_type="test",
            estimated_reading_time=1,
            tags=[]
        )

        # Should handle empty content gracefully
        analysis = content_processor.analyze_content(
            "", "english", invalid_metadata)
        assert analysis is not None
        assert analysis.reading_level["level"] == "beginner"

        # Should handle unsupported language
        with pytest.raises(ValueError, match="Unsupported language"):
            content_processor.analyze_content(
                "test", "french", invalid_metadata)

    def test_content_processor_edge_cases(self, content_processor):
        """Test content processor with various edge cases."""

        metadata = ContentMetadata(
            author="Test Author",
            source="Test Source",
            publish_date=datetime.utcnow(),
            content_type="test",
            estimated_reading_time=1,
            tags=["test"]
        )

        # Test very short content
        short_analysis = content_processor.analyze_content(
            "Hi.", "english", metadata)
        assert short_analysis is not None
        assert short_analysis.reading_level["level"] == "beginner"

        # Test content with special characters
        special_content = "Hello! @#$%^&*() This has special characters... 123456"
        special_analysis = content_processor.analyze_content(
            special_content, "english", metadata)
        assert special_analysis is not None
        assert len(special_analysis.embedding) > 0

        # Test Japanese content with mixed scripts
        mixed_japanese = "これはテストです。This is a test. 123 テスト！"
        japanese_analysis = content_processor.analyze_content(
            mixed_japanese, "japanese", metadata)
        assert japanese_analysis is not None
        assert japanese_analysis.reading_level["character_variety"] > 0

    @pytest.mark.asyncio
    async def test_session_management_integration(self, conversation_service, mock_db):
        """Test session management across conversation flows."""

        # Mock session creation and retrieval
        mock_session = ConversationSession(
            session_id="session_testuser_123456",
            user_id="testuser",
            context={"current_topic": None, "discovery_mode_active": False}
        )

        # First call returns None (new session), subsequent calls return existing session
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            None, mock_session, mock_session]
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock(side_effect=lambda x: setattr(
            x, 'session_id', mock_session.session_id))

        # Mock agent core
        conversation_service.agent_core.analyze_intent.return_value = {
            "intent": "general_conversation"}
        conversation_service.agent_core.extract_entities.return_value = {
            "language": ["english"]}
        conversation_service.agent_core.generate_response.return_value = "Hello! How can I help you?"

        session_id = "session_testuser_123456"

        # First message - should create new session
        response1 = await conversation_service.process_user_message(
            session_id, "Hello", mock_db
        )

        assert response1 is not None
        mock_db.add.assert_called()  # Session should be created

        # Second message - should use existing session
        response2 = await conversation_service.process_user_message(
            session_id, "How are you?", mock_db
        )

        assert response2 is not None
        # Session should be retrieved, not created again

    def test_performance_metrics_calculation(self, user_profile_engine):
        """Test performance metrics calculation for reading assessment."""

        # Test high performance metrics
        high_performance = {
            "completion_rate": 0.95,
            "reading_speed": 280.0,
            "pause_patterns": [],  # No pauses
            "interactions": [{"type": "highlight"}, {"type": "note"}]
        }

        score = user_profile_engine._calculate_performance_score(
            high_performance)
        assert 0.8 <= score <= 1.0

        # Test low performance metrics
        low_performance = {
            "completion_rate": 0.3,
            "reading_speed": 80.0,
            "pause_patterns": [{"duration": 30}] * 10,  # Many long pauses
            "interactions": []
        }

        score = user_profile_engine._calculate_performance_score(
            low_performance)
        assert 0.0 <= score <= 0.4

        # Test medium performance metrics
        medium_performance = {
            "completion_rate": 0.7,
            "reading_speed": 200.0,
            "pause_patterns": [{"duration": 5}] * 3,
            "interactions": [{"type": "highlight"}]
        }

        score = user_profile_engine._calculate_performance_score(
            medium_performance)
        assert 0.4 <= score <= 0.8


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
