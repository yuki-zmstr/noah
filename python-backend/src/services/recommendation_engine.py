"""Contextual recommendation engine for personalized content suggestions."""

import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from collections import defaultdict
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func, or_

from src.models.user_profile import UserProfile, ReadingBehavior, PreferenceSnapshot
from src.models.content import ContentItem, DiscoveryRecommendation
from src.schemas.user_profile import PreferenceModel, LanguageReadingLevels, ReadingContext
from src.schemas.content import ContentAnalysis
from src.services.user_profile_service import user_profile_engine
from src.services.database import db_service

logger = logging.getLogger(__name__)


class ContextualRecommendationEngine:
    """Engine for generating contextual content recommendations."""

    def __init__(self):
        """Initialize the recommendation engine."""
        self.diversity_threshold = 0.3  # Minimum diversity score for recommendations
        self.max_similar_content = 0.4  # Maximum proportion of similar content
        self.context_weight = 0.3  # Weight for contextual factors
        self.preference_weight = 0.5  # Weight for user preferences
        self.reading_level_weight = 0.2  # Weight for reading level matching

        # Time-based preference modifiers
        self.time_preferences = {
            "morning": {"focus": 1.2, "light_reading": 0.8},
            "afternoon": {"educational": 1.1, "technical": 1.0},
            "evening": {"fiction": 1.3, "relaxing": 1.2},
            "night": {"light_reading": 1.4, "complex": 0.6}
        }

        # Mood-based content filtering
        self.mood_filters = {
            "focused": {"complexity_boost": 0.2, "length_preference": "long"},
            "relaxed": {"complexity_boost": -0.1, "length_preference": "medium"},
            "curious": {"diversity_boost": 0.3, "discovery_weight": 1.5},
            "tired": {"complexity_boost": -0.3, "length_preference": "short"}
        }

    async def generate_contextual_recommendations(
        self,
        user_id: str,
        context: Optional[ReadingContext] = None,
        limit: int = 10,
        language: Optional[str] = None,
        db: Session = None
    ) -> List[Dict]:
        """
        Generate contextual recommendations for a user.

        Args:
            user_id: User identifier
            context: Reading context (time, mood, available time, etc.)
            limit: Maximum number of recommendations
            language: Preferred language filter
            db: Database session

        Returns:
            List of recommendation dictionaries with scores and explanations
        """
        logger.info(
            f"Generating contextual recommendations for user {user_id}")

        if not db:
            db = db_service.get_session()

        try:
            # Get user profile
            profile = await user_profile_engine.get_or_create_profile(user_id, db)
            preferences = PreferenceModel(**profile.preferences)
            reading_levels = LanguageReadingLevels(**profile.reading_levels)

            # Infer context if not provided
            if not context:
                context = await self._infer_context_from_patterns(user_id, db)

            # Get candidate content
            candidates = await self._get_candidate_content(
                user_id, language, reading_levels, db
            )

            if not candidates:
                logger.warning(
                    f"No candidate content found for user {user_id}")
                return []

            # Score candidates based on multiple factors
            scored_recommendations = []
            for content in candidates:
                score_data = await self._calculate_recommendation_score(
                    content, preferences, reading_levels, context, user_id, db
                )

                if score_data["total_score"] > 0.1:  # Minimum threshold
                    scored_recommendations.append({
                        "content_id": content.id,
                        "title": content.title,
                        "language": content.language,
                        "metadata": content.content_metadata,
                        "analysis": content.analysis,
                        "recommendation_score": score_data["total_score"],
                        "score_breakdown": score_data["breakdown"],
                        "recommendation_reason": score_data["explanation"],
                        "contextual_factors": score_data["contextual_factors"]
                    })

            # Apply diversity filtering
            diverse_recommendations = self._apply_diversity_filtering(
                scored_recommendations, limit
            )

            # Sort by score and return top recommendations
            final_recommendations = sorted(
                diverse_recommendations,
                key=lambda x: x["recommendation_score"],
                reverse=True
            )[:limit]

            logger.info(
                f"Generated {len(final_recommendations)} recommendations for user {user_id}")
            return final_recommendations

        except Exception as e:
            logger.error(
                f"Error generating recommendations for user {user_id}: {e}")
            raise

    async def _get_candidate_content(
        self,
        user_id: str,
        language: Optional[str],
        reading_levels: LanguageReadingLevels,
        db: Session
    ) -> List[ContentItem]:
        """Get candidate content for recommendations."""
        # Get user's reading history to avoid duplicates
        read_content_ids = set()
        user_behaviors = db.query(ReadingBehavior).filter(
            ReadingBehavior.user_id == user_id
        ).all()

        for behavior in user_behaviors:
            if behavior.completion_rate and behavior.completion_rate > 0.8:
                read_content_ids.add(behavior.content_id)

        # Build query for candidate content
        query = db.query(ContentItem)

        # Filter by language if specified
        if language:
            query = query.filter(ContentItem.language == language)

        # Exclude already read content
        if read_content_ids:
            query = query.filter(~ContentItem.id.in_(read_content_ids))

        # Get content with analysis data
        query = query.filter(ContentItem.analysis.isnot(None))

        # Limit to reasonable number for processing
        candidates = query.limit(100).all()

        # Filter by reading level appropriateness
        filtered_candidates = []
        for content in candidates:
            if await self._is_reading_level_appropriate(content, reading_levels):
                filtered_candidates.append(content)

        return filtered_candidates

    async def _is_reading_level_appropriate(
        self,
        content: ContentItem,
        reading_levels: LanguageReadingLevels
    ) -> bool:
        """Check if content reading level is appropriate for user."""
        if not content.analysis:
            return True  # Include if no analysis available

        analysis = ContentAnalysis(**content.analysis)
        content_language = content.language

        if content_language == "english":
            user_level = reading_levels.english.get("level", 8.0)
            content_level = analysis.reading_level.get("flesch_kincaid", 8.0)

            # Allow content within 2 grade levels of user's level
            return abs(content_level - user_level) <= 2.0

        elif content_language == "japanese":
            user_level = reading_levels.japanese.get("level", 0.3)
            content_level = analysis.reading_level.get("kanji_density", 0.3)

            # Allow content within 0.2 kanji density difference
            return abs(content_level - user_level) <= 0.2

        return True

    async def _calculate_recommendation_score(
        self,
        content: ContentItem,
        preferences: PreferenceModel,
        reading_levels: LanguageReadingLevels,
        context: ReadingContext,
        user_id: str,
        db: Session
    ) -> Dict:
        """Calculate comprehensive recommendation score for content."""
        analysis = ContentAnalysis(
            **content.analysis) if content.analysis else None

        # Initialize score components
        interest_score = 0.0
        reading_level_score = 0.0
        contextual_score = 0.0

        score_breakdown = {}
        contextual_factors = {}

        # 1. Calculate interest score based on topic preferences
        if analysis and analysis.topics:
            topic_scores = []
            for topic_data in analysis.topics:
                topic = topic_data.get("topic", "")
                topic_confidence = topic_data.get("confidence", 0.5)

                # Find matching user preference
                user_topic_weight = 0.0
                for pref_topic in preferences.topics:
                    if pref_topic.get("topic") == topic:
                        user_topic_weight = pref_topic.get("weight", 0.0)
                        break

                topic_score = user_topic_weight * topic_confidence
                topic_scores.append(topic_score)

            interest_score = np.mean(topic_scores) if topic_scores else 0.0
            score_breakdown["interest"] = interest_score

        # 2. Calculate reading level appropriateness score
        reading_level_score = await self._calculate_reading_level_score(
            content, reading_levels
        )
        score_breakdown["reading_level"] = reading_level_score

        # 3. Calculate contextual score
        contextual_score, contextual_factors = await self._calculate_contextual_score(
            content, context, preferences
        )
        score_breakdown["contextual"] = contextual_score

        # 4. Calculate time-based score
        time_score = self._calculate_time_based_score(content, context)
        score_breakdown["time_based"] = time_score
        contextual_factors["time_factors"] = time_score

        # 5. Calculate mood-based score
        mood_score = self._calculate_mood_based_score(content, context)
        score_breakdown["mood_based"] = mood_score
        contextual_factors["mood_factors"] = mood_score

        # Combine scores with weights
        total_score = (
            interest_score * self.preference_weight +
            reading_level_score * self.reading_level_weight +
            (contextual_score + time_score + mood_score) * self.context_weight
        )

        # Generate explanation
        explanation = self._generate_recommendation_explanation(
            content, score_breakdown, contextual_factors
        )

        return {
            "total_score": max(0.0, min(1.0, total_score)),
            "breakdown": score_breakdown,
            "contextual_factors": contextual_factors,
            "explanation": explanation
        }

    async def _calculate_reading_level_score(
        self,
        content: ContentItem,
        reading_levels: LanguageReadingLevels
    ) -> float:
        """Calculate reading level appropriateness score."""
        if not content.analysis:
            return 0.5  # Neutral score if no analysis

        analysis = ContentAnalysis(**content.analysis)

        if content.language == "english":
            user_level = reading_levels.english.get("level", 8.0)
            content_level = analysis.reading_level.get("flesch_kincaid", 8.0)

            # Optimal when content is slightly above user level
            level_diff = content_level - user_level
            if -1.0 <= level_diff <= 1.5:
                return 1.0  # Perfect match
            elif -2.0 <= level_diff <= 3.0:
                return 0.7  # Good match
            else:
                return 0.3  # Poor match

        elif content.language == "japanese":
            user_level = reading_levels.japanese.get("level", 0.3)
            content_level = analysis.reading_level.get("kanji_density", 0.3)

            level_diff = content_level - user_level
            if -0.1 <= level_diff <= 0.15:
                return 1.0
            elif -0.2 <= level_diff <= 0.25:
                return 0.7
            else:
                return 0.3

        return 0.5

    async def _calculate_contextual_score(
        self,
        content: ContentItem,
        context: ReadingContext,
        preferences: PreferenceModel
    ) -> Tuple[float, Dict]:
        """Calculate contextual appropriateness score."""
        contextual_score = 0.0
        factors = {}

        if not context:
            return 0.5, factors

        # Available time factor
        if context.available_time:
            estimated_time = content.content_metadata.get(
                "estimated_reading_time", 10)
            time_ratio = context.available_time / max(estimated_time, 1)

            if 0.8 <= time_ratio <= 1.5:
                time_factor = 1.0
            elif 0.5 <= time_ratio <= 2.0:
                time_factor = 0.7
            else:
                time_factor = 0.3

            contextual_score += time_factor * 0.4
            factors["time_match"] = time_factor

        # Device type factor
        if context.device_type:
            device_preferences = {
                "mobile": {"short_content": 1.2, "visual_content": 1.1},
                "tablet": {"medium_content": 1.1, "interactive": 1.2},
                "desktop": {"long_content": 1.2, "technical": 1.1}
            }

            device_factor = 0.5  # Default
            if context.device_type in device_preferences:
                # This would be enhanced with actual content type analysis
                device_factor = 0.8  # Simplified for now

            contextual_score += device_factor * 0.3
            factors["device_match"] = device_factor

        # Location factor
        if context.location:
            location_preferences = {
                "home": {"relaxed_reading": 1.2},
                "commute": {"short_articles": 1.3},
                "office": {"professional_content": 1.1}
            }

            location_factor = 0.7  # Default positive
            contextual_score += location_factor * 0.3
            factors["location_match"] = location_factor

        return min(1.0, contextual_score), factors

    def _calculate_time_based_score(self, content: ContentItem, context: ReadingContext) -> float:
        """Calculate time-of-day based score."""
        if not context or not context.time_of_day:
            return 0.5

        time_of_day = context.time_of_day.lower()
        content_type = content.content_metadata.get("content_type", "unknown")

        # Get time preferences
        time_prefs = self.time_preferences.get(time_of_day, {})

        score = 0.5  # Base score

        # Apply time-based modifiers
        if content_type in time_prefs:
            score *= time_prefs[content_type]

        # General time-based rules
        if time_of_day == "morning" and "educational" in content.content_metadata.get("tags", []):
            score *= 1.1
        elif time_of_day == "evening" and "fiction" in content.content_metadata.get("tags", []):
            score *= 1.2
        elif time_of_day == "night":
            # Prefer shorter, lighter content at night
            reading_time = content.content_metadata.get(
                "estimated_reading_time", 10)
            if reading_time <= 15:
                score *= 1.2
            else:
                score *= 0.8

        return min(1.0, score)

    def _calculate_mood_based_score(self, content: ContentItem, context: ReadingContext) -> float:
        """Calculate mood-based score."""
        if not context or not context.user_mood:
            return 0.5

        mood = context.user_mood.lower()
        mood_filter = self.mood_filters.get(mood, {})

        score = 0.5  # Base score

        # Apply complexity adjustments
        if "complexity_boost" in mood_filter and content.analysis:
            analysis = ContentAnalysis(**content.analysis)
            complexity = analysis.complexity.get("overall", 0.5)

            adjusted_complexity = complexity + mood_filter["complexity_boost"]
            if 0.3 <= adjusted_complexity <= 0.7:  # Optimal complexity range
                score *= 1.2
            else:
                score *= 0.8

        # Apply length preferences
        if "length_preference" in mood_filter:
            reading_time = content.content_metadata.get(
                "estimated_reading_time", 10)
            pref = mood_filter["length_preference"]

            if pref == "short" and reading_time <= 10:
                score *= 1.3
            elif pref == "medium" and 10 < reading_time <= 30:
                score *= 1.2
            elif pref == "long" and reading_time > 30:
                score *= 1.1

        return min(1.0, score)

    def _apply_diversity_filtering(self, recommendations: List[Dict], limit: int) -> List[Dict]:
        """Apply diversity filtering to prevent filter bubbles."""
        if len(recommendations) <= limit:
            return recommendations

        # Sort by score first
        sorted_recs = sorted(
            recommendations, key=lambda x: x["recommendation_score"], reverse=True)

        # Select diverse recommendations
        selected = []
        topic_counts = defaultdict(int)
        content_type_counts = defaultdict(int)

        max_similar = int(limit * self.max_similar_content)

        for rec in sorted_recs:
            if len(selected) >= limit:
                break

            # Check diversity constraints
            analysis = rec.get("analysis", {})
            topics = [t.get("topic", "") for t in analysis.get("topics", [])]
            content_type = rec.get("metadata", {}).get(
                "content_type", "unknown")

            # Check if adding this recommendation maintains diversity
            topic_ok = all(topic_counts[topic] <
                           max_similar for topic in topics)
            type_ok = content_type_counts[content_type] < max_similar

            if topic_ok and type_ok:
                selected.append(rec)
                for topic in topics:
                    topic_counts[topic] += 1
                content_type_counts[content_type] += 1
            elif len(selected) < limit // 2:
                # Allow some non-diverse content if we don't have enough recommendations
                selected.append(rec)

        return selected

    def _generate_recommendation_explanation(
        self,
        content: ContentItem,
        score_breakdown: Dict,
        contextual_factors: Dict
    ) -> str:
        """Generate human-readable explanation for recommendation."""
        explanations = []

        # Interest-based explanation
        if score_breakdown.get("interest", 0) > 0.6:
            explanations.append("matches your reading interests")
        elif score_breakdown.get("interest", 0) > 0.3:
            explanations.append("aligns with some of your preferences")

        # Reading level explanation
        if score_breakdown.get("reading_level", 0) > 0.8:
            explanations.append("is at an ideal difficulty level for you")
        elif score_breakdown.get("reading_level", 0) > 0.6:
            explanations.append("matches your reading level well")

        # Contextual explanations
        if contextual_factors.get("time_match", 0) > 0.8:
            explanations.append("fits your available reading time")

        if contextual_factors.get("mood_factors", 0) > 0.7:
            explanations.append("suits your current mood")

        # Default explanation if no specific factors stand out
        if not explanations:
            explanations.append("is recommended based on your reading profile")

        return f"This content {' and '.join(explanations)}."

    async def _infer_context_from_patterns(self, user_id: str, db: Session) -> ReadingContext:
        """Infer reading context from user's historical patterns."""
        # Get recent reading behaviors
        recent_behaviors = db.query(ReadingBehavior).filter(
            and_(
                ReadingBehavior.user_id == user_id,
                ReadingBehavior.created_at >= datetime.utcnow() - timedelta(days=30)
            )
        ).order_by(desc(ReadingBehavior.created_at)).limit(20).all()

        # Analyze patterns to infer context
        current_hour = datetime.utcnow().hour

        # Infer time of day
        if 6 <= current_hour < 12:
            time_of_day = "morning"
        elif 12 <= current_hour < 17:
            time_of_day = "afternoon"
        elif 17 <= current_hour < 22:
            time_of_day = "evening"
        else:
            time_of_day = "night"

        # Infer typical reading time from patterns
        avg_reading_time = 15  # Default
        if recent_behaviors:
            reading_times = []
            for behavior in recent_behaviors:
                if behavior.end_time and behavior.start_time:
                    duration = (behavior.end_time -
                                behavior.start_time).total_seconds() / 60
                    reading_times.append(duration)

            if reading_times:
                avg_reading_time = int(np.mean(reading_times))

        # Infer device type (simplified - would use actual device detection)
        device_type = "desktop"  # Default assumption

        return ReadingContext(
            time_of_day=time_of_day,
            device_type=device_type,
            available_time=avg_reading_time,
            user_mood=None  # Would be inferred from more sophisticated analysis
        )


# Global instance
contextual_recommendation_engine = ContextualRecommendationEngine()
