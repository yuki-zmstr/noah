"""Feedback processing system for explicit and implicit user feedback."""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from enum import Enum
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func

from src.models.user_profile import UserProfile, ReadingBehavior
from src.models.content import ContentItem
from src.schemas.user_profile import PreferenceModel
from src.services.user_profile_service import user_profile_engine
from src.services.database import db_service

logger = logging.getLogger(__name__)


class FeedbackType(Enum):
    """Types of feedback that can be processed."""
    EXPLICIT_RATING = "explicit_rating"
    LIKE_DISLIKE = "like_dislike"
    CONTEXTUAL_COMMENT = "contextual_comment"
    IMPLICIT_COMPLETION = "implicit_completion"
    IMPLICIT_TIME = "implicit_time"
    IMPLICIT_INTERACTION = "implicit_interaction"
    IMPLICIT_RETURN = "implicit_return"


class FeedbackProcessor:
    """Processes various types of user feedback to improve recommendations."""

    def __init__(self):
        """Initialize the feedback processor."""
        self.profile_engine = user_profile_engine

        # Feedback weights for different types
        self.feedback_weights = {
            FeedbackType.EXPLICIT_RATING: 1.0,
            FeedbackType.LIKE_DISLIKE: 0.8,
            FeedbackType.CONTEXTUAL_COMMENT: 0.9,
            FeedbackType.IMPLICIT_COMPLETION: 0.4,
            FeedbackType.IMPLICIT_TIME: 0.3,
            FeedbackType.IMPLICIT_INTERACTION: 0.2,
            FeedbackType.IMPLICIT_RETURN: 0.5
        }

        # Thresholds for implicit feedback interpretation
        self.completion_thresholds = {
            "high": 0.8,
            "medium": 0.5,
            "low": 0.2
        }

        self.time_thresholds = {
            "engaged": 1.2,  # 120% of expected reading time
            "normal": 0.8,   # 80% of expected reading time
            "rushed": 0.5    # 50% of expected reading time
        }

    async def process_explicit_feedback(self, user_id: str, content_id: str,
                                        feedback_data: Dict, db: Session) -> Dict:
        """Process explicit user feedback (ratings, likes, comments)."""
        feedback_type = FeedbackType(
            feedback_data.get("type", "explicit_rating"))

        # Validate and normalize feedback
        normalized_feedback = self._normalize_explicit_feedback(
            feedback_data, feedback_type)

        # Update user preferences
        await self.profile_engine.update_preferences_from_feedback(
            user_id, content_id, normalized_feedback, db
        )

        # Store feedback for transparency
        feedback_record = await self._store_feedback_record(
            user_id, content_id, feedback_type, normalized_feedback, db
        )

        # Generate explanation for the user
        explanation = await self._generate_feedback_explanation(
            user_id, content_id, feedback_type, normalized_feedback, db
        )

        logger.info(
            f"Processed explicit feedback for user {user_id}, content {content_id}")

        return {
            "feedback_processed": True,
            "feedback_type": feedback_type.value,
            "normalized_value": normalized_feedback["value"],
            "explanation": explanation,
            "profile_updated": True
        }

    async def process_implicit_feedback(self, user_id: str, content_id: str,
                                        behavior_data: Dict, db: Session) -> Dict:
        """Process implicit feedback from reading behavior."""
        # Analyze different aspects of behavior
        feedback_signals = []

        # Completion rate feedback
        completion_feedback = self._analyze_completion_feedback(behavior_data)
        if completion_feedback:
            feedback_signals.append(completion_feedback)

        # Reading time feedback
        time_feedback = self._analyze_time_feedback(behavior_data)
        if time_feedback:
            feedback_signals.append(time_feedback)

        # Interaction feedback
        interaction_feedback = self._analyze_interaction_feedback(
            behavior_data)
        if interaction_feedback:
            feedback_signals.append(interaction_feedback)

        # Return behavior feedback (if user returns to content)
        return_feedback = await self._analyze_return_behavior(user_id, content_id, db)
        if return_feedback:
            feedback_signals.append(return_feedback)

        # Combine signals into overall implicit feedback
        combined_feedback = self._combine_implicit_signals(feedback_signals)

        if combined_feedback:
            # Update user preferences
            await self.profile_engine.update_preferences_from_feedback(
                user_id, content_id, combined_feedback, db
            )

            # Store implicit feedback record
            await self._store_feedback_record(
                user_id, content_id, FeedbackType.IMPLICIT_COMPLETION,
                combined_feedback, db
            )

        logger.info(
            f"Processed implicit feedback for user {user_id}, content {content_id}")

        return {
            "feedback_processed": len(feedback_signals) > 0,
            "signals_detected": len(feedback_signals),
            "signal_types": [signal["type"] for signal in feedback_signals],
            "combined_value": combined_feedback.get("value", 0.0) if combined_feedback else 0.0,
            "profile_updated": combined_feedback is not None
        }

    async def analyze_feedback_patterns(self, user_id: str, db: Session,
                                        days_back: int = 30) -> Dict:
        """Analyze user's feedback patterns for insights."""
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)

        # Get recent reading behaviors
        recent_behaviors = db.query(ReadingBehavior).filter(
            and_(
                ReadingBehavior.user_id == user_id,
                ReadingBehavior.created_at >= cutoff_date
            )
        ).order_by(desc(ReadingBehavior.created_at)).all()

        if not recent_behaviors:
            return {"patterns_found": False, "message": "Insufficient feedback data"}

        # Analyze patterns
        patterns = {
            "total_sessions": len(recent_behaviors),
            "completion_patterns": self._analyze_completion_patterns(recent_behaviors),
            "time_patterns": self._analyze_time_patterns(recent_behaviors),
            "interaction_patterns": self._analyze_interaction_patterns(recent_behaviors),
            "content_type_patterns": await self._analyze_content_type_patterns(recent_behaviors, db),
            "contextual_patterns": self._analyze_contextual_patterns(recent_behaviors),
            "engagement_trends": self._analyze_engagement_trends(recent_behaviors)
        }

        # Generate insights
        insights = self._generate_pattern_insights(patterns)

        return {
            "patterns_found": True,
            "analysis_period": f"{days_back} days",
            "patterns": patterns,
            "insights": insights,
            "recommendations": self._generate_feedback_recommendations(patterns)
        }

    async def get_feedback_transparency(self, user_id: str, db: Session) -> Dict:
        """Provide transparency into how feedback has influenced preferences."""
        profile = await self.profile_engine.get_or_create_profile(user_id, db)

        # Get recent feedback records (would need to implement feedback storage)
        recent_behaviors = db.query(ReadingBehavior).filter(
            and_(
                ReadingBehavior.user_id == user_id,
                ReadingBehavior.created_at >= datetime.utcnow() - timedelta(days=90)
            )
        ).order_by(desc(ReadingBehavior.created_at)).limit(50).all()

        # Analyze feedback impact
        feedback_impact = await self._analyze_feedback_impact(user_id, recent_behaviors, db)

        # Generate explanations
        explanations = self._generate_transparency_explanations(
            feedback_impact)

        return {
            "user_id": user_id,
            "feedback_data_points": len(recent_behaviors),
            "feedback_impact": feedback_impact,
            "explanations": explanations,
            "preference_changes": await self._track_preference_changes(user_id, db),
            "feedback_effectiveness": self._calculate_feedback_effectiveness(recent_behaviors)
        }

    # Private helper methods

    def _normalize_explicit_feedback(self, feedback_data: Dict, feedback_type: FeedbackType) -> Dict:
        """Normalize explicit feedback to standard format."""
        if feedback_type == FeedbackType.EXPLICIT_RATING:
            # Assume rating is on 1-5 scale, convert to -1 to 1
            rating = feedback_data.get("rating", 3)
            normalized_value = (rating - 3) / 2.0  # Convert 1-5 to -1 to 1

        elif feedback_type == FeedbackType.LIKE_DISLIKE:
            # Boolean like/dislike
            liked = feedback_data.get("liked", None)
            if liked is True:
                normalized_value = 0.8
            elif liked is False:
                normalized_value = -0.8
            else:
                normalized_value = 0.0

        elif feedback_type == FeedbackType.CONTEXTUAL_COMMENT:
            # Analyze sentiment of comment (simplified)
            comment = feedback_data.get("comment", "")
            normalized_value = self._analyze_comment_sentiment(comment)

        else:
            normalized_value = 0.0

        return {
            "type": "explicit",
            "value": max(-1.0, min(1.0, normalized_value)),
            "context": feedback_data.get("context", {}),
            "timestamp": datetime.utcnow().isoformat(),
            "original_data": feedback_data
        }

    def _analyze_comment_sentiment(self, comment: str) -> float:
        """Simple sentiment analysis for comments."""
        # This is a simplified implementation
        # In practice, you'd use a proper sentiment analysis library

        positive_words = ["good", "great", "excellent", "love", "amazing", "wonderful",
                          "fantastic", "brilliant", "perfect", "outstanding"]
        negative_words = ["bad", "terrible", "awful", "hate", "horrible", "boring",
                          "disappointing", "waste", "poor", "worst"]

        comment_lower = comment.lower()

        positive_count = sum(
            1 for word in positive_words if word in comment_lower)
        negative_count = sum(
            1 for word in negative_words if word in comment_lower)

        if positive_count > negative_count:
            return min(0.8, positive_count * 0.2)
        elif negative_count > positive_count:
            return max(-0.8, -negative_count * 0.2)
        else:
            return 0.0

    def _analyze_completion_feedback(self, behavior_data: Dict) -> Optional[Dict]:
        """Analyze completion rate for implicit feedback."""
        completion_rate = behavior_data.get("completion_rate", 0.0)

        if completion_rate >= self.completion_thresholds["high"]:
            return {
                "type": FeedbackType.IMPLICIT_COMPLETION.value,
                "value": 0.6,
                "confidence": 0.8,
                "reason": f"High completion rate ({completion_rate:.1%})"
            }
        elif completion_rate <= self.completion_thresholds["low"]:
            return {
                "type": FeedbackType.IMPLICIT_COMPLETION.value,
                "value": -0.4,
                "confidence": 0.6,
                "reason": f"Low completion rate ({completion_rate:.1%})"
            }

        return None

    def _analyze_time_feedback(self, behavior_data: Dict) -> Optional[Dict]:
        """Analyze reading time patterns for implicit feedback."""
        reading_speed = behavior_data.get("reading_speed", 0.0)
        estimated_time = behavior_data.get("estimated_reading_time", 0)
        actual_time = behavior_data.get("actual_reading_time", 0)

        if estimated_time > 0 and actual_time > 0:
            time_ratio = actual_time / estimated_time

            if time_ratio >= self.time_thresholds["engaged"]:
                return {
                    "type": FeedbackType.IMPLICIT_TIME.value,
                    "value": 0.3,
                    "confidence": 0.5,
                    "reason": f"Spent {time_ratio:.1f}x expected time (engaged reading)"
                }
            elif time_ratio <= self.time_thresholds["rushed"]:
                return {
                    "type": FeedbackType.IMPLICIT_TIME.value,
                    "value": -0.2,
                    "confidence": 0.4,
                    "reason": f"Spent {time_ratio:.1f}x expected time (rushed reading)"
                }

        return None

    def _analyze_interaction_feedback(self, behavior_data: Dict) -> Optional[Dict]:
        """Analyze user interactions for implicit feedback."""
        interactions = behavior_data.get("interactions", [])

        if not interactions:
            return None

        # Count different types of interactions
        highlights = sum(
            1 for i in interactions if i.get("type") == "highlight")
        notes = sum(1 for i in interactions if i.get("type") == "note")
        bookmarks = sum(1 for i in interactions if i.get("type") == "bookmark")

        total_interactions = len(interactions)

        if total_interactions >= 5:  # High interaction threshold
            return {
                "type": FeedbackType.IMPLICIT_INTERACTION.value,
                "value": 0.4,
                "confidence": 0.6,
                "reason": f"High interaction count ({total_interactions} interactions)"
            }
        elif highlights > 0 or notes > 0:  # Meaningful interactions
            return {
                "type": FeedbackType.IMPLICIT_INTERACTION.value,
                "value": 0.2,
                "confidence": 0.4,
                "reason": f"Meaningful interactions ({highlights} highlights, {notes} notes)"
            }

        return None

    async def _analyze_return_behavior(self, user_id: str, content_id: str, db: Session) -> Optional[Dict]:
        """Analyze if user returns to content multiple times."""
        # Count reading sessions for this content
        session_count = db.query(ReadingBehavior).filter(
            and_(
                ReadingBehavior.user_id == user_id,
                ReadingBehavior.content_id == content_id
            )
        ).count()

        if session_count > 1:
            return {
                "type": FeedbackType.IMPLICIT_RETURN.value,
                "value": 0.5,
                "confidence": 0.7,
                "reason": f"Returned to content {session_count} times"
            }

        return None

    def _combine_implicit_signals(self, signals: List[Dict]) -> Optional[Dict]:
        """Combine multiple implicit feedback signals."""
        if not signals:
            return None

        # Weight signals by their confidence and type
        weighted_sum = 0.0
        total_weight = 0.0

        for signal in signals:
            signal_type = FeedbackType(signal["type"])
            weight = self.feedback_weights[signal_type] * signal["confidence"]
            weighted_sum += signal["value"] * weight
            total_weight += weight

        if total_weight == 0:
            return None

        combined_value = weighted_sum / total_weight

        return {
            "type": "implicit",
            "value": max(-1.0, min(1.0, combined_value)),
            "context": {"signals": signals},
            "timestamp": datetime.utcnow().isoformat(),
            "confidence": min(1.0, total_weight / len(signals))
        }

    async def _store_feedback_record(self, user_id: str, content_id: str,
                                     feedback_type: FeedbackType, feedback_data: Dict,
                                     db: Session) -> Dict:
        """Store feedback record for transparency and analysis."""
        # In a full implementation, you'd have a FeedbackRecord model
        # For now, we'll just log it
        record = {
            "user_id": user_id,
            "content_id": content_id,
            "feedback_type": feedback_type.value,
            "feedback_value": feedback_data["value"],
            "timestamp": datetime.utcnow().isoformat(),
            "context": feedback_data.get("context", {})
        }

        logger.info(f"Stored feedback record: {record}")
        return record

    async def _generate_feedback_explanation(self, user_id: str, content_id: str,
                                             feedback_type: FeedbackType, feedback_data: Dict,
                                             db: Session) -> str:
        """Generate explanation of how feedback will affect recommendations."""
        content = db.query(ContentItem).filter(
            ContentItem.id == content_id).first()

        if not content:
            return "Feedback recorded but content not found for detailed explanation."

        feedback_value = feedback_data["value"]
        content_title = content.title

        if feedback_value > 0.5:
            direction = "increase"
            strength = "significantly" if feedback_value > 0.7 else "moderately"
        elif feedback_value < -0.5:
            direction = "decrease"
            strength = "significantly" if feedback_value < -0.7 else "moderately"
        else:
            direction = "slightly adjust"
            strength = ""

        # Get content topics for specific explanation
        topics = []
        if content.analysis and "topics" in content.analysis:
            topics = [t["topic"] for t in content.analysis["topics"][:3]]

        topic_text = f" related to {', '.join(topics)}" if topics else ""

        explanation = (f"Your {feedback_type.value.replace('_', ' ')} for '{content_title}' will "
                       f"{strength} {direction} recommendations for similar content{topic_text}. "
                       f"This helps us better understand your preferences.")

        return explanation

    def _analyze_completion_patterns(self, behaviors: List[ReadingBehavior]) -> Dict:
        """Analyze completion rate patterns."""
        completion_rates = [
            b.completion_rate for b in behaviors if b.completion_rate is not None]

        if not completion_rates:
            return {"pattern": "insufficient_data"}

        avg_completion = sum(completion_rates) / len(completion_rates)
        high_completion_count = sum(
            1 for rate in completion_rates if rate > 0.8)
        low_completion_count = sum(
            1 for rate in completion_rates if rate < 0.3)

        return {
            "average_completion": avg_completion,
            "high_completion_sessions": high_completion_count,
            "low_completion_sessions": low_completion_count,
            "completion_consistency": 1.0 - (max(completion_rates) - min(completion_rates)),
            "pattern": self._classify_completion_pattern(avg_completion, high_completion_count, low_completion_count)
        }

    def _classify_completion_pattern(self, avg_completion: float, high_count: int, low_count: int) -> str:
        """Classify completion pattern."""
        if avg_completion > 0.8:
            return "high_completer"
        elif avg_completion < 0.3:
            return "low_completer"
        elif high_count > low_count * 2:
            return "selective_completer"
        elif low_count > high_count * 2:
            return "browser"
        else:
            return "mixed_pattern"

    def _analyze_time_patterns(self, behaviors: List[ReadingBehavior]) -> Dict:
        """Analyze reading time patterns."""
        reading_speeds = [
            b.reading_speed for b in behaviors if b.reading_speed and b.reading_speed > 0]

        if not reading_speeds:
            return {"pattern": "insufficient_data"}

        avg_speed = sum(reading_speeds) / len(reading_speeds)

        return {
            "average_reading_speed": avg_speed,
            "speed_consistency": 1.0 - (max(reading_speeds) - min(reading_speeds)) / avg_speed,
            "pattern": "fast_reader" if avg_speed > 300 else "slow_reader" if avg_speed < 150 else "average_reader"
        }

    def _analyze_interaction_patterns(self, behaviors: List[ReadingBehavior]) -> Dict:
        """Analyze interaction patterns."""
        total_interactions = sum(len(b.interactions or []) for b in behaviors)
        sessions_with_interactions = sum(
            1 for b in behaviors if b.interactions and len(b.interactions) > 0)

        return {
            "total_interactions": total_interactions,
            "sessions_with_interactions": sessions_with_interactions,
            "average_interactions_per_session": total_interactions / len(behaviors) if behaviors else 0,
            "interaction_rate": sessions_with_interactions / len(behaviors) if behaviors else 0,
            "pattern": "highly_interactive" if total_interactions > len(behaviors) * 3 else
            "moderately_interactive" if total_interactions > len(
                behaviors) else "passive_reader"
        }

    async def _analyze_content_type_patterns(self, behaviors: List[ReadingBehavior], db: Session) -> Dict:
        """Analyze content type preferences from behavior."""
        content_ids = [b.content_id for b in behaviors]

        if not content_ids:
            return {"pattern": "insufficient_data"}

        # Get content items
        content_items = db.query(ContentItem).filter(
            ContentItem.id.in_(content_ids)).all()
        content_types = [item.content_metadata.get(
            "content_type", "unknown") for item in content_items]

        # Count content types
        type_counts = {}
        for content_type in content_types:
            type_counts[content_type] = type_counts.get(content_type, 0) + 1

        # Find most preferred type
        most_read_type = max(
            type_counts.items(), key=lambda x: x[1]) if type_counts else ("unknown", 0)

        return {
            "content_type_distribution": type_counts,
            "most_read_type": most_read_type[0],
            "type_diversity": len(type_counts),
            "pattern": "specialized" if len(type_counts) <= 2 else "diverse_reader"
        }

    def _analyze_contextual_patterns(self, behaviors: List[ReadingBehavior]) -> Dict:
        """Analyze contextual reading patterns."""
        contexts = [b.context for b in behaviors if b.context]

        if not contexts:
            return {"pattern": "insufficient_data"}

        # Analyze time of day patterns
        time_patterns = {}
        device_patterns = {}

        for context in contexts:
            time_of_day = context.get("time_of_day", "unknown")
            device_type = context.get("device_type", "unknown")

            time_patterns[time_of_day] = time_patterns.get(time_of_day, 0) + 1
            device_patterns[device_type] = device_patterns.get(
                device_type, 0) + 1

        return {
            "time_of_day_patterns": time_patterns,
            "device_patterns": device_patterns,
            "preferred_reading_time": max(time_patterns.items(), key=lambda x: x[1])[0] if time_patterns else "unknown",
            "preferred_device": max(device_patterns.items(), key=lambda x: x[1])[0] if device_patterns else "unknown"
        }

    def _analyze_engagement_trends(self, behaviors: List[ReadingBehavior]) -> Dict:
        """Analyze engagement trends over time."""
        # Sort behaviors by date
        sorted_behaviors = sorted(behaviors, key=lambda b: b.created_at)

        if len(sorted_behaviors) < 5:
            return {"trend": "insufficient_data"}

        # Calculate engagement scores for each session
        engagement_scores = []
        for behavior in sorted_behaviors:
            score = 0.0

            # Completion rate contribution
            if behavior.completion_rate:
                score += behavior.completion_rate * 0.4

            # Interaction contribution
            if behavior.interactions:
                score += min(1.0, len(behavior.interactions) / 5) * 0.3

            # Reading speed contribution (normalized)
            if behavior.reading_speed and behavior.reading_speed > 0:
                # Normalize to 250 WPM
                speed_score = min(1.0, behavior.reading_speed / 250)
                score += speed_score * 0.3

            engagement_scores.append(score)

        # Analyze trend
        if len(engagement_scores) >= 3:
            recent_avg = sum(engagement_scores[-3:]) / 3
            early_avg = sum(engagement_scores[:3]) / 3
            trend_direction = "increasing" if recent_avg > early_avg * 1.1 else \
                "decreasing" if recent_avg < early_avg * 0.9 else "stable"
        else:
            trend_direction = "stable"

        return {
            "engagement_scores": engagement_scores,
            "average_engagement": sum(engagement_scores) / len(engagement_scores),
            "trend_direction": trend_direction,
            "recent_engagement": sum(engagement_scores[-5:]) / min(5, len(engagement_scores))
        }

    def _generate_pattern_insights(self, patterns: Dict) -> List[str]:
        """Generate insights from feedback patterns."""
        insights = []

        # Completion insights
        completion = patterns.get("completion_patterns", {})
        if completion.get("pattern") == "high_completer":
            insights.append(
                "You tend to finish most content you start, indicating good content matching.")
        elif completion.get("pattern") == "selective_completer":
            insights.append(
                "You're selective about what you finish, suggesting we should improve initial recommendations.")

        # Time insights
        time_patterns = patterns.get("time_patterns", {})
        if time_patterns.get("pattern") == "fast_reader":
            insights.append(
                "You read quickly, so we can recommend longer content without concern.")
        elif time_patterns.get("pattern") == "slow_reader":
            insights.append(
                "You prefer to read at a measured pace, so we'll prioritize quality over quantity.")

        # Interaction insights
        interaction = patterns.get("interaction_patterns", {})
        if interaction.get("pattern") == "highly_interactive":
            insights.append(
                "You actively engage with content through highlights and notes.")
        elif interaction.get("pattern") == "passive_reader":
            insights.append(
                "You prefer to read without many interactions, focusing on the content itself.")

        # Engagement trends
        engagement = patterns.get("engagement_trends", {})
        if engagement.get("trend_direction") == "increasing":
            insights.append(
                "Your engagement with recommended content is improving over time.")
        elif engagement.get("trend_direction") == "decreasing":
            insights.append(
                "We may need to adjust our recommendations to better match your evolving preferences.")

        return insights

    def _generate_feedback_recommendations(self, patterns: Dict) -> List[str]:
        """Generate recommendations based on feedback patterns."""
        recommendations = []

        completion = patterns.get("completion_patterns", {})
        if completion.get("average_completion", 0) < 0.5:
            recommendations.append(
                "Consider providing more explicit feedback to help us understand your preferences better.")

        interaction = patterns.get("interaction_patterns", {})
        if interaction.get("interaction_rate", 0) < 0.2:
            recommendations.append(
                "Try using highlights or notes to help us learn what interests you most.")

        engagement = patterns.get("engagement_trends", {})
        if engagement.get("trend_direction") == "decreasing":
            recommendations.append(
                "Let us know if your interests are changing so we can adapt our recommendations.")

        return recommendations

    async def _analyze_feedback_impact(self, user_id: str, behaviors: List[ReadingBehavior],
                                       db: Session) -> Dict:
        """Analyze how feedback has impacted user preferences."""
        # This would analyze changes in preferences over time
        # For now, return a simplified analysis

        return {
            "total_feedback_points": len(behaviors),
            "preference_adjustments": len(behaviors) // 5,  # Simplified
            "confidence_improvement": 0.1 * len(behaviors),  # Simplified
            # Would be calculated from actual data
            "recommendation_accuracy_trend": "improving"
        }

    def _generate_transparency_explanations(self, feedback_impact: Dict) -> List[str]:
        """Generate explanations for feedback transparency."""
        explanations = []

        total_points = feedback_impact.get("total_feedback_points", 0)
        adjustments = feedback_impact.get("preference_adjustments", 0)

        explanations.append(
            f"We've analyzed {total_points} reading sessions to understand your preferences.")

        if adjustments > 0:
            explanations.append(
                f"Based on your behavior, we've made {adjustments} adjustments to your preference profile.")

        explanations.append(
            "Your feedback helps us recommend content that better matches your interests and reading level.")

        return explanations

    async def _track_preference_changes(self, user_id: str, db: Session) -> List[Dict]:
        """Track how preferences have changed over time."""
        # This would track actual preference changes
        # For now, return a simplified version

        return [
            {
                "change_type": "topic_preference",
                "item": "fiction",
                "old_value": 0.5,
                "new_value": 0.7,
                "change_date": datetime.utcnow().isoformat(),
                "reason": "Increased engagement with fiction content"
            }
        ]

    def _calculate_feedback_effectiveness(self, behaviors: List[ReadingBehavior]) -> Dict:
        """Calculate how effective the feedback system has been."""
        if not behaviors:
            return {"effectiveness": "insufficient_data"}

        # Simplified effectiveness calculation
        avg_completion = sum(
            b.completion_rate or 0 for b in behaviors) / len(behaviors)
        interaction_rate = sum(1 for b in behaviors if b.interactions and len(
            b.interactions) > 0) / len(behaviors)

        effectiveness_score = (avg_completion * 0.6) + (interaction_rate * 0.4)

        return {
            "effectiveness_score": effectiveness_score,
            "effectiveness": "high" if effectiveness_score > 0.7 else
            "medium" if effectiveness_score > 0.4 else "low",
            "improvement_areas": self._identify_improvement_areas(avg_completion, interaction_rate)
        }

    def _identify_improvement_areas(self, completion_rate: float, interaction_rate: float) -> List[str]:
        """Identify areas for improvement in feedback processing."""
        areas = []

        if completion_rate < 0.5:
            areas.append("Content relevance matching")

        if interaction_rate < 0.3:
            areas.append("User engagement encouragement")

        if not areas:
            areas.append("Continue current approach")

        return areas


# Global instance
feedback_processor = FeedbackProcessor()
