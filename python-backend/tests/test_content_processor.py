"""Tests for content processor functionality."""

import pytest
from datetime import datetime

from src.services.content_processor import ContentProcessor
from src.schemas.content import ContentMetadata


@pytest.fixture
def content_processor():
    """Create a content processor instance for testing."""
    return ContentProcessor()


@pytest.fixture
def sample_metadata():
    """Create sample content metadata."""
    return ContentMetadata(
        author="Test Author",
        source="Test Source",
        publish_date=datetime.utcnow(),
        content_type="article",
        estimated_reading_time=5,
        tags=["test", "sample"]
    )


class TestEnglishContentProcessing:
    """Test English content processing functionality."""

    def test_analyze_simple_english_content(self, content_processor, sample_metadata):
        """Test analysis of simple English content."""
        content = "This is a simple test. It has two sentences."

        analysis = content_processor.analyze_content(
            content, "english", sample_metadata)

        assert analysis is not None
        assert "level" in analysis.reading_level
        assert analysis.reading_level["level"] in [
            "beginner", "intermediate", "advanced", "expert"]
        assert len(analysis.embedding) > 0
        assert isinstance(analysis.topics, list)
        assert isinstance(analysis.key_phrases, list)

    def test_analyze_complex_english_content(self, content_processor, sample_metadata):
        """Test analysis of complex English content."""
        content = """
        The implementation of sophisticated algorithms requires comprehensive understanding 
        of computational complexity theory. Furthermore, the optimization of performance 
        characteristics necessitates careful consideration of algorithmic trade-offs.
        """

        analysis = content_processor.analyze_content(
            content, "english", sample_metadata)

        assert analysis is not None
        assert analysis.reading_level["level"] in ["advanced", "expert"]
        assert analysis.complexity["lexical_diversity"] > 0
        assert analysis.complexity["complex_word_ratio"] > 0

    def test_english_readability_metrics(self, content_processor):
        """Test English readability metric calculations."""
        content = "The cat sat on the mat. It was a sunny day."
        word_count = 10
        sentence_count = 2

        metrics = content_processor._calculate_english_readability(
            content, word_count, sentence_count)

        assert "flesch_kincaid" in metrics
        assert "smog" in metrics
        assert "coleman_liau" in metrics
        assert "level" in metrics
        assert metrics["level"] in ["beginner",
                                    "intermediate", "advanced", "expert"]

    def test_english_topic_extraction(self, content_processor):
        """Test English topic extraction."""
        content = "Python programming is essential for data science and machine learning applications."

        topics = content_processor._extract_english_topics(content)

        assert isinstance(topics, list)
        # Should extract some topics even with simple content
        if topics:
            assert all(
                "topic" in topic and "confidence" in topic for topic in topics)


class TestJapaneseContentProcessing:
    """Test Japanese content processing functionality."""

    def test_analyze_simple_japanese_content(self, content_processor, sample_metadata):
        """Test analysis of simple Japanese content."""
        content = "これは簡単なテストです。二つの文があります。"

        analysis = content_processor.analyze_content(
            content, "japanese", sample_metadata)

        assert analysis is not None
        assert "level" in analysis.reading_level
        assert analysis.reading_level["level"] in [
            "beginner", "intermediate", "advanced", "expert"]
        assert len(analysis.embedding) > 0
        assert isinstance(analysis.topics, list)
        assert isinstance(analysis.key_phrases, list)

    def test_analyze_complex_japanese_content(self, content_processor, sample_metadata):
        """Test analysis of complex Japanese content."""
        content = """
        高度なアルゴリズムの実装には、計算複雑性理論の包括的な理解が必要である。
        さらに、性能特性の最適化には、アルゴリズムのトレードオフを慎重に検討する必要がある。
        """

        analysis = content_processor.analyze_content(
            content, "japanese", sample_metadata)

        assert analysis is not None
        # Complex Japanese content should have higher reading level
        assert analysis.reading_level["kanji_density"] > 0
        assert analysis.reading_level["level"] in [
            "intermediate", "advanced", "expert"]

    def test_japanese_readability_metrics(self, content_processor):
        """Test Japanese readability metric calculations."""
        content = "猫が座っています。今日は晴れです。"
        word_count = 8
        sentence_count = 2

        metrics = content_processor._calculate_japanese_readability(
            content, word_count, sentence_count)

        assert "kanji_density" in metrics
        assert "kanji_count" in metrics
        assert "hiragana_count" in metrics
        assert "katakana_count" in metrics
        assert "level" in metrics
        assert metrics["level"] in ["beginner",
                                    "intermediate", "advanced", "expert"]

    def test_japanese_sentence_splitting(self, content_processor):
        """Test Japanese sentence splitting."""
        content = "これは最初の文です。これは二番目の文です！これは三番目の文ですか？"

        sentences = content_processor._split_japanese_sentences(content)

        assert len(sentences) == 3
        assert all(sentence.strip() for sentence in sentences)


class TestContentProcessorUtilities:
    """Test utility functions of content processor."""

    def test_syllable_counting_english(self, content_processor):
        """Test English syllable counting."""
        # Simple test cases
        syllables = content_processor._count_syllables_english("hello world")
        assert syllables > 0

        syllables = content_processor._count_syllables_english("cat")
        assert syllables >= 1

    def test_complex_word_counting_english(self, content_processor):
        """Test English complex word counting."""
        complex_count = content_processor._count_complex_words_english(
            "sophisticated implementation")
        assert complex_count >= 1  # Both words should be considered complex

        complex_count = content_processor._count_complex_words_english(
            "cat dog")
        assert complex_count == 0  # Simple words

    def test_embedding_generation(self, content_processor):
        """Test embedding generation."""
        content = "This is a test sentence for embedding generation."

        embedding = content_processor._generate_embedding(content)

        assert isinstance(embedding, list)
        assert len(embedding) > 0
        assert all(isinstance(x, float) for x in embedding)

    def test_unsupported_language(self, content_processor, sample_metadata):
        """Test handling of unsupported language."""
        with pytest.raises(ValueError, match="Unsupported language"):
            content_processor.analyze_content(
                "test", "french", sample_metadata)


class TestContentProcessorEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_content(self, content_processor, sample_metadata):
        """Test handling of empty content."""
        analysis = content_processor.analyze_content(
            "", "english", sample_metadata)

        assert analysis is not None
        # Empty content should be beginner level
        assert analysis.reading_level["level"] == "beginner"

    def test_very_short_content(self, content_processor, sample_metadata):
        """Test handling of very short content."""
        analysis = content_processor.analyze_content(
            "Hi.", "english", sample_metadata)

        assert analysis is not None
        assert len(analysis.embedding) > 0

    def test_content_with_special_characters(self, content_processor, sample_metadata):
        """Test handling of content with special characters."""
        content = "Hello! @#$%^&*() This has special characters... 123456"

        analysis = content_processor.analyze_content(
            content, "english", sample_metadata)

        assert analysis is not None
        assert analysis.reading_level["level"] in [
            "beginner", "intermediate", "advanced", "expert"]
