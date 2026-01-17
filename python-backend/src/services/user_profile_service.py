"""User profile engine for preference learning and reading level assessment."""

import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from collections import defaultdict
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func

from src.models.user_profile import UserProfile, ReadingBehavior, PreferenceSnapshot
from src.models.content import ContentItem
from src.schemas.user_profile import (
    UserProfileCreate, UserProfileResponse, PreferenceModel,
    LanguageReadingLevels, TopicPreference, ReadingContext
)
from src.services.database import db_service

logger = logging.getLogger(__name__)


class UserProfileEngine:
    """Engine for user profile management, preference learning, and reading level assessment."""

    def __init__(self):
        """Initialize the user profile engine."""
        self.preference_decay_factor = 0.95  # How quickly old preferences fade
        self.confidence_threshold = 0.6  # Minimum confidence for reliable preferences
        self.evolution_window_days = 30  # Days to look back for preference evolution

        # Reading level thresholds for English (Flesch-Kincaid grade levels)
        self.english_levels = {
            "beginner": (0, 6),
            "intermediate": (6, 10),
            "advanced": (10, 14),
            "expert": (14, 20)
        }

        # Japanese reading levels based on kanji density and complexity
        self.japanese_levels = {
            "beginner": (0, 0.2),  # Low kanji density
            "intermediate": (0.2, 0.4),
            "advanced": (0.4, 0.6),
            "expert": (0.6, 1.0)
        }

    async def get_or_create_profile(self, user_id: str, db: Session) -> UserProfile:
        """Get existing user profile or create a new one with defaults."""
        profile = db.query(UserProfile).filter(
            UserProfile.user_id == user_id).first()

        if not profile:
            # Create default profile
            default_preferences = PreferenceModel(
                topics=[],
                content_types=[],
                contextual_preferences=[],
                evolution_history=[]
            )

            default_reading_levels = LanguageReadingLevels(
                english={"level": 8.0, "confidence": 0.3,
                         "assessment_count": 0},
                japanese={"level": 0.3, "confidence": 0.3,
                          "assessment_count": 0}
            )

            profile = UserProfile(
                user_id=user_id,
                preferences=default_preferences.dict(),
                reading_levels=default_reading_levels.dict(),
                created_at=datetime.utcnow(),
                last_updated=datetime.utcnow()
            )

            db.add(profile)
            db.commit()
            db.refresh(profile)

            logger.info(f"Created new user profile for {user_id}")

        return profile

    async def update_reading_behavior(self, user_id: str, content_id: str,
                                      behavior_data: Dict, db: Session) -> ReadingBehavior:
        """Record reading behavior and update user profile."""
        # Create reading behavior record
        behavior = ReadingBehavior(
            content_id=content_id,
            user_id=user_id,
            session_id=behavior_data.get("session_id"),
            start_time=behavior_data.get("start_time", datetime.utcnow()),
            end_time=behavior_data.get("end_time"),
            completion_rate=behavior_data.get("completion_rate", 0.0),
            reading_speed=behavior_data.get("reading_speed", 0.0),
            pause_patterns=behavior_data.get("pause_patterns", []),
            interactions=behavior_data.get("interactions", []),
            context=behavior_data.get("context", {}),
            created_at=datetime.utcnow()
        )

        db.add(behavior)

        # Update user profile based on this behavior
        await self._update_profile_from_behavior(user_id, behavior, db)

        db.commit()
        db.refresh(behavior)

        logger.info(
            f"Recorded reading behavior for user {user_id}, content {content_id}")
        return behavior

    async def assess_reading_level(self, user_id: str, language: str,
                                   content_analysis: Dict, performance_metrics: Dict,
                                   db: Session) -> Dict:
        """Assess and update user's reading level for a specific language."""
        profile = await self.get_or_create_profile(user_id, db)
        current_levels = LanguageReadingLevels(**profile.reading_levels)

        # Get current level for the language
        if language == "english":
            current_level_data = current_levels.english
            content_difficulty = content_analysis.get(
                "reading_level", {}).get("flesch_kincaid", 8.0)
        elif language == "japanese":
            current_level_data = current_levels.japanese
            content_difficulty = content_analysis.get(
                "reading_level", {}).get("kanji_density", 0.3)
        else:
            raise ValueError(f"Unsupported language: {language}")

        # Calculate performance score based on metrics
        performance_score = self._calculate_performance_score(
            performance_metrics)

        # Update reading level based on performance
        new_level_data = self._update_reading_level(
            current_level_data, content_difficulty, performance_score
        )

        # Update profile
        if language == "english":
            current_levels.english = new_level_data
        else:
            current_levels.japanese = new_level_data

        profile.reading_levels = current_levels.dict()
        profile.last_updated = datetime.utcnow()

        db.commit()

        logger.info(
            f"Updated {language} reading level for user {user_id}: {new_level_data}")
        return new_level_data

    async def update_preferences_from_feedback(self, user_id: str, content_id: str,
                                               feedback_data: Dict, db: Session) -> None:
        """Update user preferences based on explicit or implicit feedback."""
        profile = await self.get_or_create_profile(user_id, db)
        content = db.query(ContentItem).filter(
            ContentItem.id == content_id).first()

        if not content or not content.analysis:
            logger.warning(f"Content {content_id} not found or lacks analysis")
            return

        # Extract content topics and features
        content_topics = content.analysis.get("topics", [])
        content_type = content.content_metadata.get("content_type", "unknown")

        # Process feedback
        feedback_type = feedback_data.get("type", "implicit")
        feedback_value = feedback_data.get("value", 0.0)  # -1 to 1 scale

        # Update topic preferences
        await self._update_topic_preferences(
            profile, content_topics, feedback_value, feedback_type, db
        )

        # Update content type preferences
        await self._update_content_type_preferences(
            profile, content_type, feedback_value, feedback_type, db
        )

        # Update contextual preferences if context provided
        if "context" in feedback_data:
            await self._update_contextual_preferences(
                profile, feedback_data["context"], feedback_value, db
            )

        profile.last_updated = datetime.utcnow()
        db.commit()

        logger.info(
            f"Updated preferences for user {user_id} based on {feedback_type} feedback")

    async def track_preference_evolution(self, user_id: str, db: Session) -> Dict:
        """Analyze and track preference evolution over time."""
        profile = await self.get_or_create_profile(user_id, db)

        # Get recent preference snapshots
        cutoff_date = datetime.utcnow() - timedelta(days=self.evolution_window_days)
        recent_snapshots = db.query(PreferenceSnapshot).filter(
            and_(
                PreferenceSnapshot.user_id == user_id,
                PreferenceSnapshot.timestamp >= cutoff_date
            )
        ).order_by(desc(PreferenceSnapshot.timestamp)).all()

        if len(recent_snapshots) < 2:
            # Not enough data for evolution analysis
            return {"evolution_detected": False, "trends": []}

        # Analyze trends
        evolution_analysis = self._analyze_preference_trends(recent_snapshots)

        # Create new snapshot if significant changes detected
        if evolution_analysis["significant_changes"]:
            await self._create_preference_snapshot(user_id, profile, db)

        return evolution_analysis

    async def get_preference_transparency(self, user_id: str, db: Session) -> Dict:
        """Generate transparent explanation of learned preferences."""
        profile = await self.get_or_create_profile(user_id, db)
        preferences = PreferenceModel(**profile.preferences)
        reading_levels = LanguageReadingLevels(**profile.reading_levels)

        # Get recent behavior data for explanations
        recent_behaviors = db.query(ReadingBehavior).filter(
            and_(
                ReadingBehavior.user_id == user_id,
                ReadingBehavior.created_at >= datetime.utcnow() - timedelta(days=90)
            )
        ).order_by(desc(ReadingBehavior.created_at)).limit(50).all()

        transparency_data = {
            "user_id": user_id,
            "profile_created": profile.created_at.isoformat(),
            "last_updated": profile.last_updated.isoformat(),
            "data_points_analyzed": len(recent_behaviors),
            "reading_levels": {
                "english": {
                    **reading_levels.english,
                    "explanation": self._explain_reading_level("english", reading_levels.english)
                },
                "japanese": {
                    **reading_levels.japanese,
                    "explanation": self._explain_reading_level("japanese", reading_levels.japanese)
                }
            },
            "topic_preferences": self._explain_topic_preferences(preferences.topics, recent_behaviors),
            "content_type_preferences": self._explain_content_type_preferences(
                preferences.content_types, recent_behaviors
            ),
            "contextual_patterns": self._explain_contextual_preferences(
                preferences.contextual_preferences, recent_behaviors
            ),
            "preference_evolution": self._explain_preference_evolution(preferences.evolution_history)
        }

        return transparency_data

    async def get_collaborative_filtering_data(self, user_id: str, db: Session) -> Dict:
        """Get data for collaborative filtering recommendations."""
        profile = await self.get_or_create_profile(user_id, db)

        # Get user's reading history
        user_behaviors = db.query(ReadingBehavior).filter(
            ReadingBehavior.user_id == user_id
        ).all()

        # Get similar users based on reading patterns
        similar_users = await self._find_similar_users(user_id, user_behaviors, db)

        # Get content-based similarity data
        content_similarities = await self._calculate_content_similarities(user_behaviors, db)

        return {
            "user_reading_history": [
                {
                    "content_id": b.content_id,
                    "completion_rate": b.completion_rate,
                    "reading_speed": b.reading_speed,
                    "implicit_rating": self._calculate_implicit_rating(b)
                }
                for b in user_behaviors
            ],
            "similar_users": similar_users,
            "content_similarities": content_similarities,
            "preference_vector": self._create_preference_vector(profile)
        }

    # Private helper methods

    def _calculate_performance_score(self, metrics: Dict) -> float:
        """Calculate performance score from reading metrics."""
        completion_rate = metrics.get("completion_rate", 0.0)
        reading_speed = metrics.get("reading_speed", 0.0)
        pause_frequency = len(metrics.get("pause_patterns", []))
        interaction_count = len(metrics.get("interactions", []))

        # Normalize and weight factors
        completion_weight = 0.4
        speed_weight = 0.3
        pause_weight = 0.2  # Lower pause frequency is better
        interaction_weight = 0.1  # More interactions can indicate engagement

        # Normalize reading speed (assuming 200-300 WPM is average)
        speed_score = min(1.0, max(0.0, (reading_speed - 100) / 200))

        # Normalize pause frequency (fewer pauses is better for comprehension)
        pause_score = max(0.0, 1.0 - (pause_frequency / 10))

        # Normalize interaction count
        interaction_score = min(1.0, interaction_count / 5)

        performance_score = (
            completion_rate * completion_weight +
            speed_score * speed_weight +
            pause_score * pause_weight +
            interaction_score * interaction_weight
        )

        return max(0.0, min(1.0, performance_score))

    def _update_reading_level(self, current_data: Dict, content_difficulty: float,
                              performance_score: float) -> Dict:
        """Update reading level based on performance."""
        current_level = current_data.get("level", 0.0)
        current_confidence = current_data.get("confidence", 0.3)
        assessment_count = current_data.get("assessment_count", 0)

        # Calculate adjustment based on performance
        if performance_score > 0.8:
            # Good performance, can handle more difficulty
            level_adjustment = 0.1 * (content_difficulty - current_level)
        elif performance_score > 0.6:
            # Adequate performance, small adjustment
            level_adjustment = 0.05 * (content_difficulty - current_level)
        else:
            # Poor performance, reduce level estimate
            level_adjustment = -0.1 * abs(content_difficulty - current_level)

        # Update level with momentum
        new_level = current_level + (level_adjustment * 0.3)

        # Update confidence based on consistency
        confidence_adjustment = 0.05 if abs(level_adjustment) < 0.5 else -0.02
        new_confidence = max(
            0.1, min(1.0, current_confidence + confidence_adjustment))

        return {
            "level": new_level,
            "confidence": new_confidence,
            "assessment_count": assessment_count + 1,
            "last_assessment": datetime.utcnow().isoformat()
        }

    async def _update_profile_from_behavior(self, user_id: str, behavior: ReadingBehavior,
                                            db: Session) -> None:
        """Update user profile based on reading behavior."""
        # Calculate implicit feedback from behavior
        implicit_rating = self._calculate_implicit_rating(behavior)

        feedback_data = {
            "type": "implicit",
            "value": implicit_rating,
            "context": behavior.context
        }

        await self.update_preferences_from_feedback(
            user_id, behavior.content_id, feedback_data, db
        )

    def _calculate_implicit_rating(self, behavior: ReadingBehavior) -> float:
        """Calculate implicit rating from reading behavior."""
        completion_rate = behavior.completion_rate or 0.0
        reading_speed = behavior.reading_speed or 0.0

        # Base rating on completion
        rating = completion_rate * 2 - 1  # Scale to -1 to 1

        # Adjust based on reading speed (assuming 200-300 WPM is normal)
        if reading_speed > 0:
            # Normalize to average speed
            speed_factor = min(1.0, reading_speed / 250)
            rating *= speed_factor

        # Adjust based on interactions (more interactions = more engagement)
        interaction_count = len(behavior.interactions or [])
        if interaction_count > 0:
            rating += min(0.2, interaction_count * 0.05)

        return max(-1.0, min(1.0, rating))

    async def _update_topic_preferences(self, profile: UserProfile, content_topics: List[Dict],
                                        feedback_value: float, feedback_type: str, db: Session) -> None:
        """Update topic preferences based on feedback."""
        preferences = PreferenceModel(**profile.preferences)

        # Convert topics list to dict for easier manipulation
        topic_dict = {tp["topic"]: tp for tp in preferences.topics}

        for topic_data in content_topics:
            topic = topic_data.get("topic", "")
            topic_confidence = topic_data.get("confidence", 0.5)

            if topic in topic_dict:
                # Update existing topic preference
                current_weight = topic_dict[topic]["weight"]
                current_confidence = topic_dict[topic]["confidence"]

                # Weighted update based on feedback strength and topic confidence
                weight_adjustment = feedback_value * topic_confidence * 0.1
                new_weight = max(-1.0,
                                 min(1.0, current_weight + weight_adjustment))

                # Update confidence
                confidence_adjustment = 0.05 if abs(
                    weight_adjustment) > 0.05 else 0.02
                new_confidence = min(
                    1.0, current_confidence + confidence_adjustment)

                topic_dict[topic].update({
                    "weight": new_weight,
                    "confidence": new_confidence,
                    "last_updated": datetime.utcnow().isoformat(),
                    "evolution_trend": self._calculate_trend(current_weight, new_weight)
                })
            else:
                # Add new topic preference
                topic_dict[topic] = {
                    "topic": topic,
                    "weight": feedback_value * topic_confidence * 0.5,  # Start conservative
                    "confidence": topic_confidence * 0.5,
                    "last_updated": datetime.utcnow().isoformat(),
                    "evolution_trend": "new"
                }

        # Convert back to list and update profile
        preferences.topics = list(topic_dict.values())
        profile.preferences = preferences.dict()

    async def _update_content_type_preferences(self, profile: UserProfile, content_type: str,
                                               feedback_value: float, feedback_type: str, db: Session) -> None:
        """Update content type preferences."""
        preferences = PreferenceModel(**profile.preferences)

        # Find or create content type preference
        type_dict = {ct["type"]: ct for ct in preferences.content_types}

        if content_type in type_dict:
            current_pref = type_dict[content_type]["preference"]
            adjustment = feedback_value * 0.1
            new_pref = max(-1.0, min(1.0, current_pref + adjustment))

            type_dict[content_type].update({
                "preference": new_pref,
                "last_updated": datetime.utcnow().isoformat()
            })
        else:
            type_dict[content_type] = {
                "type": content_type,
                "preference": feedback_value * 0.5,
                "last_updated": datetime.utcnow().isoformat()
            }

        preferences.content_types = list(type_dict.values())
        profile.preferences = preferences.dict()

    async def _update_contextual_preferences(self, profile: UserProfile, context: Dict,
                                             feedback_value: float, db: Session) -> None:
        """Update contextual preferences."""
        preferences = PreferenceModel(**profile.preferences)

        # Process contextual factors
        ctx_dict = {
            f"{cp['factor']}:{cp.get('value', '')}": cp
            for cp in preferences.contextual_preferences
        }

        for factor, value in context.items():
            if factor in ["time_of_day", "device_type", "location", "user_mood"]:
                factor_key = f"{factor}:{value}"
                if factor_key in ctx_dict:
                    current_weight = ctx_dict[factor_key]["weight"]
                    adjustment = feedback_value * 0.05
                    new_weight = max(-1.0,
                                     min(1.0, current_weight + adjustment))

                    ctx_dict[factor_key].update({
                        "weight": new_weight,
                        "last_updated": datetime.utcnow().isoformat()
                    })
                else:
                    ctx_dict[factor_key] = {
                        "factor": factor,
                        "value": value,
                        "weight": feedback_value * 0.3,
                        "last_updated": datetime.utcnow().isoformat()
                    }

        preferences.contextual_preferences = list(ctx_dict.values())
        profile.preferences = preferences.dict()

    def _calculate_trend(self, old_value: float, new_value: float) -> str:
        """Calculate trend direction."""
        diff = new_value - old_value
        if abs(diff) < 0.05:
            return "stable"
        elif diff > 0:
            return "increasing"
        else:
            return "decreasing"

    async def _create_preference_snapshot(self, user_id: str, profile: UserProfile, db: Session) -> None:
        """Create a preference snapshot for evolution tracking."""
        preferences = PreferenceModel(**profile.preferences)

        # Calculate topic weights for snapshot
        topic_weights = {tp["topic"]: tp["weight"]
                         for tp in preferences.topics}

        # Calculate contextual factors
        contextual_factors = {
            cp["factor"]: cp["weight"] for cp in preferences.contextual_preferences
        }

        # Calculate overall confidence
        topic_confidences = [tp["confidence"]
                             for tp in preferences.topics if "confidence" in tp]
        avg_confidence = sum(topic_confidences) / \
            len(topic_confidences) if topic_confidences else 0.5

        snapshot = PreferenceSnapshot(
            user_id=user_id,
            timestamp=datetime.utcnow(),
            topic_weights=topic_weights,
            reading_level_preference=0.0,  # Could be calculated from reading levels
            contextual_factors=contextual_factors,
            confidence_score=avg_confidence
        )

        db.add(snapshot)
        logger.info(f"Created preference snapshot for user {user_id}")

    def _analyze_preference_trends(self, snapshots: List[PreferenceSnapshot]) -> Dict:
        """Analyze preference evolution trends."""
        if len(snapshots) < 2:
            return {"evolution_detected": False, "trends": []}

        trends = []
        significant_changes = False

        # Compare most recent with previous snapshots
        latest = snapshots[0]
        previous = snapshots[1]

        # Analyze topic weight changes
        for topic, weight in latest.topic_weights.items():
            prev_weight = previous.topic_weights.get(topic, 0.0)
            change = weight - prev_weight

            if abs(change) > 0.2:  # Significant change threshold
                significant_changes = True
                trends.append({
                    "type": "topic",
                    "item": topic,
                    "change": change,
                    "direction": "increasing" if change > 0 else "decreasing",
                    "magnitude": abs(change)
                })

        # Analyze confidence changes
        confidence_change = latest.confidence_score - previous.confidence_score
        if abs(confidence_change) > 0.1:
            trends.append({
                "type": "confidence",
                "item": "overall",
                "change": confidence_change,
                "direction": "increasing" if confidence_change > 0 else "decreasing",
                "magnitude": abs(confidence_change)
            })

        return {
            "evolution_detected": significant_changes,
            "trends": trends,
            "analysis_period": {
                "start": snapshots[-1].timestamp.isoformat(),
                "end": snapshots[0].timestamp.isoformat(),
                "snapshots_analyzed": len(snapshots)
            }
        }

    async def _find_similar_users(self, user_id: str, user_behaviors: List[ReadingBehavior],
                                  db: Session) -> List[Dict]:
        """Find users with similar reading patterns for collaborative filtering."""
        # Get content IDs that this user has read
        user_content_ids = {b.content_id for b in user_behaviors}

        if not user_content_ids:
            return []

        # Find other users who have read similar content
        similar_user_behaviors = db.query(ReadingBehavior).filter(
            and_(
                ReadingBehavior.content_id.in_(user_content_ids),
                ReadingBehavior.user_id != user_id
            )
        ).all()

        # Group by user and calculate similarity scores
        user_similarities = defaultdict(list)
        for behavior in similar_user_behaviors:
            user_similarities[behavior.user_id].append(behavior)

        # Calculate similarity scores
        similar_users = []
        for other_user_id, other_behaviors in user_similarities.items():
            other_content_ids = {b.content_id for b in other_behaviors}

            # Calculate Jaccard similarity
            intersection = len(user_content_ids & other_content_ids)
            union = len(user_content_ids | other_content_ids)
            jaccard_similarity = intersection / union if union > 0 else 0

            if jaccard_similarity > 0.1:  # Minimum similarity threshold
                similar_users.append({
                    "user_id": other_user_id,
                    "similarity_score": jaccard_similarity,
                    "common_content_count": intersection
                })

        # Sort by similarity and return top matches
        similar_users.sort(key=lambda x: x["similarity_score"], reverse=True)
        return similar_users[:10]

    async def _calculate_content_similarities(self, user_behaviors: List[ReadingBehavior],
                                              db: Session) -> Dict:
        """Calculate content-based similarities for recommendations."""
        content_ids = [b.content_id for b in user_behaviors]

        if not content_ids:
            return {}

        # Get content items with analysis
        content_items = db.query(ContentItem).filter(
            ContentItem.id.in_(content_ids)
        ).all()

        similarities = {}
        for content in content_items:
            if content.analysis and "topics" in content.analysis:
                content_topics = {t["topic"]
                                  for t in content.analysis["topics"]}
                similarities[content.id] = {
                    "topics": list(content_topics),
                    "reading_level": content.analysis.get("reading_level", {}),
                    "content_type": content.content_metadata.get("content_type", "unknown")
                }

        return similarities

    def _create_preference_vector(self, profile: UserProfile) -> List[float]:
        """Create a numerical preference vector for similarity calculations."""
        preferences = PreferenceModel(**profile.preferences)

        # Create vector from topic preferences (top 20 topics)
        topic_weights = {tp["topic"]: tp["weight"]
                         for tp in preferences.topics}

        # Get most common topics (this would be from a global topic vocabulary in practice)
        common_topics = ["fiction", "non-fiction", "science", "history", "biography",
                         "mystery", "romance", "fantasy", "technology", "health"]

        vector = [topic_weights.get(topic, 0.0) for topic in common_topics]

        # Add content type preferences
        content_type_weights = {ct["type"]: ct["preference"]
                                for ct in preferences.content_types}
        common_types = ["book", "article", "paper", "blog", "news"]
        vector.extend([content_type_weights.get(ctype, 0.0)
                      for ctype in common_types])

        return vector

    def _explain_reading_level(self, language: str, level_data: Dict) -> str:
        """Generate explanation for reading level assessment."""
        level = level_data.get("level", 0.0)
        confidence = level_data.get("confidence", 0.0)
        assessment_count = level_data.get("assessment_count", 0)

        if language == "english":
            if level < 6:
                level_desc = "elementary"
            elif level < 10:
                level_desc = "middle school"
            elif level < 14:
                level_desc = "high school"
            else:
                level_desc = "college"
        else:  # Japanese
            if level < 0.2:
                level_desc = "basic (hiragana/katakana focus)"
            elif level < 0.4:
                level_desc = "intermediate (common kanji)"
            elif level < 0.6:
                level_desc = "advanced (complex kanji)"
            else:
                level_desc = "expert (literary kanji)"

        confidence_desc = "high" if confidence > 0.7 else "medium" if confidence > 0.4 else "low"

        return (f"Assessed at {level_desc} level based on {assessment_count} reading sessions. "
                f"Confidence in this assessment is {confidence_desc}.")

    def _explain_topic_preferences(self, topics: List[Dict], behaviors: List[ReadingBehavior]) -> List[Dict]:
        """Generate explanations for topic preferences."""
        explanations = []

        for topic_data in sorted(topics, key=lambda x: abs(x.get("weight", 0)), reverse=True)[:10]:
            topic = topic_data.get("topic", "")
            weight = topic_data.get("weight", 0.0)
            confidence = topic_data.get("confidence", 0.0)

            # Count related reading sessions
            related_sessions = sum(1 for b in behaviors
                                   if any(t.get("topic") == topic
                                          for t in (b.content_item.analysis.get("topics", [])
                                                    if hasattr(b, 'content_item') and b.content_item and b.content_item.analysis
                                                    else [])))

            preference_strength = "strong" if abs(
                weight) > 0.6 else "moderate" if abs(weight) > 0.3 else "weak"
            preference_direction = "positive" if weight > 0 else "negative"

            explanation = (f"{preference_strength.title()} {preference_direction} preference for {topic} "
                           f"based on {related_sessions} reading sessions. "
                           f"Confidence: {confidence:.1%}")

            explanations.append({
                "topic": topic,
                "weight": weight,
                "confidence": confidence,
                "explanation": explanation,
                "related_sessions": related_sessions
            })

        return explanations

    def _explain_content_type_preferences(self, content_types: List[Dict],
                                          behaviors: List[ReadingBehavior]) -> List[Dict]:
        """Generate explanations for content type preferences."""
        explanations = []

        for ct_data in content_types:
            content_type = ct_data.get("type", "")
            preference = ct_data.get("preference", 0.0)

            # Count sessions with this content type
            type_sessions = sum(1 for b in behaviors
                                if (hasattr(b, 'content_item') and b.content_item and
                                    b.content_item.content_metadata.get("content_type") == content_type))

            pref_desc = "preferred" if preference > 0.3 else "neutral" if preference > - \
                0.3 else "avoided"

            explanation = f"{content_type.title()} content is {pref_desc} based on {type_sessions} reading sessions."

            explanations.append({
                "content_type": content_type,
                "preference": preference,
                "explanation": explanation,
                "sessions_count": type_sessions
            })

        return explanations

    def _explain_contextual_preferences(self, contextual_prefs: List[Dict],
                                        behaviors: List[ReadingBehavior]) -> List[Dict]:
        """Generate explanations for contextual preferences."""
        explanations = []

        for ctx_data in contextual_prefs:
            factor = ctx_data.get("factor", "")
            value = ctx_data.get("value", "")
            weight = ctx_data.get("weight", 0.0)

            # Count sessions with this context
            ctx_sessions = sum(1 for b in behaviors
                               if b.context and b.context.get(factor) == value)

            weight_desc = "strongly" if abs(weight) > 0.5 else "moderately" if abs(
                weight) > 0.2 else "slightly"
            direction = "favors" if weight > 0 else "avoids"

            explanation = f"{weight_desc.title()} {direction} reading when {factor} is {value} (based on {ctx_sessions} sessions)."

            explanations.append({
                "factor": factor,
                "value": value,
                "weight": weight,
                "explanation": explanation,
                "sessions_count": ctx_sessions
            })

        return explanations

    def _explain_preference_evolution(self, evolution_history: List[Dict]) -> Dict:
        """Generate explanation for preference evolution."""
        if not evolution_history:
            return {"has_evolution": False, "explanation": "No preference evolution data available yet."}

        recent_changes = evolution_history[-5:]  # Last 5 changes

        return {
            "has_evolution": True,
            "recent_changes_count": len(recent_changes),
            "explanation": f"Preferences have evolved over time with {len(evolution_history)} recorded changes. "
            f"Recent trends show adaptation to new content types and topics.",
            "recent_changes": recent_changes
        }


# Global instance
user_profile_engine = UserProfileEngine()
