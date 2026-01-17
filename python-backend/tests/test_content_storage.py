"""Tests for content storage service functionality."""

import pytest
import uuid
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock

from src.services.content_storage import ContentStorageService
from src.schemas.content import (
    ContentItemCreate, ContentMetadata, SavedContentRequest,
    ContentSearchRequest, ContentIngestionRequest
)
from src.models.content import ContentItem
from src.models.user_profile import UserProfile, ReadingBehavior


@pytest.fixture
def content_storage_service():
    """Create a content storage service instance for testing."""
    service = ContentStorageService()
    # Mock the vector index to avoid Pinecone dependency in tests
    service.index = Mock()
    return service


@pytest.fixture
def sample_content_metadata():
    """Create sample content metadata."""
    return ContentMetadata(
        author="Test Author",
        source="Test Source",
        publish_date=datetime.utcnow(),
        content_type="article",
        estimated_reading_time=5,
        tags=["test", "sample"]
    )


@pytest.fixture
def sample_content_create(sample_content_metadata):
    """Create sample content creation data."""
    return ContentItemCreate(
        id=str(uuid.uuid4()),
        title="Test Article",
        content="This is a test article with some content for analysis.",
        language="english",
        metadata=sample_content_metadata
    )


class TestContentIngestion:
    """Test content ingestion functionality."""

    @patch('src.services.content_storage.db_service.get_session')
    async def test_ingest_content_success(self, mock_get_session, content_storage_service, sample_content_create):
        """Test successful content ingestion."""
        # Mock database session
        mock_session = Mock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_get_session.return_value.__exit__.return_value = None

        # Mock content processor
        mock_analysis = Mock()
        mock_analysis.dict.return_value = {
            "topics": [{"topic": "test", "confidence": 0.8}],
            "reading_level": {"level": "intermediate"},
            "complexity": {"lexical_diversity": 0.5},
            "embedding": [0.1, 0.2, 0.3],
            "key_phrases": ["test phrase"]
        }
        mock_analysis.embedding = [0.1, 0.2, 0.3]
        mock_analysis.topics = [{"topic": "test", "confidence": 0.8}]
        mock_analysis.reading_level = {"level": "intermediate"}

        with patch.object(content_storage_service.processor, 'analyze_content', return_value=mock_analysis):
            result = await content_storage_service.ingest_content(sample_content_create, "test_user")

            # Verify content was processed
            assert result is not None
            mock_session.add.assert_called_once()
            mock_session.commit.assert_called_once()

    async def test_ingest_content_generates_id_if_missing(self, content_storage_service, sample_content_create):
        """Test that content ID is generated if not provided."""
        sample_content_create.id = None

        with patch('src.services.content_storage.db_service.get_session'), \
                patch.object(content_storage_service.processor, 'analyze_content'), \
                patch.object(content_storage_service, '_store_vector_embedding'):

            result = await content_storage_service.ingest_content(sample_content_create)

            # Should have generated an ID
            assert sample_content_create.id is not None
            assert len(sample_content_create.id) > 0

    async def test_enhanced_metadata_extraction(self, content_storage_service, sample_content_metadata):
        """Test enhanced metadata extraction."""
        content = "This is a test article with multiple sentences. It has various topics and complexity."

        mock_analysis = Mock()
        mock_analysis.topics = [
            {"topic": "test", "confidence": 0.8},
            {"topic": "article", "confidence": 0.6}
        ]
        mock_analysis.reading_level = {"level": "intermediate"}
        mock_analysis.complexity = {"lexical_diversity": 0.7}

        enhanced_metadata = content_storage_service._extract_enhanced_metadata(
            content, sample_content_metadata, mock_analysis, "test_user"
        )

        assert enhanced_metadata.word_count == len(content.split())
        assert enhanced_metadata.reading_level == "intermediate"
        assert enhanced_metadata.complexity_score == 0.7
        assert "test" in enhanced_metadata.key_topics
        assert enhanced_metadata.user_context == "test_user"


