"""Simplified integration tests for core systems checkpoint - Task 6."""

import pytest
from datetime import datetime
from unittest.mock import MagicMock

from src.services.content_processor import ContentProcessor
from src.services.user_profile_service import UserProfileEngine
from src.schemas.content import ContentMetadata


class TestCoreSystemsIntegrationSimple:
    """Simplified test integration between core systems."""

    @pytest.fixture
    def content_processor(self):
        """Create content processor instance."""
        return ContentProcessor()

    @pytest.fixture
    def user_profile_engine(self):
        """Create user profile engine instance."""
        return UserProfileEngine()

    def test_english_content_processing(self, content_processor):
        """Test English content processing works."""
        content = """
        The implementation of sophisticated algorithms requires comprehensive understanding 
        of computational complexity theory. Furthermore, the optimization of performance 
        characteristics necessitates careful consideration of algorithmic trade-offs.
        """

        # Create metadata with title attribute
        metadata = type('MockMetadata', (), {
            'author': "Dr. Computer Science",
            'source': "Academic Journal",
            'publish_date': datetime.utcnow(),
            'content_type': "article",
            'estimated_reading_time': 10,
            'tags': ["computer science", "algorithms"],
            'title': "Advanced Algorithms"
        })()

        analysis = content_processor.analyze_content(
            content, "english", metadata)

        # Verify analysis worked
        assert analysis is not None
        assert analysis.reading_level["level"] in [
            "beginner", "intermediate", "advanced", "expert"]
        assert len(analysis.embedding) > 0
        assert isinstance(analysis.topics, list)
        assert isinstance(analysis.key_phrases, list)

    def test_japanese_content_processing(self, content_processor):
        """Test Japanese content processing works."""
        content = """
        高度なアルゴリズムの実装には、計算複雑性理論の包括的な理解が必要である。
        さらに、性能特性の最適化には、アルゴリズムのトレードオフを慎重に検討する必要がある。
        """

        # Create metadata with title attribute
        metadata = type('MockMetadata', (), {
            'author': "コンピュータサイエンス博士",
            'source': "学術雑誌",
            'publish_date': datetime.utcnow(),
            'content_type': "article",
            'estimated_reading_time': 8,
            'tags': ["コンピュータサイエンス", "アルゴリズム"],
            'title': "高度なアルゴリズム"
        })()

        analysis = content_processor.analyze_content(
            content, "japanese", metadata)

        # Verify analysis worked
        assert analysis is not None
        assert analysis.reading_level["level"] in [
            "beginner", "intermediate", "advanced", "expert"]
        assert "kanji_density" in analysis.reading_level
        assert analysis.reading_level["kanji_density"] > 0
        assert len(analysis.embedding) > 0
        assert isinstance(analysis.topics, list)

    def test_multilingual_embedding_consistency(self, content_processor):
        """Test that both languages produce embeddings of same dimension."""
        english_content = "This is a test sentence in English."
        japanese_content = "これは日本語のテスト文です。"

        # Create simple metadata
        metadata = type('MockMetadata', (), {
            'author': "Test Author",
            'source': "Test",
            'publish_date': datetime.utcnow(),
            'content_type': "test",
            'estimated_reading_time': 1,
            'tags': ["test"],
            'title': "Test Content"
        })()

        english_analysis = content_processor.analyze_content(
            english_content, "english", metadata)
        japanese_analysis = content_processor.analyze_content(
            japanese_content, "japanese", metadata)

        # Both should have embeddings of same dimension
        assert len(english_analysis.embedding) == len(
            japanese_analysis.embedding)
        assert len(english_analysis.embedding) > 0

    def test_user_profile_performance_calculation(self, user_profile_engine):
        """Test user profile performance score calculation."""
        # Test high performance
        high_performance = {
            "completion_rate": 0.95,
            "reading_speed": 280.0,
            "pause_patterns": [],
            "interactions": [{"type": "highlight"}, {"type": "note"}]
        }

        score = user_profile_engine._calculate_performance_score(
            high_performance)
        assert 0.7 <= score <= 1.0

        # Test low performance
        low_performance = {
            "completion_rate": 0.2,
            "reading_speed": 50.0,
            "pause_patterns": [{"duration": 30}] * 10,
            "interactions": []
        }

        score = user_profile_engine._calculate_performance_score(
            low_performance)
        assert 0.0 <= score <= 0.5

    def test_reading_level_update_logic(self, user_profile_engine):
        """Test reading level update calculations."""
        current_data = {
            "level": 8.0,
            "confidence": 0.6,
            "assessment_count": 3
        }

        # Test with good performance on harder content
        new_data = user_profile_engine._update_reading_level(
            current_data, 10.0, 0.85
        )

        assert new_data["level"] > 8.0  # Should increase
        assert new_data["assessment_count"] == 4
        assert "last_assessment" in new_data

        # Test with poor performance
        poor_data = user_profile_engine._update_reading_level(
            current_data, 10.0, 0.3
        )

        assert poor_data["level"] < 8.0  # Should decrease
        assert poor_data["assessment_count"] == 4

    def test_content_processor_edge_cases(self, content_processor):
        """Test content processor handles edge cases."""
        # Create simple metadata
        metadata = type('MockMetadata', (), {
            'author': "Test Author",
            'source': "Test",
            'publish_date': datetime.utcnow(),
            'content_type': "test",
            'estimated_reading_time': 1,
            'tags': ["test"],
            'title': "Test Content"
        })()

        # Test empty content
        empty_analysis = content_processor.analyze_content(
            "", "english", metadata)
        assert empty_analysis is not None
        assert empty_analysis.reading_level["level"] == "beginner"

        # Test very short content
        short_analysis = content_processor.analyze_content(
            "Hi.", "english", metadata)
        assert short_analysis is not None
        assert len(short_analysis.embedding) > 0

        # Test unsupported language
        with pytest.raises(ValueError, match="Unsupported language"):
            content_processor.analyze_content("test", "french", metadata)

    def test_system_integration_workflow(self, content_processor, user_profile_engine):
        """Test a complete workflow integrating multiple systems."""
        # Step 1: Process content
        content = "Machine learning algorithms can analyze large datasets efficiently."
        metadata = type('MockMetadata', (), {
            'author': "AI Researcher",
            'source': "Tech Journal",
            'publish_date': datetime.utcnow(),
            'content_type': "article",
            'estimated_reading_time': 5,
            'tags': ["machine learning", "AI"],
            'title': "ML Algorithms"
        })()

        analysis = content_processor.analyze_content(
            content, "english", metadata)

        # Step 2: Simulate reading performance
        performance_metrics = {
            "completion_rate": 0.8,
            "reading_speed": 250.0,
            "pause_patterns": [{"duration": 5}],
            "interactions": [{"type": "highlight"}]
        }

        # Step 3: Calculate performance score
        performance_score = user_profile_engine._calculate_performance_score(
            performance_metrics)

        # Step 4: Update reading level
        current_level = {
            "level": 8.0,
            "confidence": 0.6,
            "assessment_count": 2
        }

        new_level = user_profile_engine._update_reading_level(
            current_level,
            analysis.reading_level.get("flesch_kincaid", 8.0),
            performance_score
        )

        # Verify the workflow completed successfully
        assert analysis is not None
        assert 0.0 <= performance_score <= 1.0
        assert new_level["assessment_count"] == 3
        assert "last_assessment" in new_level

        print(f"✅ Integration workflow completed successfully:")
        print(
            f"   - Content analyzed: {analysis.reading_level['level']} level")
        print(f"   - Performance score: {performance_score:.2f}")
        print(f"   - Reading level updated: {new_level['level']:.1f}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
