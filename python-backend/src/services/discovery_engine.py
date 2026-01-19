"""Discovery mode engine for serendipitous content recommendations."""

import logging
from typing import Dict, List, Optional, Tuple, Set
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func, not_

from src.models.user_profile import UserProfile, ReadingBehavior
from src.models.content import ContentItem, DiscoveryRecommendation
from src.schemas.user_profile import PreferenceModel, LanguageReadingLevels
from src.schemas.content import ContentAnalysis
from src.services.user_profile_service import user_profile_engine
from src.services.database import db_service

logger = logging.getLogger(__name__)


class DiscoveryModeEngine:
    """Engine for generating serendipitous 'I'm feeling lucky' recommendations."""

    def __init__(self):
        """Initialize the discovery engine."""
        self.min_divergence_score = 0.4  # Minimum divergence from user preferences
        self.max_divergence_score = 0.8  # Maximum divergence to maintain accessibility
        self.collaborative_weight = 0.4  # Weight for collaborative filtering
        self.content_diversity_weight = 0.3  # Weight for content diversity
        self.serendipity_weight = 0.3  # Weight for serendipitous connections

        # Genre exploration strategies
        self.genre_bridges = {
            "fiction": ["historical_fiction", "science_fiction", "literary_fiction"],
            "non_fiction": ["biography", "memoir", "popular_science"],
            "mystery": ["thriller", "crime", "detective"],
            "romance": ["contemporary_romance", "historical_romance", "romantic_comedy"],
            "science": ["popular_science", "science_fiction", "technology"],
            "history": ["historical_fiction", "biography", "cultural_studies"]
        }

        # Topic bridging connections
        self.topic_bridges = {
            "technology": ["innovation", "future", "society", "ethics"],
            "psychology": ["behavior", "relationships", "self_help", "neuroscience"],
            "art": ["creativity", "culture", "history", "philosophy"],
            "travel": ["culture", "geography", "adventure", "memoir"]
        }

    async def generate_discovery_recommendations(
        self,
        user_id: str,
        limit: int = 5,
        language: Optional[str] = None,
        db: Session = None
    ) -> List[Dict]:
        """
        Generate discovery mode recommendations that diverge from user preferences.

        Args:
            user_id: User identifier
            limit: Maximum number of recommendations
            language: Preferred language filter
            db: Database session

        Returns:
            List of discovery recommendation dictionaries
        """
        import time
        start_time = time.time()
        logger.info(f"Generating discovery recommendations for user {user_id}")

        if not db:
            # Database session must be provided by the caller
            raise ValueError("Database session must be provided to generate_discovery_recommendations")

        try:
            # Get user profile and reading history
            profile_start = time.time()
            profile = await user_profile_engine.get_or_create_profile(user_id, db)
            preferences = PreferenceModel(**profile.preferences)
            reading_levels = LanguageReadingLevels(**profile.reading_levels)
            logger.info(f"Profile retrieval took {time.time() - profile_start:.2f}s")

            # Analyze user's established preferences
            patterns_start = time.time()
            user_patterns = await self._analyze_user_patterns(user_id, preferences, db)
            logger.info(f"Pattern analysis took {time.time() - patterns_start:.2f}s")

            # Get discovery candidates
            candidates_start = time.time()
            candidates = await self._get_discovery_candidates(
                user_id, user_patterns, language, reading_levels, db
            )
            logger.info(f"Candidate retrieval took {time.time() - candidates_start:.2f}s, found {len(candidates)} candidates")

            if not candidates:
                logger.warning(
                    f"No discovery candidates found for user {user_id}")
                return []

            # Score candidates for discovery potential (parallelized)
            scoring_start = time.time()
            import asyncio
            
            async def score_candidate(content):
                discovery_data = await self._calculate_discovery_score(
                    content, user_patterns, preferences, reading_levels, user_id, db
                )
                
                if discovery_data["divergence_score"] >= self.min_divergence_score:
                    # Store discovery recommendation for tracking
                    await self._store_discovery_recommendation(
                        user_id, content.id, discovery_data, db
                    )
                    
                    return {
                        "content_id": content.id,
                        "title": content.title,
                        "language": content.language,
                        "metadata": content.content_metadata,
                        "analysis": content.analysis,
                        "divergence_score": discovery_data["divergence_score"],
                        "bridging_topics": discovery_data["bridging_topics"],
                        "discovery_reason": discovery_data["discovery_reason"],
                        "accessibility_score": discovery_data["accessibility_score"],
                        "serendipity_factors": discovery_data["serendipity_factors"]
                    }
                return None
            
            # Process candidates in parallel batches of 10 to avoid overwhelming the database
            batch_size = 10
            discovery_recommendations = []
            
            for i in range(0, len(candidates), batch_size):
                batch = candidates[i:i + batch_size]
                batch_results = await asyncio.gather(
                    *[score_candidate(content) for content in batch],
                    return_exceptions=True
                )
                
                # Filter out None results and exceptions
                for result in batch_results:
                    if result is not None and not isinstance(result, Exception):
                        discovery_recommendations.append(result)
            
            logger.info(f"Scoring took {time.time() - scoring_start:.2f}s, generated {len(discovery_recommendations)} recommendations")

            # Apply serendipity filtering and ranking
            ranking_start = time.time()
            final_recommendations = self._rank_discovery_recommendations(
                discovery_recommendations, limit
            )
            logger.info(f"Ranking took {time.time() - ranking_start:.2f}s")
            
            total_time = time.time() - start_time
            logger.info(f"Total discovery recommendation generation took {total_time:.2f}s for user {user_id}")
            logger.info(
                f"Generated {len(final_recommendations)} discovery recommendations for user {user_id}")
            return final_recommendations

        except Exception as e:
            logger.error(
                f"Error generating discovery recommendations for user {user_id}: {e}")
            raise

    async def _analyze_user_patterns(
        self,
        user_id: str,
        preferences: PreferenceModel,
        db: Session
    ) -> Dict:
        """Analyze user's established reading patterns."""
        # Get reading history
        behaviors = db.query(ReadingBehavior).filter(
            ReadingBehavior.user_id == user_id
        ).order_by(desc(ReadingBehavior.created_at)).limit(50).all()

        # Analyze established topics
        established_topics = set()
        topic_weights = {}
        for topic_pref in preferences.topics:
            topic = topic_pref.get("topic", "")
            weight = topic_pref.get("weight", 0.0)
            if weight > 0.3:  # Significant positive preference
                established_topics.add(topic)
                topic_weights[topic] = weight

        # Analyze content types
        content_type_counts = Counter()
        for behavior in behaviors:
            if hasattr(behavior, 'content_item') and behavior.content_item:
                content_type = behavior.content_item.content_metadata.get(
                    "content_type", "unknown")
                content_type_counts[content_type] += 1

        established_content_types = set(
            ct for ct, count in content_type_counts.most_common(3)
        )

        # Analyze reading level comfort zone
        reading_levels = []
        for behavior in behaviors:
            if (hasattr(behavior, 'content_item') and behavior.content_item and
                behavior.content_item.analysis and behavior.completion_rate and
                    behavior.completion_rate > 0.7):

                analysis = behavior.content_item.analysis
                if behavior.content_item.language == "english":
                    level = analysis.get("reading_level", {}).get(
                        "flesch_kincaid", 8.0)
                    reading_levels.append(level)
                elif behavior.content_item.language == "japanese":
                    level = analysis.get("reading_level", {}).get(
                        "kanji_density", 0.3)
                    reading_levels.append(level)

        comfort_zone = {
            "min": min(reading_levels) if reading_levels else 0,
            "max": max(reading_levels) if reading_levels else 1,
            "avg": np.mean(reading_levels) if reading_levels else 0.5
        }

        # Identify unexplored areas
        all_topics = await self._get_all_available_topics(db)
        unexplored_topics = all_topics - established_topics

        all_content_types = await self._get_all_content_types(db)
        unexplored_content_types = all_content_types - established_content_types

        return {
            "established_topics": established_topics,
            "topic_weights": topic_weights,
            "established_content_types": established_content_types,
            "unexplored_topics": unexplored_topics,
            "unexplored_content_types": unexplored_content_types,
            "reading_comfort_zone": comfort_zone,
            "total_reading_sessions": len(behaviors)
        }

    async def _get_discovery_candidates(
        self,
        user_id: str,
        user_patterns: Dict,
        language: Optional[str],
        reading_levels: LanguageReadingLevels,
        db: Session
    ) -> List[ContentItem]:
        """Get candidate content for discovery recommendations."""
        # Get content user hasn't read
        read_content_ids = set()
        user_behaviors = db.query(ReadingBehavior).filter(
            ReadingBehavior.user_id == user_id
        ).all()

        for behavior in user_behaviors:
            read_content_ids.add(behavior.content_id)

        # Get content not previously recommended in discovery mode
        previous_discovery_ids = set()
        previous_discoveries = db.query(DiscoveryRecommendation).filter(
            and_(
                DiscoveryRecommendation.user_id == user_id,
                DiscoveryRecommendation.created_at >= datetime.utcnow() - timedelta(days=30)
            )
        ).all()

        for discovery in previous_discoveries:
            previous_discovery_ids.add(discovery.content_id)

        # Build query for candidates
        query = db.query(ContentItem)

        # Filter by language if specified
        if language:
            query = query.filter(ContentItem.language == language)

        # Exclude read and previously discovered content
        excluded_ids = read_content_ids | previous_discovery_ids
        if excluded_ids:
            query = query.filter(~ContentItem.id.in_(excluded_ids))

        # Require analysis data
        query = query.filter(ContentItem.analysis.isnot(None))

        # Get candidates with optimized limit
        candidates = query.limit(50).all()  # Reduced from 200 to 50 for better performance

        # Filter for discovery potential
        discovery_candidates = []
        for content in candidates:
            if await self._has_discovery_potential(content, user_patterns, reading_levels):
                discovery_candidates.append(content)

        return discovery_candidates

    async def _has_discovery_potential(
        self,
        content: ContentItem,
        user_patterns: Dict,
        reading_levels: LanguageReadingLevels
    ) -> bool:
        """Check if content has discovery potential for the user."""
        if not content.analysis:
            return False

        analysis = ContentAnalysis(**content.analysis)

        # Check reading level accessibility
        if not await self._is_accessible_reading_level(content, reading_levels):
            return False

        # Check for topic divergence
        content_topics = set(t.get("topic", "") for t in analysis.topics)
        established_topics = user_patterns["established_topics"]

        # Must have some divergence from established topics
        topic_overlap = len(content_topics & established_topics)
        topic_divergence = len(content_topics - established_topics)

        if topic_divergence == 0:  # No new topics
            return False

        # Check for bridging potential
        has_bridge = self._has_bridging_topics(
            content_topics, established_topics)

        # Content type divergence
        content_type = content.content_metadata.get("content_type", "unknown")
        type_divergence = content_type not in user_patterns["established_content_types"]

        # Must have either topic divergence with bridging or content type divergence
        return has_bridge or type_divergence

    async def _is_accessible_reading_level(
        self,
        content: ContentItem,
        reading_levels: LanguageReadingLevels
    ) -> bool:
        """Check if content is at an accessible reading level for discovery."""
        if not content.analysis:
            return True

        analysis = ContentAnalysis(**content.analysis)

        if content.language == "english":
            user_level_data = reading_levels.english.get("level", "intermediate")
            # Convert level names to numeric values
            level_mapping = {
                "beginner": 5.0,
                "intermediate": 8.0,
                "advanced": 12.0,
                "expert": 16.0
            }
            user_level = level_mapping.get(user_level_data, 8.0)
            content_level = analysis.reading_level.get("flesch_kincaid", 8.0)

            # Allow slightly more challenging content for discovery
            return content_level <= user_level + 3.0

        elif content.language == "japanese":
            user_level_data = reading_levels.japanese.get("level", "intermediate")
            # Convert level names to numeric values
            level_mapping = {
                "beginner": 0.1,
                "intermediate": 0.3,
                "advanced": 0.5,
                "expert": 0.7
            }
            user_level = level_mapping.get(user_level_data, 0.3)
            content_level = analysis.reading_level.get("kanji_density", 0.3)

            return content_level <= user_level + 0.3

        return True

    def _has_bridging_topics(self, content_topics: Set[str], established_topics: Set[str]) -> bool:
        """Check if content has topics that bridge to user's established interests."""
        # Check genre bridges
        for established_topic in established_topics:
            if established_topic in self.genre_bridges:
                bridge_topics = set(self.genre_bridges[established_topic])
                if content_topics & bridge_topics:
                    return True

        # Check topic bridges
        for established_topic in established_topics:
            if established_topic in self.topic_bridges:
                bridge_topics = set(self.topic_bridges[established_topic])
                if content_topics & bridge_topics:
                    return True

        return False

    async def _calculate_discovery_score(
        self,
        content: ContentItem,
        user_patterns: Dict,
        preferences: PreferenceModel,
        reading_levels: LanguageReadingLevels,
        user_id: str,
        db: Session
    ) -> Dict:
        """Calculate discovery score and metadata for content."""
        analysis = ContentAnalysis(
            **content.analysis) if content.analysis else None

        # Calculate divergence score
        divergence_score = await self._calculate_divergence_score(
            content, user_patterns, analysis
        )

        # Calculate accessibility score
        accessibility_score = await self._calculate_accessibility_score(
            content, reading_levels, analysis
        )

        # Find bridging topics
        bridging_topics = self._find_bridging_topics(
            content, user_patterns, analysis
        )

        # Calculate serendipity factors
        serendipity_factors = await self._calculate_serendipity_factors(
            content, user_id, db
        )

        # Generate discovery reason
        discovery_reason = self._generate_discovery_reason(
            content, user_patterns, bridging_topics, serendipity_factors
        )

        return {
            "divergence_score": divergence_score,
            "accessibility_score": accessibility_score,
            "bridging_topics": bridging_topics,
            "discovery_reason": discovery_reason,
            "serendipity_factors": serendipity_factors
        }

    async def _calculate_divergence_score(
        self,
        content: ContentItem,
        user_patterns: Dict,
        analysis: Optional[ContentAnalysis]
    ) -> float:
        """Calculate how much content diverges from user's established preferences."""
        if not analysis:
            return 0.5

        # Topic divergence
        content_topics = set(t.get("topic", "") for t in analysis.topics)
        established_topics = user_patterns["established_topics"]

        if not content_topics:
            return 0.3

        # Calculate topic overlap and divergence
        overlap = len(content_topics & established_topics)
        total_content_topics = len(content_topics)

        topic_divergence = 1.0 - \
            (overlap / total_content_topics) if total_content_topics > 0 else 0.5

        # Content type divergence
        content_type = content.content_metadata.get("content_type", "unknown")
        type_divergence = 1.0 if content_type not in user_patterns[
            "established_content_types"] else 0.0

        # Combine divergence factors
        combined_divergence = (topic_divergence * 0.7) + \
            (type_divergence * 0.3)

        return min(1.0, max(0.0, combined_divergence))

    async def _calculate_accessibility_score(
        self,
        content: ContentItem,
        reading_levels: LanguageReadingLevels,
        analysis: Optional[ContentAnalysis]
    ) -> float:
        """Calculate how accessible the content is despite divergence."""
        if not analysis:
            return 0.5

        # Reading level accessibility
        if content.language == "english":
            user_level = reading_levels.english.get("level", 8.0)
            content_level = analysis.reading_level.get("flesch_kincaid", 8.0)

            level_diff = abs(content_level - user_level)
            if level_diff <= 1.0:
                level_score = 1.0
            elif level_diff <= 2.0:
                level_score = 0.8
            elif level_diff <= 3.0:
                level_score = 0.6
            else:
                level_score = 0.3

        elif content.language == "japanese":
            user_level = reading_levels.japanese.get("level", 0.3)
            content_level = analysis.reading_level.get("kanji_density", 0.3)

            level_diff = abs(content_level - user_level)
            if level_diff <= 0.1:
                level_score = 1.0
            elif level_diff <= 0.2:
                level_score = 0.8
            elif level_diff <= 0.3:
                level_score = 0.6
            else:
                level_score = 0.3
        else:
            level_score = 0.5

        # Content length accessibility
        reading_time = content.content_metadata.get(
            "estimated_reading_time", 10)
        if reading_time <= 20:
            length_score = 1.0
        elif reading_time <= 45:
            length_score = 0.8
        else:
            length_score = 0.6

        return (level_score * 0.7) + (length_score * 0.3)

    def _find_bridging_topics(
        self,
        content: ContentItem,
        user_patterns: Dict,
        analysis: Optional[ContentAnalysis]
    ) -> List[str]:
        """Find topics that bridge content to user's established interests."""
        if not analysis:
            return []

        content_topics = set(t.get("topic", "") for t in analysis.topics)
        established_topics = user_patterns["established_topics"]
        bridging_topics = []

        # Find direct bridges
        for established_topic in established_topics:
            # Genre bridges
            if established_topic in self.genre_bridges:
                bridge_topics = set(self.genre_bridges[established_topic])
                bridges = content_topics & bridge_topics
                bridging_topics.extend(list(bridges))

            # Topic bridges
            if established_topic in self.topic_bridges:
                bridge_topics = set(self.topic_bridges[established_topic])
                bridges = content_topics & bridge_topics
                bridging_topics.extend(list(bridges))

        return list(set(bridging_topics))  # Remove duplicates

    async def _calculate_serendipity_factors(
        self,
        content: ContentItem,
        user_id: str,
        db: Session
    ) -> Dict:
        """Calculate serendipitous connection factors."""
        factors = {}

        # Collaborative filtering serendipity - optimized with single query
        try:
            similar_users_count = db.query(ReadingBehavior).filter(
                ReadingBehavior.content_id == content.id,
                ReadingBehavior.user_id != user_id
            ).count()
            
            if similar_users_count > 0:
                factors["collaborative_discovery"] = similar_users_count
                factors["similar_user_count"] = similar_users_count
        except Exception as e:
            logger.warning(f"Error calculating collaborative serendipity: {e}")
            factors["similar_user_count"] = 0

        # Temporal serendipity (trending or recently added)
        days_since_added = (datetime.utcnow() - content.created_at).days
        if days_since_added <= 7:
            factors["recently_added"] = True

        # Popularity serendipity (not too popular, not too obscure)
        # Use cached read count if available, otherwise query
        read_count = getattr(content, '_cached_read_count', None)
        if read_count is None:
            try:
                read_count = db.query(ReadingBehavior).filter(
                    ReadingBehavior.content_id == content.id
                ).count()
            except Exception as e:
                logger.warning(f"Error calculating read count: {e}")
                read_count = 0

        if 5 <= read_count <= 50:  # Sweet spot for serendipity
            factors["optimal_popularity"] = True
            factors["read_count"] = read_count

        return factors

    async def _find_users_with_similar_content(
        self,
        content_id: str,
        user_id: str,
        db: Session
    ) -> List[str]:
        """Find users who have read similar content."""
        # Get users who read this content
        content_readers = db.query(ReadingBehavior.user_id).filter(
            and_(
                ReadingBehavior.content_id == content_id,
                ReadingBehavior.user_id != user_id
            )
        ).distinct().all()

        return [reader.user_id for reader in content_readers]

    def _generate_discovery_reason(
        self,
        content: ContentItem,
        user_patterns: Dict,
        bridging_topics: List[str],
        serendipity_factors: Dict
    ) -> str:
        """Generate human-readable reason for discovery recommendation."""
        reasons = []

        # Bridging topic reasons
        if bridging_topics:
            if len(bridging_topics) == 1:
                reasons.append(
                    f"explores {bridging_topics[0]} which connects to your interests")
            else:
                reasons.append(
                    f"bridges to your interests through {', '.join(bridging_topics[:2])}")

        # Content type exploration
        content_type = content.content_metadata.get("content_type", "unknown")
        if content_type not in user_patterns["established_content_types"]:
            reasons.append(f"introduces you to {content_type} content")

        # Serendipity reasons
        if serendipity_factors.get("recently_added"):
            reasons.append("is newly available content")

        if serendipity_factors.get("collaborative_discovery"):
            reasons.append("is enjoyed by readers with similar tastes")

        # Default reason
        if not reasons:
            reasons.append(
                "offers a fresh perspective outside your usual reading habits")

        return f"This content {' and '.join(reasons)}."

    def _rank_discovery_recommendations(
        self,
        recommendations: List[Dict],
        limit: int
    ) -> List[Dict]:
        """Rank and filter discovery recommendations."""
        # Calculate combined discovery score
        for rec in recommendations:
            combined_score = (
                rec["divergence_score"] * 0.4 +
                rec["accessibility_score"] * 0.3 +
                len(rec["bridging_topics"]) * 0.1 +
                len(rec["serendipity_factors"]) * 0.2
            )
            rec["combined_discovery_score"] = combined_score

        # Sort by combined score
        sorted_recs = sorted(
            recommendations,
            key=lambda x: x["combined_discovery_score"],
            reverse=True
        )

        # Apply diversity filtering for discovery
        final_recs = []
        used_topics = set()
        used_content_types = set()

        for rec in sorted_recs:
            if len(final_recs) >= limit:
                break

            # Check diversity
            analysis = rec.get("analysis", {})
            content_topics = set(t.get("topic", "")
                                 for t in analysis.get("topics", []))
            content_type = rec.get("metadata", {}).get(
                "content_type", "unknown")

            # Ensure diversity in discovery recommendations
            topic_overlap = len(content_topics & used_topics)
            if topic_overlap <= 1 and content_type not in used_content_types:
                final_recs.append(rec)
                used_topics.update(content_topics)
                used_content_types.add(content_type)
            elif len(final_recs) < limit // 2:
                # Allow some overlap if we don't have enough diverse recommendations
                final_recs.append(rec)

        return final_recs

    async def _store_discovery_recommendation(
        self,
        user_id: str,
        content_id: str,
        discovery_data: Dict,
        db: Session
    ) -> None:
        """Store discovery recommendation for tracking and analysis."""
        discovery_rec = DiscoveryRecommendation(
            content_id=content_id,
            user_id=user_id,
            divergence_score=discovery_data["divergence_score"],
            bridging_topics=discovery_data["bridging_topics"],
            discovery_reason=discovery_data["discovery_reason"],
            created_at=datetime.utcnow()
        )

        db.add(discovery_rec)
        # Note: commit will be handled by the calling function

    async def track_discovery_response(
        self,
        user_id: str,
        content_id: str,
        response: str,
        db: Session = None
    ) -> None:
        """Track user response to discovery recommendation."""
        if not db:
            # Use context manager for database session
            from src.services.database import db_service
            with db_service.get_session() as db:
                await self._track_discovery_response_with_session(user_id, content_id, response, db)
        else:
            await self._track_discovery_response_with_session(user_id, content_id, response, db)

    async def _track_discovery_response_with_session(
        self,
        user_id: str,
        content_id: str,
        response: str,
        db: Session
    ) -> None:
        """Internal method to track discovery response with provided session."""
        try:
            # Find the discovery recommendation
            discovery_rec = db.query(DiscoveryRecommendation).filter(
                and_(
                    DiscoveryRecommendation.user_id == user_id,
                    DiscoveryRecommendation.content_id == content_id
                )
            ).order_by(desc(DiscoveryRecommendation.created_at)).first()

            if discovery_rec:
                discovery_rec.user_response = response
                discovery_rec.response_timestamp = datetime.utcnow()
                db.commit()

                logger.info(
                    f"Tracked discovery response for user {user_id}, content {content_id}: {response}")

        except Exception as e:
            logger.error(f"Error tracking discovery response: {e}")
            db.rollback()
            raise

    async def _get_all_available_topics(self, db: Session) -> Set[str]:
        """Get all available topics from content analysis."""
        # This would be optimized with a topics cache in production
        content_items = db.query(ContentItem).filter(
            ContentItem.analysis.isnot(None)
        ).limit(1000).all()

        all_topics = set()
        for content in content_items:
            if content.analysis and "topics" in content.analysis:
                for topic_data in content.analysis["topics"]:
                    topic = topic_data.get("topic", "")
                    if topic:
                        all_topics.add(topic)

        return all_topics

    async def _get_all_content_types(self, db: Session) -> Set[str]:
        """Get all available content types."""
        # Query content items and extract content types from metadata
        content_items = db.query(ContentItem).all()

        content_types = set()
        for item in content_items:
            if item.content_metadata and "content_type" in item.content_metadata:
                content_types.add(item.content_metadata["content_type"])

        return content_types


# Global instance
discovery_engine = DiscoveryModeEngine()