class TestSavedContent:
    """Test saved content functionality."""

    @patch('src.services.content_storage.db_service.get_session')
    async def test_save_content_for_user_new_record(self, mock_get_session, content_storage_service):
        """Test saving content for user with new record."""
        # Mock database session and objects
        mock_session = Mock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_get_session.return_value.__exit__.return_value = None

        mock_content = Mock()
        mock_content.title = "Test Content"
        mock_content.language = "english"
        # content exists, user exists
        mock_session.get.side_effect = [mock_content, Mock()]
        # no existing behavior
        mock_session.query.return_value.filter.return_value.first.return_value = None

        request = SavedContentRequest(
            content_id="test_content_id",
            user_id="test_user_id",
            user_rating=4,
            user_notes="Great article!",
            tags=["interesting", "useful"],
            save_reason="bookmark"
        )

        result = await content_storage_service.save_content_for_user(request)

        assert result.content_id == "test_content_id"
        assert result.user_id == "test_user_id"
        assert result.user_rating == 4
        assert result.user_notes == "Great article!"
        assert "interesting" in result.tags
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    @patch('src.services.content_storage.db_service.get_session')
    async def test_save_content_for_user_update_existing(self, mock_get_session, content_storage_service):
        """Test updating existing saved content."""
        # Mock database session and objects
        mock_session = Mock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_get_session.return_value.__exit__.return_value = None

        mock_content = Mock()
        mock_content.title = "Test Content"
        mock_content.language = "english"

        mock_existing_behavior = Mock()
        mock_existing_behavior.interactions = [
            {"action": "viewed", "timestamp": "2023-01-01"}]

        # content exists, user exists
        mock_session.get.side_effect = [mock_content, Mock()]
        mock_session.query.return_value.filter.return_value.first.return_value = mock_existing_behavior

        request = SavedContentRequest(
            content_id="test_content_id",
            user_id="test_user_id",
            user_rating=5,
            user_notes="Updated notes",
            tags=["updated"],
            save_reason="reference"
        )

        result = await content_storage_service.save_content_for_user(request)

        assert result.user_rating == 5
        assert result.user_notes == "Updated notes"
        # Original + new save action
        assert len(mock_existing_behavior.interactions) == 2
        mock_session.commit.assert_called_once()

    @patch('src.services.content_storage.db_service.get_session')
    async def test_save_content_content_not_found(self, mock_get_session, content_storage_service):
        """Test error when content doesn't exist."""
        mock_session = Mock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_get_session.return_value.__exit__.return_value = None
        mock_session.get.return_value = None  # Content not found

        request = SavedContentRequest(
            content_id="nonexistent_content",
            user_id="test_user_id"
        )

        with pytest.raises(ValueError, match="Content nonexistent_content not found"):
            await content_storage_service.save_content_for_user(request)


