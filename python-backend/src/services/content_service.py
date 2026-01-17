"""Unified content service combining processing and adaptation."""

import logging
from typing import Dict, List, Optional
from datetime import datetime

from src.services.content_processor import content_processor
from src.services.content_adapter import content_adapter, AdaptationResult
from src.schemas.content import ContentAnalysis, ContentMetadata, ContentItemCreate, ContentItemResponse
from src.models.content import ContentItem
from src.services.database import db_service

logger = logging.getLogger(__name__)


class ContentService:
    """Unified service for content processing, analysis, and adaptation."""

    def __init__(self):
        """Initialize the content service."""
        self.processor = content_processor
        self.adapter = content_adapter

    def process_and_store_content(self, content_data: ContentItemCreate) -> ContentItemResponse:
        """
        Process new content, analyze it, and store in database.

        Args:
            content_data: Content item creation data

        Returns:
            ContentItemResponse with processed content
        """
        logger.info(f"Processing content: {content_data.title}")

        try:
            # Analyze content
            analysis = self.processor.analyze_content(
                content=content_data.content,
                language=content_data.language,
                metadata=content_data.metadata
            )

            # Create content item with analysis
            with db_service.get_session() as session:
                content_item = ContentItem(
                    id=content_data.id,
                    title=content_data.title,
                    content=content_data.content,
                    language=content_data.language,
                    content_metadata=content_data.metadata.dict(),
                    analysis=analysis.dict(),
                    adaptations=[],  # Will be populated when adaptations are requested
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )

                session.add(content_item)
                session.commit()
                session.refresh(content_item)

                return ContentItemResponse.from_orm(content_item)

        except Exception as e:
            logger.error(f"Failed to process content {content_data.id}: {e}")
            raise

    def get_content_analysis(self, content_id: str) -> Optional[ContentAnalysis]:
        """
        Get content analysis for a specific content item.

        Args:
            content_id: ID of the content item

        Returns:
            ContentAnalysis if found, None otherwise
        """
        with db_service.get_session() as session:
            content_item = session.get(ContentItem, content_id)
            if content_item and content_item.analysis:
                return ContentAnalysis(**content_item.analysis)
            return None

    async def adapt_content_for_user(self, content_id: str, target_reading_level: str,
                                     user_language_preference: str = None) -> Optional[AdaptationResult]:
        """
        Adapt content to user's reading level and preferences.

        Args:
            content_id: ID of the content to adapt
            target_reading_level: Target reading level ("beginner", "intermediate", "advanced", "expert")
            user_language_preference: User's preferred language for adaptations

        Returns:
            AdaptationResult if successful, None if content not found
        """
        logger.info(
            f"Adapting content {content_id} to {target_reading_level} level")

        async with get_db_session() as session:
            content_item = await session.get(ContentItem, content_id)
            if not content_item:
                return None

            # Get current reading level from analysis
            analysis = ContentAnalysis(
                **content_item.analysis) if content_item.analysis else None
            if not analysis:
                logger.warning(f"No analysis found for content {content_id}")
                return None

            current_level = analysis.reading_level.get('level', 'intermediate')

            # Perform adaptation
            adaptation_result = self.adapter.adapt_content(
                content=content_item.content,
                language=content_item.language,
                target_level=target_reading_level,
                current_level=current_level,
                preserve_meaning=True
            )

            # Store adaptation result
            if adaptation_result.adaptations_made:
                adaptations = content_item.adaptations or []
                adaptations.append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "target_level": target_reading_level,
                    "adaptations": adaptation_result.adaptations_made,
                    "reading_level_change": adaptation_result.reading_level_change
                })

                content_item.adaptations = adaptations
                content_item.updated_at = datetime.utcnow()
                await session.commit()

            return adaptation_result

    async def search_content_by_similarity(self, query_text: str, language: str,
                                           limit: int = 10) -> List[ContentItemResponse]:
        """
        Search for similar content using embeddings.

        Args:
            query_text: Text to search for
            language: Language to search in
            limit: Maximum number of results

        Returns:
            List of similar content items
        """
        # Generate embedding for query
        query_embedding = self.processor._generate_embedding(query_text)

        # In a real implementation, this would use vector similarity search
        # For now, return a simple text-based search
        async with get_db_session() as session:
            # This is a simplified implementation - in practice, use vector database
            from sqlalchemy import and_, func

            results = await session.execute(
                session.query(ContentItem)
                .filter(and_(
                    ContentItem.language == language,
                    func.lower(ContentItem.content).contains(
                        query_text.lower())
                ))
                .limit(limit)
            )

            content_items = results.scalars().all()
            return [ContentItemResponse.from_orm(item) for item in content_items]

    async def get_content_by_reading_level(self, language: str, reading_level: str,
                                           limit: int = 10) -> List[ContentItemResponse]:
        """
        Get content filtered by reading level.

        Args:
            language: Content language
            reading_level: Target reading level
            limit: Maximum number of results

        Returns:
            List of content items at the specified reading level
        """
        async with get_db_session() as session:
            from sqlalchemy import and_

            # Query content with matching reading level
            results = await session.execute(
                session.query(ContentItem)
                .filter(and_(
                    ContentItem.language == language,
                    ContentItem.analysis.op(
                        '->>')('reading_level').op('->>')('level') == reading_level
                ))
                .limit(limit)
            )

            content_items = results.scalars().all()
            return [ContentItemResponse.from_orm(item) for item in content_items]

    async def get_content_topics(self, language: str) -> List[Dict]:
        """
        Get all unique topics from content analysis.

        Args:
            language: Content language

        Returns:
            List of topics with frequency counts
        """
        async with get_db_session() as session:
            from sqlalchemy import and_

            results = await session.execute(
                session.query(ContentItem)
                .filter(ContentItem.language == language)
            )

            content_items = results.scalars().all()
            topic_counts = {}

            for item in content_items:
                if item.analysis and 'topics' in item.analysis:
                    for topic_data in item.analysis['topics']:
                        topic = topic_data.get('topic', '')
                        if topic:
                            topic_counts[topic] = topic_counts.get(
                                topic, 0) + 1

            # Return sorted by frequency
            return [
                {"topic": topic, "count": count}
                for topic, count in sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)
            ]

    def analyze_text_sample(self, text: str, language: str) -> ContentAnalysis:
        """
        Analyze a text sample without storing it.

        Args:
            text: Text to analyze
            language: Language of the text

        Returns:
            ContentAnalysis results
        """
        # Create minimal metadata for analysis
        metadata = ContentMetadata(
            author="Unknown",
            source="Sample",
            publish_date=datetime.utcnow(),
            content_type="text",
            estimated_reading_time=max(
                1, len(text.split()) // 200),  # Rough estimate
            tags=[]
        )

        return self.processor.analyze_content(text, language, metadata)

    def adapt_text_sample(self, text: str, language: str, target_level: str) -> AdaptationResult:
        """
        Adapt a text sample without storing it.

        Args:
            text: Text to adapt
            language: Language of the text
            target_level: Target reading level

        Returns:
            AdaptationResult
        """
        # First analyze to get current level
        analysis = self.analyze_text_sample(text, language)
        current_level = analysis.reading_level.get('level', 'intermediate')

        return self.adapter.adapt_content(
            content=text,
            language=language,
            target_level=target_level,
            current_level=current_level,
            preserve_meaning=True
        )


# Global instance
content_service = ContentService()
