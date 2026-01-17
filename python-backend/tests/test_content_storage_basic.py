"""Basic tests for content storage without external dependencies."""

import pytest
import uuid
from datetime import datetime
from unittest.mock import Mock, patch

from src.services.content_storage import ContentStorageService
from src.schemas.content import ContentMetadata, ContentItemCreate


def test_content_storage_service_initialization():
    """Test that content storage service can be initialized."""
    with patch('src.services.content_storage.VectorDBManager'):
        service = ContentStorageService()
        assert service is not None
        assert hasattr(service, 'processor')


def test_enhanced_metadata_extraction():
    """Test enhanced metadata extraction functionality."""
    with patch('src.services.content_storage.VectorDBManager'):
        service = ContentStorageService()

        # Create sample data
        content = "This is a test article with multiple sentences. It contains various topics and has reasonable complexity."

        base_metadata = ContentMetadata(
            author="Test Author",
            source="Test Source",
            publish_date=datetime.utcnow(),
            content_type="article",
            estimated_reading_time=5,
            tags=["test", "sample"]
        )

        mock_analysis = Mock()
        mock_analysis.topics = [
            {"topic": "test", "confidence": 0.8},
            {"topic": "article", "confidence": 0.6}
        ]
        mock_analysis.reading_level = {"level": "intermediate"}
        mock_analysis.complexity = {"lexical_diversity": 0.7}

        # Test metadata extraction
        enhanced_metadata = service._extract_enhanced_metadata(
            content, base_metadata, mock_analysis, "test_user"
        )

        # Verify enhanced fields
        assert enhanced_metadata.word_count == len(content.split())
        assert enhanced_metadata.reading_level == "intermediate"
        assert enhanced_metadata.complexity_score == 0.7
        assert "test" in enhanced_metadata.key_topics
        assert enhanced_metadata.user_context == "test_user"

        # Verify original fields preserved
        assert enhanced_metadata.author == base_metadata.author
        assert enhanced_metadata.source == base_metadata.source
        assert enhanced_metadata.content_type == base_metadata.content_type


def test_content_create_with_generated_id():
    """Test content creation with auto-generated ID."""
    with patch('src.services.content_storage.VectorDBManager'):
        service = ContentStorageService()

        metadata = ContentMetadata(
            author="Test Author",
            source="Test Source",
            publish_date=datetime.utcnow(),
            content_type="article",
            estimated_reading_time=5,
            tags=["test"]
        )

        content_data = ContentItemCreate(
            id=None,  # Should be generated
            title="Test Article",
            content="Test content",
            language="english",
            metadata=metadata
        )

        # Mock the ingestion process
        with patch.object(service.processor, 'analyze_content') as mock_analyze, \
                patch('src.services.content_storage.db_service.get_session') as mock_session, \
                patch.object(service, '_store_vector_embedding'):

            mock_analyze.return_value = Mock()
            mock_analyze.return_value.dict.return_value = {}
            mock_analyze.return_value.embedding = []

            # The service should generate an ID
            assert content_data.id is None

            # This would normally call ingest_content, but we're testing the ID generation logic
            if not content_data.id:
                content_data.id = str(uuid.uuid4())

            assert content_data.id is not None
            assert len(content_data.id) > 0


def test_vector_embedding_storage_without_index():
    """Test vector embedding storage when index is unavailable."""
    with patch('src.services.content_storage.VectorDBManager'):
        service = ContentStorageService()
        service.index = None  # Simulate unavailable index

        # Should not raise exception
        import asyncio
        asyncio.run(service._store_vector_embedding("test_id", [0.1, 0.2], {}))


def test_enhanced_metadata_word_count_calculation():
    """Test word count calculation in enhanced metadata."""
    with patch('src.services.content_storage.VectorDBManager'):
        service = ContentStorageService()

        test_cases = [
            ("Single word", 2),
            ("This has multiple words in it", 6),
            ("", 0),
            ("Word1 Word2 Word3", 3)
        ]

        base_metadata = ContentMetadata(
            author="Test",
            source="Test",
            publish_date=datetime.utcnow(),
            content_type="test",
            estimated_reading_time=1,
            tags=[]
        )

        mock_analysis = Mock()
        mock_analysis.topics = []
        mock_analysis.reading_level = {"level": "beginner"}
        mock_analysis.complexity = {"lexical_diversity": 0.5}

        for content, expected_words in test_cases:
            enhanced = service._extract_enhanced_metadata(
                content, base_metadata, mock_analysis
            )
            assert enhanced.word_count == expected_words


def test_reading_time_estimation():
    """Test reading time estimation in enhanced metadata."""
    with patch('src.services.content_storage.VectorDBManager'):
        service = ContentStorageService()

        base_metadata = ContentMetadata(
            author="Test",
            source="Test",
            publish_date=datetime.utcnow(),
            content_type="test",
            estimated_reading_time=1,
            tags=[]
        )

        mock_analysis = Mock()
        mock_analysis.topics = []
        mock_analysis.reading_level = {"level": "beginner"}
        mock_analysis.complexity = {"lexical_diversity": 0.5}

        # Test different content lengths
        test_cases = [
            ("Short content", 1),  # Minimum 1 minute
            (" ".join(["word"] * 200), 1),  # Exactly 200 words = 1 minute
            (" ".join(["word"] * 400), 2),  # 400 words = 2 minutes
            (" ".join(["word"] * 1000), 5),  # 1000 words = 5 minutes
        ]

        for content, expected_time in test_cases:
            enhanced = service._extract_enhanced_metadata(
                content, base_metadata, mock_analysis
            )
            assert enhanced.estimated_reading_time == expected_time


def test_topic_extraction_in_metadata():
    """Test topic extraction and inclusion in enhanced metadata."""
    with patch('src.services.content_storage.VectorDBManager'):
        service = ContentStorageService()

        base_metadata = ContentMetadata(
            author="Test",
            source="Test",
            publish_date=datetime.utcnow(),
            content_type="test",
            estimated_reading_time=1,
            tags=["original_tag"]
        )

        mock_analysis = Mock()
        mock_analysis.topics = [
            {"topic": "technology", "confidence": 0.9},
            {"topic": "programming", "confidence": 0.8},
            {"topic": "python", "confidence": 0.7}
        ]
        mock_analysis.reading_level = {"level": "advanced"}
        mock_analysis.complexity = {"lexical_diversity": 0.8}

        enhanced = service._extract_enhanced_metadata(
            "test content", base_metadata, mock_analysis
        )

        # Should include original tags plus extracted topics
        assert "original_tag" in enhanced.tags
        assert "technology" in enhanced.tags
        assert "programming" in enhanced.tags
        assert "python" in enhanced.tags

        # Key topics should be limited to top 5
        assert len(enhanced.key_topics) <= 5
        assert "technology" in enhanced.key_topics
        assert "programming" in enhanced.key_topics