class TestContentSearch:
    """Test content search functionality."""

    async def test_vector_similarity_search_success(self, content_storage_service):
        """Test successful vector similarity search."""
        # Mock vector search results
        mock_match = Mock()
        mock_match.id = "content_1"
        mock_match.score = 0.85
        mock_match.metadata = {"title": "Test Content"}

        mock_search_results = Mock()
        mock_search_results.matches = [mock_match]

        content_storage_service.index.query.return_value = mock_search_results

        # Mock database query
        with patch('src.services.content_storage.db_service.get_session') as mock_get_session:
            mock_session = Mock()
            mock_get_session.return_value.__enter__.return_value = mock_session
            mock_get_session.return_value.__exit__.return_value = None

            mock_content = Mock()
            mock_content.id = "content_1"
            mock_content.title = "Test Content"
            mock_session.query.return_value.filter.return_value.all.return_value = [
                mock_content]

            request = ContentSearchRequest(
                query_text="test query",
                language="english",
                limit=10
            )

            with patch('src.schemas.content.ContentItemResponse.from_orm') as mock_from_orm:
                mock_from_orm.return_value = Mock()

                result = await content_storage_service.search_content_by_similarity(request)

                assert result.query_text == "test query"
                assert len(result.results) == 1
                assert result.results[0]["similarity_score"] == 0.85
                assert result.search_method == "vector_similarity"

    async def test_fallback_text_search(self, content_storage_service):
        """Test fallback to text-based search when vector search fails."""
        # Disable vector index
        content_storage_service.index = None

        with patch('src.services.content_storage.db_service.get_session') as mock_get_session:
            mock_session = Mock()
            mock_get_session.return_value.__enter__.return_value = mock_session
            mock_get_session.return_value.__exit__.return_value = None

            mock_content = Mock()
            mock_session.query.return_value.filter.return_value.filter.return_value.limit.return_value.all.return_value = [
                mock_content]

            request = ContentSearchRequest(
                query_text="test query",
                language="english"
            )

            with patch('src.schemas.content.ContentItemResponse.from_orm') as mock_from_orm:
                mock_from_orm.return_value = Mock()

                result = await content_storage_service.search_content_by_similarity(request)

                assert result.search_method == "text_based_fallback"

    async def test_search_with_filters(self, content_storage_service):
        """Test search with language and reading level filters."""
        mock_search_results = Mock()
        mock_search_results.matches = []
        content_storage_service.index.query.return_value = mock_search_results

        with patch('src.services.content_storage.db_service.get_session'):
            request = ContentSearchRequest(
                query_text="test query",
                language="japanese",
                reading_level="beginner",
                user_id="test_user"
            )

            result = await content_storage_service.search_content_by_similarity(request)

            # Verify filters were applied to vector search
            content_storage_service.index.query.assert_called_once()
            call_args = content_storage_service.index.query.call_args
            assert call_args[1]['filter']['language'] == 'japanese'
            assert call_args[1]['filter']['reading_level'] == 'beginner'


class TestUserSavedContent:
    """Test user saved content retrieval."""

    @patch('src.services.content_storage.db_service.get_session')
    async def test_get_user_saved_content(self, mock_get_session, content_storage_service):
        """Test retrieving user's saved content."""
        mock_session = Mock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_get_session.return_value.__exit__.return_value = None

        # Mock reading behavior with save interaction
        mock_behavior = Mock()
        mock_behavior.content_id = "content_1"
        mock_behavior.user_id = "test_user"
        mock_behavior.start_time = datetime.utcnow()
        mock_behavior.interactions = [
            {"action": "saved", "user_rating": 4,
                "user_notes": "Good content", "tags": ["useful"]}
        ]
        mock_behavior.context = {"save_reason": "bookmark"}

        mock_content = Mock()
        mock_content.title = "Test Content"
        mock_content.language = "english"

        mock_session.query.return_value.join.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [
            mock_behavior]
        mock_session.get.return_value = mock_content

        result = await content_storage_service.get_user_saved_content("test_user", limit=10, offset=0)

        assert len(result) == 1
        assert result[0].content_id == "content_1"
        assert result[0].user_rating == 4
        assert result[0].user_notes == "Good content"
        assert "useful" in result[0].tags

    @patch('src.services.content_storage.db_service.get_session')
    async def test_get_user_saved_content_empty(self, mock_get_session, content_storage_service):
        """Test retrieving saved content when user has none."""
        mock_session = Mock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_get_session.return_value.__exit__.return_value = None

        mock_session.query.return_value.join.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []

        result = await content_storage_service.get_user_saved_content("test_user")

        assert len(result) == 0


