"""API endpoints for content storage and retrieval."""

import logging
from typing import List
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session

from src.database import get_db
from src.services.content_storage import content_storage_service
from src.services.database import db_service
from src.schemas.content import (
    ContentIngestionRequest, ContentItemResponse, SavedContentRequest,
    SavedContentResponse, ContentSearchRequest, ContentSearchResponse,
    ContentRecommendationRequest, ContentItemCreate, ContentMetadata
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/content-storage", tags=["content-storage"])


@router.post("/ingest", response_model=ContentItemResponse)
async def ingest_content(
    request: ContentIngestionRequest,
    db: Session = Depends(get_db)
):
    """
    Ingest new content with automatic metadata extraction and vector storage.

    This endpoint processes new content, analyzes it for topics and complexity,
    extracts metadata, and stores both the content and its vector embedding
    for similarity search.
    """
    try:
        # Create ContentMetadata from request
        metadata = ContentMetadata(
            author=request.author,
            source=request.source,
            publish_date=datetime.utcnow(),
            content_type=request.content_type,
            estimated_reading_time=max(1, len(request.content.split()) // 200),
            tags=request.tags
        )

        # Create ContentItemCreate from request
        content_data = ContentItemCreate(
            title=request.title,
            content=request.content,
            language=request.language,
            metadata=metadata
        )

        # Ingest content
        result = await content_storage_service.ingest_content(
            content_data=content_data,
            user_id=request.user_id
        )

        return result

    except Exception as e:
        logger.error(f"Content ingestion failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Content ingestion failed: {str(e)}")


@router.post("/save", response_model=SavedContentResponse)
async def save_content_for_user(
    request: SavedContentRequest,
    db: Session = Depends(get_db)
):
    """
    Save content for a specific user with user-specific metadata.

    This allows users to save content they're interested in, along with
    ratings, notes, and tags for personal organization.
    """
    try:
        result = await content_storage_service.save_content_for_user(request)
        return result

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to save content: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to save content: {str(e)}")


@router.post("/search", response_model=ContentSearchResponse)
async def search_content_by_similarity(
    request: ContentSearchRequest,
    db: Session = Depends(get_db)
):
    """
    Search for similar content using vector similarity search.

    This endpoint uses vector embeddings to find content similar to the
    query text, with optional filtering by language, reading level, and user.
    """
    try:
        result = await content_storage_service.search_content_by_similarity(request)
        return result

    except Exception as e:
        logger.error(f"Content search failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Content search failed: {str(e)}")


@router.get("/user/{user_id}/saved", response_model=List[SavedContentResponse])
async def get_user_saved_content(
    user_id: str,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Get all content saved by a specific user.

    Returns a paginated list of content that the user has saved,
    including their ratings, notes, and tags.
    """
    try:
        result = await content_storage_service.get_user_saved_content(
            user_id=user_id,
            limit=limit,
            offset=offset
        )
        return result

    except Exception as e:
        logger.error(f"Failed to retrieve saved content: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve saved content: {str(e)}")


@router.post("/recommendations", response_model=List[ContentItemResponse])
async def get_content_recommendations(
    request: ContentRecommendationRequest,
    db: Session = Depends(get_db)
):
    """
    Get content recommendations based on topics and user preferences.

    This endpoint provides content recommendations based on specified topics,
    reading level, and language preferences.
    """
    try:
        if not request.topics:
            raise HTTPException(
                status_code=400, detail="Topics are required for recommendations")

        result = await content_storage_service.get_content_recommendations_by_topics(
            topics=request.topics,
            language=request.language or "english",
            reading_level=request.reading_level or "intermediate",
            limit=request.limit
        )
        return result

    except Exception as e:
        logger.error(f"Failed to get recommendations: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get recommendations: {str(e)}")


@router.get("/content/{content_id}", response_model=ContentItemResponse)
async def get_content_by_id(
    content_id: str,
    db: Session = Depends(get_db)
):
    """
    Get a specific content item by ID.

    Returns the full content item with metadata and analysis.
    """
    try:
        with db_service.get_session() as session:
            from src.models.content import ContentItem
            content_item = session.get(ContentItem, content_id)

            if not content_item:
                raise HTTPException(
                    status_code=404, detail=f"Content {content_id} not found")

            return ContentItemResponse.from_orm(content_item)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve content: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve content: {str(e)}")


@router.put("/content/{content_id}/metadata")
async def update_content_metadata(
    content_id: str,
    metadata_updates: dict,
    db: Session = Depends(get_db)
):
    """
    Update content metadata.

    Allows updating specific metadata fields for a content item.
    """
    try:
        result = await content_storage_service.update_content_metadata(
            content_id=content_id,
            metadata_updates=metadata_updates
        )
        return result

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update metadata: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to update metadata: {str(e)}")


@router.get("/topics/{language}")
async def get_available_topics(
    language: str,
    db: Session = Depends(get_db)
):
    """
    Get all available topics for a specific language.

    Returns a list of topics extracted from content analysis,
    useful for topic-based recommendations and filtering.
    """
    try:
        # This would be implemented in the content storage service
        # For now, return a simple response
        with db_service.get_session() as session:
            from src.models.content import ContentItem
            from sqlalchemy import func

            # Get unique topics from content analysis
            content_items = session.query(ContentItem).filter(
                ContentItem.language == language
            ).all()

            topic_counts = {}
            for item in content_items:
                if item.analysis and 'topics' in item.analysis:
                    for topic_data in item.analysis['topics']:
                        topic = topic_data.get('topic', '')
                        if topic:
                            topic_counts[topic] = topic_counts.get(
                                topic, 0) + 1

            # Return sorted by frequency
            topics = [
                {"topic": topic, "count": count}
                for topic, count in sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)
            ]

            # Limit to top 50
            return {"language": language, "topics": topics[:50]}

    except Exception as e:
        logger.error(f"Failed to get topics: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get topics: {str(e)}")


@router.get("/stats")
async def get_content_storage_stats(db: Session = Depends(get_db)):
    """
    Get content storage statistics.

    Returns statistics about stored content, including counts by language,
    reading level, and other metrics.
    """
    try:
        with db_service.get_session() as session:
            from src.models.content import ContentItem
            from sqlalchemy import func

            # Get basic statistics
            total_content = session.query(func.count(ContentItem.id)).scalar()

            # Count by language
            language_stats = session.query(
                ContentItem.language,
                func.count(ContentItem.id)
            ).group_by(ContentItem.language).all()

            # Count by reading level (from analysis)
            reading_level_stats = {}
            content_items = session.query(ContentItem).all()

            for item in content_items:
                if item.analysis and 'reading_level' in item.analysis:
                    level = item.analysis['reading_level'].get(
                        'level', 'unknown')
                    reading_level_stats[level] = reading_level_stats.get(
                        level, 0) + 1

            return {
                "total_content": total_content,
                "by_language": dict(language_stats),
                "by_reading_level": reading_level_stats,
                "vector_index_available": content_storage_service.index is not None
            }

    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get stats: {str(e)}")
