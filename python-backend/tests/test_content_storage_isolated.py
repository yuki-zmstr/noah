"""Isolated tests for content storage functionality without external dependencies."""

from src.schemas.content import ContentMetadata
import pytest
import sys
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import uuid


# Mock external dependencies before importing
sys.modules['pinecone'] = MagicMock()
sys.modules['src.vector_db_init'] = MagicMock()

# Now we can import our modules


class MockContentStorageService:
    """Mock content storage service for testing core logic."""

    def __init__(self):
        self.processor = Mock()
        self.index = Mock()

    def _extract_enhanced_metadata(self, content: str, base_metadata: ContentMetadata,
                                   analysis: Mock, user_id: str = None) -> ContentMetadata:
        """Extract enhanced metadata from content and analysis."""
        # Calculate additional metadata
        word_count = len(content.split())
        estimated_reading_time = max(
            1, word_count // 200)  # 200 words per minute

        # Extract topics from analysis
        topic_tags = [topic["topic"] for topic in analysis.topics[:10]]

        # Combine with existing tags
        all_tags = list(set(base_metadata.tags + topic_tags))

        # Create enhanced metadata
        enhanced_metadata = ContentMetadata(
            author=base_metadata.author,
            source=base_metadata.source,
            publish_date=base_metadata.publish_date,
            content_type=base_metadata.content_type,
            estimated_reading_time=estimated_reading_time,
            tags=all_tags,
            # Additional fields
            word_count=word_count,
            reading_level=analysis.reading_level.get("level", "intermediate"),
            complexity_score=analysis.complexity.get("lexical_diversity", 0.0),
            key_topics=topic_tags[:5],
            language_specific_metrics=analysis.reading_level,
            ingestion_timestamp=datetime.utcnow().isoformat(),
            user_context=user_id
        )

        return enhanced_metadata


class TestContentStorageCore:
    """Test core content storage functionality."""

    @pytest.fixture
    def mock_service(self):
        """Create a mock content storage service."""
        return MockContentStorageService()

    @pytest.fixture
    def sample_metadata(self):
        """Create sample content metadata."""
        return ContentMetadata(
            author="Test Author",
            source="Test Source",
            publish_date=datetime.utcnow(),
            content_type="article",
            estimated_reading_time=5,
            tags=["test", "sample"]
        )

    def test_enhanced_metadata_extraction_basic(self, mock_service, sample_metadata):
        """Test basic enhanced metadata extraction."""
        content = "This is a test article with multiple sentences. It contains various topics."

        mock_analysis = Mock()
        mock_analysis.topics = [
            {"topic": "test", "confidence": 0.8},
            {"topic": "article", "confidence": 0.6}
        ]
        mock_analysis.reading_level = {"level": "intermediate"}
        mock_analysis.complexity = {"lexical_diversity": 0.7}

        enhanced_metadata = mock_service._extract_enhanced_metadata(
            content, sample_metadata, mock_analysis, "test_user"
        )

        # Verify enhanced fields
        assert enhanced_metadata.word_count == len(content.split())
        assert enhanced_metadata.reading_level == "intermediate"
        assert enhanced_metadata.complexity_score == 0.7
        assert "test" in enhanced_metadata.key_topics
        assert enhanced_metadata.user_context == "test_user"

        # Verify original fields preserved
        assert enhanced_metadata.author == sample_metadata.author
        assert enhanced_metadata.source == sample_metadata.source

    def test_word_count_calculation(self, mock_service, sample_metadata):
        """Test word count calculation accuracy."""
        test_cases = [
            ("Single word", 2),
            ("This has multiple words in it", 6),
            ("Word1 Word2 Word3", 3),
            ("", 0)
        ]

        mock_analysis = Mock()
        mock_analysis.topics = []
        mock_analysis.reading_level = {"level": "beginner"}
        mock_analysis.complexity = {"lexical_diversity": 0.5}

        for content, expected_words in test_cases:
            enhanced = mock_service._extract_enhanced_metadata(
                content, sample_metadata, mock_analysis
            )
            assert enhanced.word_count == expected_words

    def test_reading_time_estimation(self, mock_service, sample_metadata):
        """Test reading time estimation logic."""
        mock_analysis = Mock()
        mock_analysis.topics = []
        mock_analysis.reading_level = {"level": "beginner"}
        mock_analysis.complexity = {"lexical_diversity": 0.5}

        test_cases = [
            ("Short content", 1),  # Minimum 1 minute
            (" ".join(["word"] * 200), 1),  # Exactly 200 words = 1 minute
            (" ".join(["word"] * 400), 2),  # 400 words = 2 minutes
            (" ".join(["word"] * 1000), 5),  # 1000 words = 5 minutes
        ]

        for content, expected_time in test_cases:
            enhanced = mock_service._extract_enhanced_metadata(
                content, sample_metadata, mock_analysis
            )
            assert enhanced.estimated_reading_time == expected_time

    def test_topic_integration(self, mock_service, sample_metadata):
        """Test topic extraction and tag integration."""
        mock_analysis = Mock()
        mock_analysis.topics = [
            {"topic": "technology", "confidence": 0.9},
            {"topic": "programming", "confidence": 0.8},
            {"topic": "python", "confidence": 0.7}
        ]
        mock_analysis.reading_level = {"level": "advanced"}
        mock_analysis.complexity = {"lexical_diversity": 0.8}

        enhanced = mock_service._extract_enhanced_metadata(
            "test content", sample_metadata, mock_analysis
        )

        # Should include original tags plus extracted topics
        assert "test" in enhanced.tags  # Original tag
        assert "sample" in enhanced.tags  # Original tag
        assert "technology" in enhanced.tags  # Extracted topic
        assert "programming" in enhanced.tags  # Extracted topic

        # Key topics should be limited to top 5
        assert len(enhanced.key_topics) <= 5
        assert "technology" in enhanced.key_topics

    def test_complexity_score_extraction(self, mock_service, sample_metadata):
        """Test complexity score extraction from analysis."""
        mock_analysis = Mock()
        mock_analysis.topics = []
        mock_analysis.reading_level = {"level": "expert"}
        mock_analysis.complexity = {"lexical_diversity": 0.95}

        enhanced = mock_service._extract_enhanced_metadata(
            "complex content", sample_metadata, mock_analysis
        )

        assert enhanced.complexity_score == 0.95
        assert enhanced.reading_level == "expert"

    def test_user_context_preservation(self, mock_service, sample_metadata):
        """Test user context preservation in metadata."""
        mock_analysis = Mock()
        mock_analysis.topics = []
        mock_analysis.reading_level = {"level": "intermediate"}
        mock_analysis.complexity = {"lexical_diversity": 0.5}

        # Test with user context
        enhanced_with_user = mock_service._extract_enhanced_metadata(
            "test content", sample_metadata, mock_analysis, "user123"
        )
        assert enhanced_with_user.user_context == "user123"

        # Test without user context
        enhanced_without_user = mock_service._extract_enhanced_metadata(
            "test content", sample_metadata, mock_analysis, None
        )
        assert enhanced_without_user.user_context is None

    def test_timestamp_generation(self, mock_service, sample_metadata):
        """Test that ingestion timestamp is generated."""
        mock_analysis = Mock()
        mock_analysis.topics = []
        mock_analysis.reading_level = {"level": "intermediate"}
        mock_analysis.complexity = {"lexical_diversity": 0.5}

        enhanced = mock_service._extract_enhanced_metadata(
            "test content", sample_metadata, mock_analysis
        )

        assert enhanced.ingestion_timestamp is not None
        assert isinstance(enhanced.ingestion_timestamp, str)

        # Should be a valid ISO format timestamp
        from datetime import datetime
        parsed_time = datetime.fromisoformat(
            enhanced.ingestion_timestamp.replace('Z', '+00:00'))
        assert isinstance(parsed_time, datetime)

    def test_language_specific_metrics_preservation(self, mock_service, sample_metadata):
        """Test that language-specific metrics are preserved."""
        mock_analysis = Mock()
        mock_analysis.topics = []
        mock_analysis.reading_level = {
            "level": "intermediate",
            "flesch_kincaid": 8.5,
            "smog": 9.2,
            "kanji_density": 0.3  # For Japanese content
        }
        mock_analysis.complexity = {"lexical_diversity": 0.6}

        enhanced = mock_service._extract_enhanced_metadata(
            "test content", sample_metadata, mock_analysis
        )

        assert enhanced.language_specific_metrics == mock_analysis.reading_level
        assert enhanced.language_specific_metrics["flesch_kincaid"] == 8.5
        assert enhanced.language_specific_metrics["kanji_density"] == 0.3

    def test_empty_content_handling(self, mock_service, sample_metadata):
        """Test handling of empty or minimal content."""
        mock_analysis = Mock()
        mock_analysis.topics = []
        mock_analysis.reading_level = {"level": "beginner"}
        mock_analysis.complexity = {"lexical_diversity": 0.0}

        # Test empty content
        enhanced_empty = mock_service._extract_enhanced_metadata(
            "", sample_metadata, mock_analysis
        )
        assert enhanced_empty.word_count == 0
        assert enhanced_empty.estimated_reading_time == 1  # Minimum 1 minute

        # Test single word
        enhanced_single = mock_service._extract_enhanced_metadata(
            "word", sample_metadata, mock_analysis
        )
        assert enhanced_single.word_count == 1
        assert enhanced_single.estimated_reading_time == 1

    def test_large_topic_list_truncation(self, mock_service, sample_metadata):
        """Test that large topic lists are properly truncated."""
        # Create many topics
        many_topics = [
            {"topic": f"topic_{i}", "confidence": 0.8 - (i * 0.05)}
            for i in range(20)  # 20 topics
        ]

        mock_analysis = Mock()
        mock_analysis.topics = many_topics
        mock_analysis.reading_level = {"level": "intermediate"}
        mock_analysis.complexity = {"lexical_diversity": 0.5}

        enhanced = mock_service._extract_enhanced_metadata(
            "content with many topics", sample_metadata, mock_analysis
        )

        # Should include original tags plus up to 10 topic tags
        assert len(
            [tag for tag in enhanced.tags if tag.startswith("topic_")]) <= 10

        # Key topics should be limited to 5
        assert len(enhanced.key_topics) <= 5

        # Should include highest confidence topics first
        assert "topic_0" in enhanced.key_topics  # Highest confidence
        assert "topic_1" in enhanced.key_topics  # Second highest