class TestContentRecommendations:
    """Test content recommendation functionality."""

    @patch('src.services.content_storage.db_service.get_session')
    async def test_get_content_recommendations_by_topics(self, mock_get_session, content_storage_service):
        """Test getting content recommendations by topics."""
        mock_session = Mock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_get_session.return_value.__exit__.return_value = None

        mock_content = Mock()
        mock_session.query.return_value.filter.return_value.filter.return_value.limit.return_value.all.return_value = [
            mock_content]

        with patch('src.schemas.content.ContentItemResponse.from_orm') as mock_from_orm:
            mock_from_orm.return_value = Mock()

            result = await content_storage_service.get_content_recommendations_by_topics(
                topics=["technology", "programming"],
                language="english",
                reading_level="intermediate",
                limit=5
            )

            assert len(result) == 1
            mock_session.query.assert_called_once()

    @patch('src.services.content_storage.db_service.get_session')
    async def test_update_content_metadata(self, mock_get_session, content_storage_service):
        """Test updating content metadata."""
        mock_session = Mock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_get_session.return_value.__exit__.return_value = None

        mock_content = Mock()
        mock_content.content_metadata = {"existing": "data"}
        mock_session.get.return_value = mock_content

        with patch('src.schemas.content.ContentItemResponse.from_orm') as mock_from_orm:
            mock_from_orm.return_value = Mock()

            result = await content_storage_service.update_content_metadata(
                "content_1",
                {"new_field": "new_value", "existing": "updated"}
            )

            assert mock_content.content_metadata["new_field"] == "new_value"
            assert mock_content.content_metadata["existing"] == "updated"
            mock_session.commit.assert_called_once()


class TestVectorEmbedding:
    """Test vector embedding functionality."""

    async def test_store_vector_embedding_success(self, content_storage_service):
        """Test successful vector embedding storage."""
        embedding = [0.1, 0.2, 0.3, 0.4]
        metadata = {"title": "Test", "language": "english"}

        await content_storage_service._store_vector_embedding("content_1", embedding, metadata)

        content_storage_service.index.upsert.assert_called_once_with(
            vectors=[("content_1", embedding, metadata)]
        )

    async def test_store_vector_embedding_failure(self, content_storage_service):
        """Test vector embedding storage failure handling."""
        content_storage_service.index.upsert.side_effect = Exception(
            "Pinecone error")

        # Should not raise exception - just log error
        await content_storage_service._store_vector_embedding("content_1", [0.1, 0.2], {})

    async def test_store_vector_embedding_no_index(self, content_storage_service):
        """Test vector embedding storage when index is unavailable."""
        content_storage_service.index = None

        # Should not raise exception
        await content_storage_service._store_vector_embedding("content_1", [0.1, 0.2], {})


class TestEdgeCases:
    """Test edge cases and error handling."""

    async def test_ingest_content_with_processing_error(self, content_storage_service, sample_content_create):
        """Test content ingestion when processing fails."""
        with patch.object(content_storage_service.processor, 'analyze_content', side_effect=Exception("Processing error")):
            with pytest.raises(Exception, match="Processing error"):
                await content_storage_service.ingest_content(sample_content_create)

    async def test_search_with_empty_query(self, content_storage_service):
        """Test search with empty query text."""
        request = ContentSearchRequest(query_text="")

        # Should handle gracefully
        with patch('src.services.content_storage.db_service.get_session'):
            result = await content_storage_service.search_content_by_similarity(request)
            assert result.query_text == ""

    async def test_save_content_with_invalid_user(self, content_storage_service):
        """Test saving content with invalid user ID."""
        with patch('src.services.content_storage.db_service.get_session') as mock_get_session:
            mock_session = Mock()
            mock_get_session.return_value.__enter__.return_value = mock_session
            mock_get_session.return_value.__exit__.return_value = None
            # content exists, user doesn't
            mock_session.get.side_effect = [Mock(), None]

            request = SavedContentRequest(
                content_id="test_content",
                user_id="invalid_user"
            )

            with pytest.raises(ValueError, match="User invalid_user not found"):
                await content_storage_service.save_content_for_user(request)
