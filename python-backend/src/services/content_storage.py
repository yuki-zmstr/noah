"""Enhanced content storage service with vector similarity search and metadata management."""

import logging
import uuid
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from contextlib import asynccontextmanager

from pinecone import Pinecone
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from sqlalchemy.exc import SQLAlchemyError

from src.models.content import ContentItem
from src.models.user_profile import UserProfile, ReadingBehavior
from src.schemas.content import (
    ContentItemCreate, ContentItemResponse, ContentAnalysis,
    ContentMetadata, SavedContentRequest, SavedContentResponse,
    ContentSearchRequest, ContentSearchResponse
)
from src.services.content_processor import content_processor
from src.services.database import db_service
from src.vector_db_init import VectorDBManager
from src.config import settings

logger = logging.getLogger(__name__)


class ContentStorageService:
    """Enhanced content storage service with vector similarity search."""

    def __init__(self):
        """Initialize the content storage service."""
        self.processor = content_processor
        self.vector_db = VectorDBManager()
        self.index = None
        self._initialize_vector_index()

    def _initialize_vector_index(self):
        """Initialize Pinecone vector index."""
        try:
            self.index = self.vector_db.get_index()
            logger.info("Vector index initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize vector index: {e}")
            self.index = None

    async def ingest_content(self, content_data: ContentItemCreate, user_id: Optional[str] = None) -> ContentItemResponse:
        """
        Ingest new content with automatic metadata extraction and vector storage.

        Args:
            content_data: Content item creation data
            user_id: Optional user ID for user-specific metadata

        Returns:
            ContentItemResponse with processed content
        """
        logger.info(f"Ingesting content: {content_data.title}")

        try:
            # Generate unique ID if not provided
            if not content_data.id:
                content_data.id = str(uuid.uuid4())

            # Analyze content for metadata extraction
            analysis = self.processor.analyze_content(
                content=content_data.content,
                language=content_data.language,
                metadata=content_data.metadata,
                title=content_data.title
            )

            # Extract additional metadata
            enhanced_metadata = self._extract_enhanced_metadata(
                content_data.content, content_data.metadata, analysis, user_id
            )

            # Store in database
            with db_service.get_session() as session:
                content_item = ContentItem(
                    id=content_data.id,
                    title=content_data.title,
                    content=content_data.content,
                    language=content_data.language,
                    content_metadata=enhanced_metadata.dict(),
                    analysis=analysis.dict(),
                    adaptations=[],
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )

                session.add(content_item)
                session.flush()

                # Store vector embedding
                if self.index and analysis.embedding:
                    await self._store_vector_embedding(
                        content_id=content_data.id,
                        embedding=analysis.embedding,
                        metadata={
                            "title": content_data.title,
                            "language": content_data.language,
                            "reading_level": analysis.reading_level.get("level", "intermediate"),
                            "topics": [topic["topic"] for topic in analysis.topics[:5]],
                            "user_id": user_id or "public"
                        }
                    )

                session.commit()
                session.refresh(content_item)

                return ContentItemResponse.from_orm(content_item)

        except Exception as e:
            logger.error(f"Failed to ingest content {content_data.id}: {e}")
            raise

    async def save_content_for_user(self, request: SavedContentRequest) -> SavedContentResponse:
        """
        Save content for a specific user with user-specific metadata.

        Args:
            request: Saved content request with user ID and metadata

        Returns:
            SavedContentResponse with saved content details
        """
        logger.info(
            f"Saving content {request.content_id} for user {request.user_id}")

        try:
            with db_service.get_session() as session:
                # Check if content exists
                content_item = session.get(ContentItem, request.content_id)
                if not content_item:
                    raise ValueError(f"Content {request.content_id} not found")

                # Check if user exists
                user_profile = session.get(UserProfile, request.user_id)
                if not user_profile:
                    raise ValueError(f"User {request.user_id} not found")

                # Create or update reading behavior record
                existing_behavior = session.query(ReadingBehavior).filter(
                    and_(
                        ReadingBehavior.content_id == request.content_id,
                        ReadingBehavior.user_id == request.user_id
                    )
                ).first()

                if existing_behavior:
                    # Update existing record
                    existing_behavior.interactions = existing_behavior.interactions or []
                    existing_behavior.interactions.append({
                        "action": "saved",
                        "timestamp": datetime.utcnow().isoformat(),
                        "user_rating": request.user_rating,
                        "user_notes": request.user_notes,
                        "tags": request.tags
                    })
                    behavior_record = existing_behavior
                else:
                    # Create new record
                    behavior_record = ReadingBehavior(
                        content_id=request.content_id,
                        user_id=request.user_id,
                        session_id=f"save_{uuid.uuid4()}",
                        start_time=datetime.utcnow(),
                        completion_rate=1.0,  # Assume saved content is "completed"
                        interactions=[{
                            "action": "saved",
                            "timestamp": datetime.utcnow().isoformat(),
                            "user_rating": request.user_rating,
                            "user_notes": request.user_notes,
                            "tags": request.tags
                        }],
                        context={
                            "save_reason": request.save_reason,
                            "user_metadata": request.user_metadata
                        }
                    )
                    session.add(behavior_record)

                session.commit()
                session.refresh(behavior_record)

                return SavedContentResponse(
                    content_id=request.content_id,
                    user_id=request.user_id,
                    saved_at=behavior_record.start_time,
                    user_rating=request.user_rating,
                    user_notes=request.user_notes,
                    tags=request.tags,
                    save_reason=request.save_reason,
                    content_title=content_item.title,
                    content_language=content_item.language
                )

        except Exception as e:
            logger.error(f"Failed to save content for user: {e}")
            raise

    async def search_content_by_similarity(self, request: ContentSearchRequest) -> ContentSearchResponse:
        """
        Search for similar content using vector similarity search.

        Args:
            request: Content search request with query and filters

        Returns:
            ContentSearchResponse with similar content items
        """
        logger.info(
            f"Searching for content similar to: {request.query_text[:50]}...")

        try:
            # Generate embedding for query
            query_embedding = self.processor._generate_embedding(
                request.query_text)

            if not self.index or not query_embedding:
                # Fallback to text-based search
                return await self._fallback_text_search(request)

            # Prepare search filters
            search_filters = {}
            if request.language:
                search_filters["language"] = request.language
            if request.reading_level:
                search_filters["reading_level"] = request.reading_level
            if request.user_id:
                # Include both user-specific and public content
                search_filters["user_id"] = {
                    "$in": [request.user_id, "public"]}

            # Perform vector similarity search
            search_results = self.index.query(
                vector=query_embedding,
                filter=search_filters if search_filters else None,
                top_k=request.limit,
                include_metadata=True
            )

            # Retrieve full content items from database
            content_ids = [match.id for match in search_results.matches]

            with db_service.get_session() as session:
                content_items = session.query(ContentItem).filter(
                    ContentItem.id.in_(content_ids)
                ).all()

                # Create response with similarity scores
                results = []
                for match in search_results.matches:
                    content_item = next(
                        (item for item in content_items if item.id == match.id), None
                    )
                    if content_item:
                        results.append({
                            "content": ContentItemResponse.from_orm(content_item),
                            "similarity_score": match.score,
                            "match_metadata": match.metadata
                        })

                return ContentSearchResponse(
                    query_text=request.query_text,
                    results=results,
                    total_results=len(results),
                    search_method="vector_similarity"
                )

        except Exception as e:
            logger.error(f"Vector similarity search failed: {e}")
            # Fallback to text-based search
            return await self._fallback_text_search(request)

    async def get_user_saved_content(self, user_id: str, limit: int = 20, offset: int = 0) -> List[SavedContentResponse]:
        """
        Get all content saved by a specific user.

        Args:
            user_id: User ID
            limit: Maximum number of results
            offset: Offset for pagination

        Returns:
            List of saved content responses
        """
        logger.info(f"Retrieving saved content for user {user_id}")

        try:
            with db_service.get_session() as session:
                # Query reading behaviors where user saved content
                behaviors = session.query(ReadingBehavior).join(
                    ContentItem, ReadingBehavior.content_id == ContentItem.id
                ).filter(
                    and_(
                        ReadingBehavior.user_id == user_id,
                        ReadingBehavior.interactions.op('?')(
                            'action')  # Has 'action' key
                    )
                ).order_by(desc(ReadingBehavior.start_time)).offset(offset).limit(limit).all()

                results = []
                for behavior in behaviors:
                    # Check if this behavior includes a save action
                    save_interactions = [
                        interaction for interaction in (behavior.interactions or [])
                        if interaction.get("action") == "saved"
                    ]

                    if save_interactions:
                        # Get most recent save
                        latest_save = save_interactions[-1]
                        content_item = session.get(
                            ContentItem, behavior.content_id)

                        if content_item:
                            results.append(SavedContentResponse(
                                content_id=behavior.content_id,
                                user_id=user_id,
                                saved_at=behavior.start_time,
                                user_rating=latest_save.get("user_rating"),
                                user_notes=latest_save.get("user_notes"),
                                tags=latest_save.get("tags", []),
                                save_reason=behavior.context.get(
                                    "save_reason") if behavior.context else None,
                                content_title=content_item.title,
                                content_language=content_item.language
                            ))

                return results

        except Exception as e:
            logger.error(
                f"Failed to retrieve saved content for user {user_id}: {e}")
            raise

    async def get_content_recommendations_by_topics(self, topics: List[str], language: str,
                                                    reading_level: str, limit: int = 10) -> List[ContentItemResponse]:
        """
        Get content recommendations based on topics.

        Args:
            topics: List of topics to search for
            language: Content language
            reading_level: Target reading level
            limit: Maximum number of results

        Returns:
            List of recommended content items
        """
        logger.info(f"Getting recommendations for topics: {topics}")

        try:
            with db_service.get_session() as session:
                # Build query for content matching topics and criteria
                query = session.query(ContentItem).filter(
                    and_(
                        ContentItem.language == language,
                        ContentItem.analysis.op(
                            '->>')('reading_level').op('->>')('level') == reading_level
                    )
                )

                # Filter by topics (check if any topic appears in content analysis)
                topic_conditions = []
                for topic in topics:
                    topic_conditions.append(
                        ContentItem.analysis.op(
                            '@>')([{"topics": [{"topic": topic}]}])
                    )

                if topic_conditions:
                    query = query.filter(or_(*topic_conditions))

                content_items = query.limit(limit).all()
                return [ContentItemResponse.from_orm(item) for item in content_items]

        except Exception as e:
            logger.error(f"Failed to get topic-based recommendations: {e}")
            raise

    async def update_content_metadata(self, content_id: str, metadata_updates: Dict[str, Any]) -> ContentItemResponse:
        """
        Update content metadata.

        Args:
            content_id: Content ID
            metadata_updates: Dictionary of metadata updates

        Returns:
            Updated content item response
        """
        logger.info(f"Updating metadata for content {content_id}")

        try:
            with db_service.get_session() as session:
                content_item = session.get(ContentItem, content_id)
                if not content_item:
                    raise ValueError(f"Content {content_id} not found")

                # Update metadata
                current_metadata = content_item.content_metadata or {}
                current_metadata.update(metadata_updates)
                content_item.content_metadata = current_metadata
                content_item.updated_at = datetime.utcnow()

                session.commit()
                session.refresh(content_item)

                return ContentItemResponse.from_orm(content_item)

        except Exception as e:
            logger.error(f"Failed to update content metadata: {e}")
            raise

    def _extract_enhanced_metadata(self, content: str, base_metadata: ContentMetadata,
                                   analysis: ContentAnalysis, user_id: Optional[str] = None) -> ContentMetadata:
        """
        Extract enhanced metadata from content and analysis.

        Args:
            content: Original content text
            base_metadata: Base metadata provided
            analysis: Content analysis results
            user_id: Optional user ID for user-specific metadata

        Returns:
            Enhanced ContentMetadata
        """
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

    async def _store_vector_embedding(self, content_id: str, embedding: List[float], metadata: Dict[str, Any]):
        """
        Store vector embedding in Pinecone.

        Args:
            content_id: Content ID
            embedding: Vector embedding
            metadata: Associated metadata
        """
        try:
            if self.index:
                self.index.upsert(
                    vectors=[(content_id, embedding, metadata)]
                )
                logger.debug(
                    f"Stored vector embedding for content {content_id}")
        except Exception as e:
            logger.error(f"Failed to store vector embedding: {e}")
            # Don't raise - this is not critical for content storage

    async def _fallback_text_search(self, request: ContentSearchRequest) -> ContentSearchResponse:
        """
        Fallback text-based search when vector search is unavailable.

        Args:
            request: Content search request

        Returns:
            ContentSearchResponse with text-based results
        """
        logger.info("Using fallback text-based search")

        try:
            with db_service.get_session() as session:
                query = session.query(ContentItem)

                # Apply filters
                if request.language:
                    query = query.filter(
                        ContentItem.language == request.language)

                if request.reading_level:
                    query = query.filter(
                        ContentItem.analysis.op(
                            '->>')('reading_level').op('->>')('level') == request.reading_level
                    )

                # Text search in title and content
                search_term = f"%{request.query_text.lower()}%"
                query = query.filter(
                    or_(
                        func.lower(ContentItem.title).like(search_term),
                        func.lower(ContentItem.content).like(search_term)
                    )
                )

                content_items = query.limit(request.limit).all()

                results = [
                    {
                        "content": ContentItemResponse.from_orm(item),
                        "similarity_score": 0.5,  # Default score for text search
                        "match_metadata": {"search_method": "text_based"}
                    }
                    for item in content_items
                ]

                return ContentSearchResponse(
                    query_text=request.query_text,
                    results=results,
                    total_results=len(results),
                    search_method="text_based_fallback"
                )

        except Exception as e:
            logger.error(f"Fallback text search failed: {e}")
            raise


# Global instance
content_storage_service = ContentStorageService()
