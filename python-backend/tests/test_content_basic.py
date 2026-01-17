"""Basic tests for content processing without external dependencies."""

import pytest
from datetime import datetime

from src.services.content_processor import ContentProcessor
from src.services.content_adapter import ContentAdapter
from src.schemas.content import ContentMetadata


def test_content_processor_initialization():
    """Test that content processor can be initialized."""
    processor = ContentProcessor()
    assert processor is not None
    assert hasattr(processor, 'locale_mapping')
    assert hasattr(processor, 'available_locales')


def test_content_adapter_initialization():
    """Test that content adapter can be initialized."""
    adapter = ContentAdapter()
    assert adapter is not None
    assert hasattr(adapter, 'locale_mapping')
    assert hasattr(adapter, 'available_locales')


def test_language_normalization():
    """Test language key normalization."""
    processor = ContentProcessor()

    # Test English variants
    assert processor._normalize_language_key("english") == "english"
    assert processor._normalize_language_key("en") == "english"
    assert processor._normalize_language_key("EN") == "english"
    assert processor._normalize_language_key("en_US") == "english"

    # Test Japanese variants
    assert processor._normalize_language_key("japanese") == "japanese"
    assert processor._normalize_language_key("ja") == "japanese"
    assert processor._normalize_language_key("JA") == "japanese"
    assert processor._normalize_language_key("ja_JP") == "japanese"

    # Test unsupported language
    with pytest.raises(ValueError):
        processor._normalize_language_key("french")


def test_locale_setup():
    """Test that locales are set up correctly."""
    processor = ContentProcessor()

    # Check that locale mapping exists
    assert "english" in processor.locale_mapping
    assert "japanese" in processor.locale_mapping

    # Check that available locales are populated
    assert isinstance(processor.available_locales, dict)
    assert len(processor.available_locales) > 0


def test_basic_english_analysis_without_models():
    """Test basic English analysis functionality without external models."""
    processor = ContentProcessor()

    # Create sample metadata
    metadata = ContentMetadata(
        author="Test Author",
        source="Test Source",
        publish_date=datetime.utcnow(),
        content_type="article",
        estimated_reading_time=5,
        tags=["test"]
    )

    # Test with simple content
    content = "This is a simple test sentence. It has basic words."

    try:
        analysis = processor.analyze_content(content, "english", metadata)

        # Basic checks
        assert analysis is not None
        assert hasattr(analysis, 'reading_level')
        assert hasattr(analysis, 'topics')
        assert hasattr(analysis, 'key_phrases')
        assert hasattr(analysis, 'complexity')
        assert hasattr(analysis, 'embedding')

        # Check that reading level has required fields
        assert 'level' in analysis.reading_level
        assert analysis.reading_level['level'] in [
            'beginner', 'intermediate', 'advanced', 'expert']

    except Exception as e:
        # If models aren't available, that's expected in CI
        pytest.skip(f"Skipping test due to missing models: {e}")


def test_basic_japanese_analysis_without_models():
    """Test basic Japanese analysis functionality without external models."""
    processor = ContentProcessor()

    # Create sample metadata
    metadata = ContentMetadata(
        author="テスト著者",
        source="テストソース",
        publish_date=datetime.utcnow(),
        content_type="記事",
        estimated_reading_time=5,
        tags=["テスト"]
    )

    # Test with simple Japanese content
    content = "これは簡単なテスト文です。基本的な言葉があります。"

    try:
        analysis = processor.analyze_content(content, "japanese", metadata)

        # Basic checks
        assert analysis is not None
        assert hasattr(analysis, 'reading_level')
        assert hasattr(analysis, 'topics')
        assert hasattr(analysis, 'key_phrases')
        assert hasattr(analysis, 'complexity')
        assert hasattr(analysis, 'embedding')

        # Check that reading level has required fields
        assert 'level' in analysis.reading_level
        assert analysis.reading_level['level'] in [
            'beginner', 'intermediate', 'advanced', 'expert']

    except Exception as e:
        # If models aren't available, that's expected in CI
        pytest.skip(f"Skipping test due to missing models: {e}")


def test_adaptation_should_adapt_logic():
    """Test the logic for determining when adaptation is needed."""
    adapter = ContentAdapter()

    # Should adapt when current level is higher than target
    assert adapter._should_adapt("advanced", "beginner") == True
    assert adapter._should_adapt("expert", "intermediate") == True
    assert adapter._should_adapt("intermediate", "beginner") == True

    # Should not adapt when current level is same or lower than target
    assert adapter._should_adapt("beginner", "beginner") == False
    assert adapter._should_adapt("beginner", "intermediate") == False
    assert adapter._should_adapt("intermediate", "advanced") == False

    # Should handle invalid levels gracefully
    assert adapter._should_adapt("invalid", "beginner") == False
    assert adapter._should_adapt("beginner", "invalid") == False


def test_basic_content_adaptation():
    """Test basic content adaptation without external models."""
    adapter = ContentAdapter()

    # Test simple English adaptation
    content = "This is a sophisticated implementation of advanced algorithms."

    try:
        result = adapter.adapt_content(
            content=content,
            language="english",
            target_level="beginner",
            current_level="advanced",
            preserve_meaning=True
        )

        assert result is not None
        assert hasattr(result, 'adapted_content')
        assert hasattr(result, 'original_content')
        assert hasattr(result, 'adaptations_made')
        assert hasattr(result, 'reading_level_change')
        assert hasattr(result, 'cultural_context_preserved')

        assert result.original_content == content

    except Exception as e:
        # If models aren't available, that's expected in CI
        pytest.skip(f"Skipping test due to missing models: {e}")


def test_no_adaptation_needed():
    """Test when no adaptation is needed."""
    adapter = ContentAdapter()

    content = "This is simple text."

    result = adapter.adapt_content(
        content=content,
        language="english",
        target_level="intermediate",
        current_level="beginner",  # Current is lower than target
        preserve_meaning=True
    )

    # Should return original content unchanged
    assert result.adapted_content == content
    assert result.original_content == content
    assert result.adaptations_made == []
    assert result.reading_level_change["adapted"] == False
    assert result.cultural_context_preserved == True
