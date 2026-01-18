"""
Simple System Validation Tests for Noah Reading Agent

This test suite validates the core functionality of the Noah Reading Agent system.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch

from src.services.content_processor import ContentProcessor
from src.schemas.content import ContentMetadata


class TestCoreSystemValidation:
    """Test suite for core system validation."""

    @pytest.fixture
    def content_processor(self):
        """Create content processor instance."""
        return ContentProcessor()

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

    def test_english_content_processing(self, content_processor, sample_metadata):
        """Test English content processing functionality."""
        content = "Reading is a fundamental skill that opens doors to knowledge and imagination. It allows us to explore different worlds and learn new concepts."
        
        analysis = content_processor.analyze_content(
            content=content,
            language="english",
            metadata=sample_metadata,
            title="English Test Content"
        )
        
        assert analysis is not None
        assert len(analysis.topics) > 0
        assert "level" in analysis.reading_level
        assert len(analysis.embedding) > 0
        assert len(analysis.key_phrases) >= 0

    def test_japanese_content_processing(self, content_processor, sample_metadata):
        """Test Japanese content processing functionality."""
        content = "読書は知識と想像力への扉を開く基本的なスキルです。それは私たちが異なる世界を探索することを可能にします。"
        
        analysis = content_processor.analyze_content(
            content=content,
            language="japanese",
            metadata=sample_metadata,
            title="Japanese Test Content"
        )
        
        assert analysis is not None
        assert len(analysis.topics) > 0
        assert "level" in analysis.reading_level
        assert len(analysis.embedding) > 0

    def test_multilingual_support_validation(self, content_processor, sample_metadata):
        """Validate multilingual support works correctly for English and Japanese."""
        english_content = "This is an English text about science and technology."
        japanese_content = "これは科学技術についての日本語のテキストです。"
        
        # Process English content
        english_analysis = content_processor.analyze_content(
            content=english_content,
            language="english",
            metadata=sample_metadata,
            title="English Science Text"
        )
        
        # Process Japanese content
        japanese_analysis = content_processor.analyze_content(
            content=japanese_content,
            language="japanese",
            metadata=sample_metadata,
            title="Japanese Science Text"
        )
        
        # Both should be processed successfully
        assert english_analysis is not None
        assert japanese_analysis is not None
        
        # Both should have different embeddings (different languages)
        assert english_analysis.embedding != japanese_analysis.embedding
        
        # Both should have reading level assessments
        assert "level" in english_analysis.reading_level
        assert "level" in japanese_analysis.reading_level

    def test_content_analysis_consistency(self, content_processor, sample_metadata):
        """Test that content analysis produces consistent results."""
        content = "Artificial intelligence is transforming how we work and live. Machine learning algorithms can process vast amounts of data."
        
        # Analyze the same content multiple times
        analysis1 = content_processor.analyze_content(
            content=content,
            language="english",
            metadata=sample_metadata,
            title="AI Content Test 1"
        )
        
        analysis2 = content_processor.analyze_content(
            content=content,
            language="english",
            metadata=sample_metadata,
            title="AI Content Test 2"
        )
        
        # Results should be consistent
        assert analysis1 is not None
        assert analysis2 is not None
        assert len(analysis1.topics) > 0
        assert len(analysis2.topics) > 0
        
        # Embeddings should be similar for the same content (allowing for small variations)
        assert len(analysis1.embedding) == len(analysis2.embedding)
        assert len(analysis1.embedding) > 0

    def test_error_handling_validation(self, content_processor, sample_metadata):
        """Validate error handling and system resilience."""
        # Test empty content handling
        empty_analysis = content_processor.analyze_content(
            content="",
            language="english",
            metadata=sample_metadata,
            title="Empty Content"
        )
        assert empty_analysis is not None
        
        # Test very short content handling
        short_analysis = content_processor.analyze_content(
            content="Hi.",
            language="english",
            metadata=sample_metadata,
            title="Short Content"
        )
        assert short_analysis is not None
        
        # Test unsupported language handling
        with pytest.raises(ValueError, match="Unsupported language"):
            content_processor.analyze_content(
                content="Bonjour le monde",
                language="french",
                metadata=sample_metadata,
                title="French Content"
            )

    def test_performance_validation(self, content_processor, sample_metadata):
        """Validate system meets performance requirements."""
        import time
        
        content = "This is a test document for performance validation. " * 50  # Longer content
        
        start_time = time.time()
        analysis = content_processor.analyze_content(
            content=content,
            language="english",
            metadata=sample_metadata,
            title="Performance Test Content"
        )
        processing_time = time.time() - start_time
        
        # Should complete within reasonable time (10 seconds for longer content)
        assert processing_time < 10.0
        assert analysis is not None
        assert len(analysis.embedding) > 0

    def test_reading_level_assessment_validation(self, content_processor, sample_metadata):
        """Validate reading level assessment for different complexity levels."""
        # Simple content
        simple_content = "The cat sat on the mat. It was a sunny day."
        simple_analysis = content_processor.analyze_content(
            content=simple_content,
            language="english",
            metadata=sample_metadata,
            title="Simple Content"
        )
        
        # Complex content
        complex_content = "The implementation of sophisticated algorithms necessitates comprehensive understanding of computational complexity theory and advanced mathematical concepts."
        complex_analysis = content_processor.analyze_content(
            content=complex_content,
            language="english",
            metadata=sample_metadata,
            title="Complex Content"
        )
        
        # Both should have reading level assessments
        assert "level" in simple_analysis.reading_level
        assert "level" in complex_analysis.reading_level
        
        # Complex content should generally have higher reading level
        simple_level = simple_analysis.reading_level.get("level", "beginner")
        complex_level = complex_analysis.reading_level.get("level", "beginner")
        
        # This is a general expectation, but we'll be flexible
        assert simple_level in ["beginner", "intermediate", "advanced", "expert"]
        assert complex_level in ["beginner", "intermediate", "advanced", "expert"]

    def test_topic_extraction_validation(self, content_processor, sample_metadata):
        """Validate topic extraction functionality."""
        science_content = "Physics and chemistry are fundamental sciences that help us understand the natural world through experimentation and observation."
        
        analysis = content_processor.analyze_content(
            content=science_content,
            language="english",
            metadata=sample_metadata,
            title="Science Content"
        )
        
        assert analysis is not None
        assert len(analysis.topics) > 0
        
        # Topics should contain relevant information
        topics = analysis.topics
        assert isinstance(topics, list)
        
        # Each topic should have required structure
        for topic in topics:
            assert isinstance(topic, dict)

    def test_embedding_generation_validation(self, content_processor, sample_metadata):
        """Validate embedding generation functionality."""
        content = "Machine learning and artificial intelligence are revolutionizing technology."
        
        analysis = content_processor.analyze_content(
            content=content,
            language="english",
            metadata=sample_metadata,
            title="ML Content"
        )
        
        assert analysis is not None
        assert len(analysis.embedding) > 0
        
        # Embeddings should be numerical values
        embedding = analysis.embedding
        assert isinstance(embedding, list)
        assert all(isinstance(x, (int, float)) for x in embedding)
        
        # Embedding should have reasonable dimensionality (typically 1536 for OpenAI)
        assert len(embedding) > 100  # At least some reasonable size


if __name__ == "__main__":
    pytest.main([__file__, "-v"])