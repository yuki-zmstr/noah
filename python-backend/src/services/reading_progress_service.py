"""Reading progress tracking service with adaptive difficulty adjustment."""

import logging
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from collections import defaultdict
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func

from src.models.user_profile import UserProfile, ReadingBehavior, PreferenceSnapshot
from src.models.content import ContentItem
from src.schemas.reading_behavior import ReadingBehaviorCreate, ReadingBehaviorResponse
from src.schemas.user_profile import ReadingContext
from src.services.user_profile_service import user_profile_engine

logger = logging.getLogger(__name__)


class ReadingProgressTracker:
    """Service for tracking reading progress and adaptive difficulty adjustment."""

    def __init__(self):
        """Initialize the reading progress tracker."""
        self.difficulty_adjustment_threshold = 0.7  # Performance threshold for difficulty increase
        self.struggle_threshold = 0.4  # Performance threshold indicating struggle
        # Days to analyze for skill development
        self.skill_development_window_days = 14
        self.behavioral_metrics_weights = {
            "completion_rate": 0.35,
            "reading_speed": 0.25,
            "comprehension_indicators": 0.25,
            "engagement_metrics": 0.15
        }

    async def start_reading_session(self, user_id: str, content_id: str,
                                    context: Optional[ReadingContext], db: Session) -> Dict:
        """Start a new reading session and return session tracking data."""
        session_id = f"{user_id}_{content_id}_{datetime.utcnow().timestamp()}"

        # Get user profile and content for initial assessment
        profile = await user_profile_engine.get_or_create_profile(user_id, db)
        content = db.query(ContentItem).filter(
            ContentItem.id == content_id).first()

        if not content:
            raise ValueError(f"Content {content_id} not found")

        # Assess content difficulty vs user level
        difficulty_assessment = self._assess_content_difficulty(
            profile, content, context)

        # Create initial reading behavior record
        behavior_data = {
            "session_id": session_id,
            "start_time": datetime.utcnow(),
            "context": context.dict() if context else {}
        }

        behavior = await user_profile_engine.update_reading_behavior(
            user_id, content_id, behavior_data, db
        )

        session_data = {
            "session_id": session_id,
            "behavior_id": behavior.id,
            "content_title": content.title,
            "difficulty_assessment": difficulty_assessment,
            "adaptive_suggestions": self._generate_adaptive_suggestions(
                profile, content, difficulty_assessment
            ),
            "tracking_metrics": self._initialize_tracking_metrics()
        }

        logger.info(f"Started reading session {session_id} for user {user_id}")
        return session_data

    async def update_reading_progress(self, session_id: str, progress_data: Dict,
                                      db: Session) -> Dict:
        """Update reading progress with real-time behavioral metrics."""
        # Find the reading behavior record
        behavior = db.query(ReadingBehavior).filter(
            ReadingBehavior.session_id == session_id
        ).first()

        if not behavior:
            raise ValueError(f"Reading session {session_id} not found")

        # Update behavioral metrics
        updated_metrics = self._update_behavioral_metrics(
            behavior, progress_data)

        # Calculate real-time performance indicators
        performance_indicators = self._calculate_performance_indicators(
            updated_metrics, progress_data
        )

        # Check if adaptive adjustments are needed
        adaptive_adjustments = await self._check_adaptive_adjustments(
            behavior.user_id, performance_indicators, db
        )

        # Update the behavior record
        behavior.pause_patterns = updated_metrics.get("pause_patterns", [])
        behavior.interactions = updated_metrics.get("interactions", [])
        behavior.reading_speed = updated_metrics.get(
            "current_reading_speed", 0.0)
        behavior.completion_rate = progress_data.get("completion_rate", 0.0)

        db.commit()

        return {
            "session_id": session_id,
            "performance_indicators": performance_indicators,
            "adaptive_adjustments": adaptive_adjustments,
            "behavioral_metrics": updated_metrics,
            "recommendations": await self._generate_real_time_recommendations(
                behavior.user_id, performance_indicators, db
            )
        }

    async def complete_reading_session(self, session_id: str, completion_data: Dict,
                                       db: Session) -> Dict:
        """Complete a reading session and perform comprehensive analysis."""
        behavior = db.query(ReadingBehavior).filter(
            ReadingBehavior.session_id == session_id
        ).first()

        if not behavior:
            raise ValueError(f"Reading session {session_id} not found")

        # Update final metrics
        behavior.end_time = datetime.utcnow()
        behavior.completion_rate = completion_data.get("completion_rate", 0.0)

        # Calculate session duration
        session_duration = (behavior.end_time -
                            behavior.start_time).total_seconds() / 60

        # Perform comprehensive session analysis
        session_analysis = await self._analyze_completed_session(behavior, db)

        # Update user reading level based on performance
        await self._update_reading_level_from_session(behavior, session_analysis, db)

        # Generate skill development insights
        skill_insights = await self._generate_skill_development_insights(behavior.user_id, db)

        # Update adaptive difficulty recommendations
        difficulty_recommendations = await self._update_difficulty_recommendations(
            behavior.user_id, session_analysis, db
        )

        db.commit()

        completion_summary = {
            "session_id": session_id,
            "session_duration_minutes": session_duration,
            "completion_rate": behavior.completion_rate,
            "session_analysis": session_analysis,
            "skill_insights": skill_insights,
            "difficulty_recommendations": difficulty_recommendations,
            "next_content_suggestions": await self._suggest_next_content(
                behavior.user_id, session_analysis, db
            )
        }

        logger.info(
            f"Completed reading session {session_id} for user {behavior.user_id}")
        return completion_summary

    async def get_progress_analytics(self, user_id: str, time_period_days: int,
                                     db: Session) -> Dict:
        """Get comprehensive progress analytics for a user."""
        cutoff_date = datetime.utcnow() - timedelta(days=time_period_days)

        # Get reading behaviors in the time period
        behaviors = db.query(ReadingBehavior).filter(
            and_(
                ReadingBehavior.user_id == user_id,
                ReadingBehavior.created_at >= cutoff_date
            )
        ).order_by(desc(ReadingBehavior.created_at)).all()

        if not behaviors:
            return {"message": "No reading data available for the specified period"}

        # Calculate progress metrics
        progress_metrics = self._calculate_progress_metrics(behaviors)

        # Analyze skill development trends
        skill_trends = self._analyze_skill_development_trends(behaviors)

        # Generate adaptive difficulty insights
        difficulty_insights = await self._generate_difficulty_insights(user_id, behaviors, db)

        # Calculate behavioral patterns
        behavioral_patterns = self._analyze_behavioral_patterns(behaviors)

        return {
            "user_id": user_id,
            "analysis_period_days": time_period_days,
            "total_sessions": len(behaviors),
            "progress_metrics": progress_metrics,
            "skill_development_trends": skill_trends,
            "difficulty_insights": difficulty_insights,
            "behavioral_patterns": behavioral_patterns,
            "recommendations": await self._generate_progress_recommendations(
                user_id, progress_metrics, skill_trends, db
            )
        }

    # Private helper methods

    def _assess_content_difficulty(self, profile: UserProfile, content: ContentItem,
                                   context: Optional[ReadingContext]) -> Dict:
        """Assess content difficulty relative to user's current level."""
        if not content.analysis:
            return {"assessment": "unknown", "confidence": 0.0}

        content_analysis = content.analysis
        reading_levels = profile.reading_levels

        # Determine content language
        content_language = content.language or "english"

        if content_language == "english":
            user_level = reading_levels.get("english", {}).get("level", 8.0)
            content_difficulty = content_analysis.get(
                "reading_level", {}).get("flesch_kincaid", 8.0)
        elif content_language == "japanese":
            user_level = reading_levels.get("japanese", {}).get("level", 0.3)
            content_difficulty = content_analysis.get(
                "reading_level", {}).get("kanji_density", 0.3)
        else:
            return {"assessment": "unsupported_language", "confidence": 0.0}

        # Calculate difficulty ratio
        if content_language == "english":
            difficulty_ratio = content_difficulty / max(user_level, 1.0)
        else:  # Japanese
            difficulty_ratio = content_difficulty / max(user_level, 0.1)

        # Determine assessment
        if difficulty_ratio < 0.8:
            assessment = "too_easy"
        elif difficulty_ratio < 1.2:
            assessment = "appropriate"
        elif difficulty_ratio < 1.5:
            assessment = "challenging"
        else:
            assessment = "too_difficult"

        # Consider context factors
        context_adjustment = 0.0
        if context:
            if context.available_time and context.available_time < 15:
                context_adjustment -= 0.1  # Prefer easier content for short sessions
            if context.user_mood == "tired":
                context_adjustment -= 0.2
            elif context.user_mood == "focused":
                context_adjustment += 0.1

        adjusted_ratio = difficulty_ratio + context_adjustment

        return {
            "assessment": assessment,
            "difficulty_ratio": difficulty_ratio,
            "adjusted_ratio": adjusted_ratio,
            "content_level": content_difficulty,
            "user_level": user_level,
            "language": content_language,
            "confidence": reading_levels.get(content_language, {}).get("confidence", 0.5)
        }

    def _generate_adaptive_suggestions(self, profile: UserProfile, content: ContentItem,
                                       difficulty_assessment: Dict) -> List[Dict]:
        """Generate adaptive suggestions based on difficulty assessment."""
        suggestions = []

        assessment = difficulty_assessment.get("assessment", "unknown")

        if assessment == "too_difficult":
            suggestions.extend([
                {
                    "type": "content_adaptation",
                    "suggestion": "Consider using simplified version of this content",
                    "priority": "high"
                },
                {
                    "type": "reading_strategy",
                    "suggestion": "Take frequent breaks and focus on key concepts",
                    "priority": "medium"
                }
            ])
        elif assessment == "too_easy":
            suggestions.extend([
                {
                    "type": "complexity_increase",
                    "suggestion": "Look for more advanced content in this topic",
                    "priority": "medium"
                }
            ])
        elif assessment == "challenging":
            suggestions.append({
                "type": "optimal_challenge",
                "suggestion": "This content is at an optimal difficulty level for skill development",
                "priority": "info"
            })

        return suggestions

    def _initialize_tracking_metrics(self) -> Dict:
        """Initialize tracking metrics for a new session."""
        return {
            "start_time": datetime.utcnow().isoformat(),
            "pause_patterns": [],
            "interactions": [],
            "reading_speed_samples": [],
            "comprehension_indicators": [],
            "engagement_metrics": {
                "scroll_events": 0,
                "highlight_events": 0,
                "note_events": 0,
                "lookup_events": 0
            }
        }

    def _update_behavioral_metrics(self, behavior: ReadingBehavior,
                                   progress_data: Dict) -> Dict:
        """Update behavioral metrics with new progress data."""
        current_metrics = {
            "pause_patterns": behavior.pause_patterns or [],
            "interactions": behavior.interactions or [],
            "engagement_metrics": {}
        }

        # Update pause patterns
        if "pause_event" in progress_data:
            pause_event = progress_data["pause_event"]
            pause_event["timestamp"] = datetime.utcnow().isoformat()
            current_metrics["pause_patterns"].append(pause_event)

        # Update interactions
        if "interaction_event" in progress_data:
            interaction_event = progress_data["interaction_event"]
            interaction_event["timestamp"] = datetime.utcnow().isoformat()
            current_metrics["interactions"].append(interaction_event)

        # Update engagement metrics
        engagement = current_metrics.get("engagement_metrics", {})
        if "engagement_data" in progress_data:
            for key, value in progress_data["engagement_data"].items():
                engagement[key] = engagement.get(key, 0) + value

        # Calculate current reading speed
        if "words_read" in progress_data and "time_elapsed" in progress_data:
            time_minutes = progress_data["time_elapsed"] / 60
            if time_minutes > 0:
                current_metrics["current_reading_speed"] = progress_data["words_read"] / time_minutes

        current_metrics["engagement_metrics"] = engagement
        return current_metrics

    def _calculate_performance_indicators(self, metrics: Dict, progress_data: Dict) -> Dict:
        """Calculate real-time performance indicators."""
        indicators = {}

        # Reading speed indicator
        current_speed = metrics.get("current_reading_speed", 0)
        if current_speed > 0:
            # Average reading speed is 200-300 WPM
            speed_percentile = min(1.0, max(0.0, (current_speed - 100) / 200))
            indicators["reading_speed_percentile"] = speed_percentile

        # Engagement indicator
        engagement = metrics.get("engagement_metrics", {})
        total_engagement = sum(engagement.values())
        indicators["engagement_score"] = min(1.0, total_engagement / 10)

        # Comprehension indicator (based on pause patterns and interactions)
        pause_count = len(metrics.get("pause_patterns", []))
        interaction_count = len(metrics.get("interactions", []))

        # More pauses might indicate difficulty, but some pauses are normal
        pause_score = max(0.0, 1.0 - (pause_count / 20))
        interaction_score = min(1.0, interaction_count / 5)

        indicators["comprehension_estimate"] = (
            pause_score + interaction_score) / 2

        # Overall performance score
        completion_rate = progress_data.get("completion_rate", 0.0)
        indicators["overall_performance"] = (
            completion_rate * 0.4 +
            indicators.get("reading_speed_percentile", 0.5) * 0.3 +
            indicators.get("comprehension_estimate", 0.5) * 0.3
        )

        return indicators

    async def _check_adaptive_adjustments(self, user_id: str, performance_indicators: Dict,
                                          db: Session) -> List[Dict]:
        """Check if adaptive adjustments are needed based on performance."""
        adjustments = []

        overall_performance = performance_ind
        # Comprehension indicator (based on pause patterns and interactions)
        pause_count = len(metrics.get("pause_patterns", []))
        interaction_count = len(metrics.get("interactions", []))

        # More pauses might indicate difficulty, but some pauses are normal
        pause_score = max(0.0, 1.0 - (pause_count / 20))
        interaction_score = min(1.0, interaction_count / 5)

        indicators["comprehension_estimate"] = (
            pause_score + interaction_score) / 2

        # Overall performance score
        completion_rate = progress_data.get("completion_rate", 0.0)
        indicators["overall_performance"] = (
            completion_rate * 0.4 +
            indicators.get("reading_speed_percentile", 0.5) * 0.3 +
            indicators.get("comprehension_estimate", 0.5) * 0.3
        )

        return indicators

    async def _check_adaptive_adjustments(self, user_id: str, performance_indicators: Dict,
                                          db: Session) -> List[Dict]:
        """Check if adaptive adjustments are needed based on performance."""
        adjustments = []

        overall_performance = performance_indicators.get(
            "overall_performance", 0.5)
        comprehension = performance_indicators.get(
            "comprehension_estimate", 0.5)

        if overall_performance < self.struggle_threshold:
            adjustments.append({
                "type": "difficulty_reduction",
                "reason": "Performance indicates struggle with current content",
                "suggestion": "Consider switching to easier content or taking a break",
                "urgency": "high"
            })

        if comprehension < 0.3:
            adjustments.append({
                "type": "comprehension_support",
                "reason": "Low comprehension indicators detected",
                "suggestion": "Slow down reading pace and focus on understanding",
                "urgency": "medium"
            })

        if overall_performance > self.difficulty_adjustment_threshold:
            adjustments.append({
                "type": "difficulty_increase",
                "reason": "Performance suggests content may be too easy",
                "suggestion": "Consider more challenging content after this session",
                "urgency": "low"
            })

        return adjustments

    async def _generate_real_time_recommendations(self, user_id: str,
                                                  performance_indicators: Dict,
                                                  db: Session) -> List[Dict]:
        """Generate real-time recommendations based on current performance."""
        recommendations = []

        reading_speed = performance_indicators.get(
            "reading_speed_percentile", 0.5)
        engagement = performance_indicators.get("engagement_score", 0.5)

        if reading_speed < 0.3:
            recommendations.append({
                "type": "reading_technique",
                "message": "Try to maintain a steady reading pace",
                "priority": "medium"
            })

        if engagement < 0.2:
            recommendations.append({
                "type": "engagement",
                "message": "Consider taking notes or highlighting key points to stay engaged",
                "priority": "medium"
            })

        if reading_speed > 0.8 and engagement > 0.7:
            recommendations.append({
                "type": "positive_feedback",
                "message": "Great reading pace and engagement! Keep it up!",
                "priority": "info"
            })

        return recommendations

    async def _analyze_completed_session(self, behavior: ReadingBehavior, db: Session) -> Dict:
        """Perform comprehensive analysis of a completed reading session."""
        session_duration = (behavior.end_time -
                            behavior.start_time).total_seconds() / 60

        # Analyze pause patterns
        pause_analysis = self._analyze_pause_patterns(
            behavior.pause_patterns or [])

        # Analyze interactions
        interaction_analysis = self._analyze_interactions(
            behavior.interactions or [])

        # Calculate performance metrics
        performance_score = self._calculate_session_performance_score(behavior)

        # Determine skill development indicators
        skill_indicators = self._identify_skill_development_indicators(
            behavior, pause_analysis, interaction_analysis
        )

        return {
            "session_duration_minutes": session_duration,
            "completion_rate": behavior.completion_rate,
            "average_reading_speed": behavior.reading_speed,
            "pause_analysis": pause_analysis,
            "interaction_analysis": interaction_analysis,
            "performance_score": performance_score,
            "skill_development_indicators": skill_indicators,
            "session_quality": self._assess_session_quality(performance_score, skill_indicators)
        }

    def _analyze_pause_patterns(self, pause_patterns: List[Dict]) -> Dict:
        """Analyze pause patterns to understand reading behavior."""
        if not pause_patterns:
            return {"total_pauses": 0, "average_pause_duration": 0, "pause_frequency": 0}

        total_pauses = len(pause_patterns)
        pause_durations = [p.get("duration", 0) for p in pause_patterns]
        average_duration = sum(pause_durations) / \
            len(pause_durations) if pause_durations else 0

        # Categorize pauses
        short_pauses = sum(1 for d in pause_durations if d < 5)  # < 5 seconds
        medium_pauses = sum(
            1 for d in pause_durations if 5 <= d < 30)  # 5-30 seconds
        long_pauses = sum(1 for d in pause_durations if d >=
                          30)  # >= 30 seconds

        return {
            "total_pauses": total_pauses,
            "average_pause_duration": average_duration,
            "pause_frequency": total_pauses / max(1, len(pause_patterns)),
            "pause_distribution": {
                "short": short_pauses,
                "medium": medium_pauses,
                "long": long_pauses
            },
            "interpretation": self._interpret_pause_patterns(short_pauses, medium_pauses, long_pauses)
        }

    def _analyze_interactions(self, interactions: List[Dict]) -> Dict:
        """Analyze user interactions during reading."""
        if not interactions:
            return {"total_interactions": 0, "interaction_types": {}}

        interaction_types = defaultdict(int)
        for interaction in interactions:
            interaction_type = interaction.get("type", "unknown")
            interaction_types[interaction_type] += 1

        return {
            "total_interactions": len(interactions),
            "interaction_types": dict(interaction_types),
            "engagement_level": self._calculate_engagement_level(interaction_types),
            "learning_indicators": self._identify_learning_indicators(interaction_types)
        }

    def _calculate_session_performance_score(self, behavior: ReadingBehavior) -> float:
        """Calculate overall performance score for the session."""
        completion_rate = behavior.completion_rate or 0.0
        reading_speed = behavior.reading_speed or 0.0

        # Normalize reading speed (200-300 WPM is average)
        speed_score = min(1.0, max(0.0, (reading_speed - 100) / 200))

        # Analyze pause patterns for comprehension indicators
        pause_count = len(behavior.pause_patterns or [])
        # Fewer pauses generally better
        pause_score = max(0.0, 1.0 - (pause_count / 15))

        # Analyze interactions for engagement
        interaction_count = len(behavior.interactions or [])
        # More interactions show engagement
        interaction_score = min(1.0, interaction_count / 5)

        # Weighted performance score
        performance_score = (
            completion_rate * self.behavioral_metrics_weights["completion_rate"] +
            speed_score * self.behavioral_metrics_weights["reading_speed"] +
            pause_score * self.behavioral_metrics_weights["comprehension_indicators"] +
            interaction_score *
            self.behavioral_metrics_weights["engagement_metrics"]
        )

        return max(0.0, min(1.0, performance_score))

    def _identify_skill_development_indicators(self, behavior: ReadingBehavior,
                                               pause_analysis: Dict, interaction_analysis: Dict) -> Dict:
        """Identify indicators of skill development from the session."""
        indicators = {}

        # Reading fluency indicators
        if behavior.reading_speed and behavior.reading_speed > 200:
            indicators["reading_fluency"] = "good"
        elif behavior.reading_speed and behavior.reading_speed > 150:
            indicators["reading_fluency"] = "developing"
        else:
            indicators["reading_fluency"] = "needs_improvement"

        # Comprehension indicators
        pause_frequency = pause_analysis.get("pause_frequency", 0)
        if pause_frequency < 0.1:
            indicators["comprehension_flow"] = "excellent"
        elif pause_frequency < 0.2:
            indicators["comprehension_flow"] = "good"
        else:
            indicators["comprehension_flow"] = "challenging"

        # Engagement indicators
        engagement_level = interaction_analysis.get("engagement_level", "low")
        indicators["engagement"] = engagement_level

        # Learning behavior indicators
        learning_indicators = interaction_analysis.get(
            "learning_indicators", [])
        indicators["active_learning"] = len(learning_indicators) > 0

        return indicators

    def _assess_session_quality(self, performance_score: float, skill_indicators: Dict) -> str:
        """Assess overall session quality."""
        if performance_score > 0.8:
            return "excellent"
        elif performance_score > 0.6:
            return "good"
        elif performance_score > 0.4:
            return "fair"
        else:
            return "needs_improvement"

    def _interpret_pause_patterns(self, short: int, medium: int, long: int) -> str:
        """Interpret pause patterns for reading behavior insights."""
        total = short + medium + long
        if total == 0:
            return "Continuous reading with no significant pauses"

        if long > total * 0.3:
            return "Frequent long pauses may indicate difficulty or distraction"
        elif medium > total * 0.5:
            return "Moderate pauses suggest thoughtful reading and processing"
        else:
            return "Quick reading with minimal pauses"

    def _calculate_engagement_level(self, interaction_types: Dict) -> str:
        """Calculate engagement level from interaction types."""
        total_interactions = sum(interaction_types.values())

        if total_interactions > 10:
            return "high"
        elif total_interactions > 5:
            return "medium"
        else:
            return "low"

    def _identify_learning_indicators(self, interaction_types: Dict) -> List[str]:
        """Identify learning behavior indicators from interactions."""
        indicators = []

        if interaction_types.get("highlight", 0) > 0:
            indicators.append("active_highlighting")
        if interaction_types.get("note", 0) > 0:
            indicators.append("note_taking")
        if interaction_types.get("lookup", 0) > 0:
            indicators.append("vocabulary_lookup")
        if interaction_types.get("bookmark", 0) > 0:
            indicators.append("content_saving")

        return indicators

    async def _update_reading_level_from_session(self, behavior: ReadingBehavior,
                                                 session_analysis: Dict, db: Session) -> None:
        """Update user reading level based on session performance."""
        content = db.query(ContentItem).filter(
            ContentItem.id == behavior.content_id).first()
        if not content or not content.analysis:
            return

        performance_score = session_analysis["performance_score"]
        content_language = content.language or "english"

        # Prepare performance metrics for reading level assessment
        performance_metrics = {
            "completion_rate": behavior.completion_rate,
            "reading_speed": behavior.reading_speed,
            "pause_patterns": behavior.pause_patterns or [],
            "interactions": behavior.interactions or []
        }

        # Update reading level using the user profile engine
        await user_profile_engine.assess_reading_level(
            behavior.user_id, content_language, content.analysis, performance_metrics, db
        )

    async def _generate_skill_development_insights(self, user_id: str, db: Session) -> Dict:
        """Generate insights about skill development trends."""
        cutoff_date = datetime.utcnow() - timedelta(days=self.skill_development_window_days)

        recent_behaviors = db.query(ReadingBehavior).filter(
            and_(
                ReadingBehavior.user_id == user_id,
                ReadingBehavior.created_at >= cutoff_date,
                ReadingBehavior.end_time.isnot(None)  # Only completed sessions
            )
        ).order_by(ReadingBehavior.created_at).all()

        if len(recent_behaviors) < 3:
            return {"message": "Insufficient data for skill development analysis"}

        # Analyze trends
        completion_rates = [
            b.completion_rate for b in recent_behaviors if b.completion_rate]
        reading_speeds = [
            b.reading_speed for b in recent_behaviors if b.reading_speed]

        insights = {}

        if completion_rates:
            completion_trend = self._calculate_trend(completion_rates)
            insights["completion_rate_trend"] = completion_trend

        if reading_speeds:
            speed_trend = self._calculate_trend(reading_speeds)
            insights["reading_speed_trend"] = speed_trend

        # Analyze difficulty progression
        difficulty_progression = await self._analyze_difficulty_progression(recent_behaviors, db)
        insights["difficulty_progression"] = difficulty_progression

        return insights

    def _calculate_trend(self, values: List[float]) -> Dict:
        """Calculate trend direction and magnitude for a series of values."""
        if len(values) < 2:
            return {"trend": "insufficient_data"}

        # Simple linear trend calculation
        x = list(range(len(values)))
        slope = np.polyfit(x, values, 1)[0]

        if abs(slope) < 0.01:
            trend = "stable"
        elif slope > 0:
            trend = "improving"
        else:
            trend = "declining"

        return {
            "trend": trend,
            "slope": slope,
            "start_value": values[0],
            "end_value": values[-1],
            "change_percentage": ((values[-1] - values[0]) / values[0] * 100) if values[0] != 0 else 0
        }

    async def _analyze_difficulty_progression(self, behaviors: List[ReadingBehavior],
                                              db: Session) -> Dict:
        """Analyze how content difficulty has progressed over time."""
        content_ids = [b.content_id for b in behaviors]
        contents = db.query(ContentItem).filter(
            ContentItem.id.in_(content_ids)).all()
        content_map = {c.id: c for c in contents}

        difficulty_levels = []
        for behavior in behaviors:
            content = content_map.get(behavior.content_id)
            if content and content.analysis:
                if content.language == "japanese":
                    difficulty = content.analysis.get(
                        "reading_level", {}).get("kanji_density", 0.3)
                else:
                    difficulty = content.analysis.get(
                        "reading_level", {}).get("flesch_kincaid", 8.0)
                difficulty_levels.append(difficulty)

        if not difficulty_levels:
            return {"message": "No difficulty data available"}

        return self._calculate_trend(difficulty_levels)

    async def _update_difficulty_recommendations(self, user_id: str, session_analysis: Dict,
                                                 db: Session) -> Dict:
        """Update difficulty recommendations based on session performance."""
        performance_score = session_analysis["performance_score"]
        session_quality = session_analysis["session_quality"]

        recommendations = {}

        if performance_score > self.difficulty_adjustment_threshold and session_quality in ["good", "excellent"]:
            recommendations["next_difficulty"] = "increase"
            recommendations["reason"] = "Strong performance suggests readiness for more challenging content"
        elif performance_score < self.struggle_threshold:
            recommendations["next_difficulty"] = "decrease"
            recommendations["reason"] = "Performance indicates current content may be too difficult"
        else:
            recommendations["next_difficulty"] = "maintain"
            recommendations["reason"] = "Current difficulty level appears appropriate"

        # Get user's recent difficulty progression
        skill_insights = await self._generate_skill_development_insights(user_id, db)
        if "difficulty_progression" in skill_insights:
            progression = skill_insights["difficulty_progression"]
            if progression.get("trend") == "improving":
                recommendations["progression_note"] = "User is successfully handling increasing difficulty"
            elif progression.get("trend") == "declining":
                recommendations["progression_note"] = "Consider stabilizing at current difficulty level"

        return recommendations

    async def _suggest_next_content(self, user_id: str, session_analysis: Dict,
                                    db: Session) -> List[Dict]:
        """Suggest next content based on session performance and user progress."""
        # This would integrate with the recommendation engine
        # For now, return basic suggestions based on performance

        performance_score = session_analysis["performance_score"]
        suggestions = []

        if performance_score > 0.7:
            suggestions.append({
                "type": "challenge_increase",
                "message": "Try more advanced content in the same topic",
                "priority": "high"
            })
        elif performance_score < 0.4:
            suggestions.append({
                "type": "skill_building",
                "message": "Practice with similar or easier content to build confidence",
                "priority": "high"
            })
        else:
            suggestions.append({
                "type": "continue_level",
                "message": "Continue with similar difficulty level content",
                "priority": "medium"
            })

        return suggestions

    def _calculate_progress_metrics(self, behaviors: List[ReadingBehavior]) -> Dict:
        """Calculate comprehensive progress metrics from reading behaviors."""
        if not behaviors:
            return {}

        completed_sessions = [
            b for b in behaviors if b.end_time and b.completion_rate is not None]

        if not completed_sessions:
            return {"message": "No completed sessions found"}

        # Calculate averages
        avg_completion_rate = sum(
            b.completion_rate for b in completed_sessions) / len(completed_sessions)
        avg_reading_speed = sum(b.reading_speed for b in completed_sessions if b.reading_speed) / \
            len([b for b in completed_sessions if b.reading_speed])

        # Calculate session durations
        session_durations = []
        for b in completed_sessions:
            if b.start_time and b.end_time:
                duration = (b.end_time - b.start_time).total_seconds() / 60
                session_durations.append(duration)

        avg_session_duration = sum(
            session_durations) / len(session_durations) if session_durations else 0

        return {
            "total_sessions": len(behaviors),
            "completed_sessions": len(completed_sessions),
            "completion_rate": len(completed_sessions) / len(behaviors),
            "average_content_completion": avg_completion_rate,
            "average_reading_speed_wpm": avg_reading_speed,
            "average_session_duration_minutes": avg_session_duration,
            "total_reading_time_hours": sum(session_durations) / 60 if session_durations else 0
        }

    def _analyze_skill_development_trends(self, behaviors: List[ReadingBehavior]) -> Dict:
        """Analyze skill development trends from reading behaviors."""
        completed_behaviors = [
            b for b in behaviors if b.end_time and b.completion_rate is not None]

        if len(completed_behaviors) < 3:
            return {"message": "Insufficient data for trend analysis"}

        # Sort by date
        completed_behaviors.sort(key=lambda x: x.created_at)

        # Analyze completion rate trend
        completion_rates = [b.completion_rate for b in completed_behaviors]
        completion_trend = self._calculate_trend(completion_rates)

        # Analyze reading speed trend
        reading_speeds = [
            b.reading_speed for b in completed_behaviors if b.reading_speed]
        speed_trend = self._calculate_trend(reading_speeds) if reading_speeds else {
            "trend": "no_data"}

        return {
            "completion_rate_trend": completion_trend,
            "reading_speed_trend": speed_trend,
            "skill_development_summary": self._summarize_skill_development(completion_trend, speed_trend)
        }

    def _summarize_skill_development(self, completion_trend: Dict, speed_trend: Dict) -> str:
        """Summarize overall skill development based on trends."""
        completion_dir = completion_trend.get("trend", "stable")
        speed_dir = speed_trend.get("trend", "stable")

        if completion_dir == "improving" and speed_dir == "improving":
            return "Excellent progress - both comprehension and reading speed are improving"
        elif completion_dir == "improving":
            return "Good progress - comprehension is improving steadily"
        elif speed_dir == "improving":
            return "Good progress - reading speed is increasing"
        elif completion_dir == "stable" and speed_dir == "stable":
            return "Steady performance - skills are stabilizing at current level"
        else:
            return "Mixed progress - some areas may need attention"

    async def _generate_difficulty_insights(self, user_id: str, behaviors: List[ReadingBehavior],
                                            db: Session) -> Dict:
        """Generate insights about difficulty management and adaptation."""
        # Get content difficulty data
        content_ids = [b.content_id for b in behaviors]
        contents = db.query(ContentItem).filter(
            ContentItem.id.in_(content_ids)).all()
        content_map = {c.id: c for c in contents}

        difficulty_performance = []
        for behavior in behaviors:
            if behavior.completion_rate is not None:
                content = content_map.get(behavior.content_id)
                if content and content.analysis:
                    if content.language == "japanese":
                        difficulty = content.analysis.get(
                            "reading_level", {}).get("kanji_density", 0.3)
                    else:
                        difficulty = content.analysis.get(
                            "reading_level", {}).get("flesch_kincaid", 8.0)

                    difficulty_performance.append({
                        "difficulty": difficulty,
                        "performance": behavior.completion_rate,
                        "language": content.language
                    })

        if not difficulty_performance:
            return {"message": "No difficulty data available"}

        # Analyze optimal difficulty range
        optimal_range = self._find_optimal_difficulty_range(
            difficulty_performance)

        return {
            "optimal_difficulty_range": optimal_range,
            "difficulty_adaptation_needed": self._assess_difficulty_adaptation_need(difficulty_performance),
            "language_specific_insights": self._generate_language_specific_insights(difficulty_performance)
        }

    def _find_optimal_difficulty_range(self, difficulty_performance: List[Dict]) -> Dict:
        """Find the optimal difficulty range for the user."""
        # Group by performance levels
        high_performance = [
            dp for dp in difficulty_performance if dp["performance"] > 0.8]
        medium_performance = [
            dp for dp in difficulty_performance if 0.6 <= dp["performance"] <= 0.8]

        optimal_difficulties = high_performance + medium_performance

        if not optimal_difficulties:
            return {"message": "Insufficient high-performance data"}

        difficulties = [dp["difficulty"] for dp in optimal_difficulties]

        return {
            "min_difficulty": min(difficulties),
            "max_difficulty": max(difficulties),
            "average_optimal": sum(difficulties) / len(difficulties),
            "sample_size": len(optimal_difficulties)
        }

    def _assess_difficulty_adaptation_need(self, difficulty_performance: List[Dict]) -> str:
        """Assess if difficulty adaptation is needed."""
        recent_performance = difficulty_performance[-5:] if len(
            difficulty_performance) >= 5 else difficulty_performance

        avg_performance = sum(dp["performance"]
                              for dp in recent_performance) / len(recent_performance)

        if avg_performance > 0.85:
            return "increase_difficulty"
        elif avg_performance < 0.5:
            return "decrease_difficulty"
        else:
            return "maintain_current"

    def _generate_language_specific_insights(self, difficulty_performance: List[Dict]) -> Dict:
        """Generate language-specific difficulty insights."""
        english_data = [dp for dp in difficulty_performance if dp.get(
            "language") == "english"]
        japanese_data = [dp for dp in difficulty_performance if dp.get(
            "language") == "japanese"]

        insights = {}

        if english_data:
            avg_english_perf = sum(dp["performance"]
                                   for dp in english_data) / len(english_data)
            insights["english"] = {
                "average_performance": avg_english_perf,
                "sessions_count": len(english_data),
                "recommendation": "increase_difficulty" if avg_english_perf > 0.8 else "maintain" if avg_english_perf > 0.6 else "decrease_difficulty"
            }

        if japanese_data:
            avg_japanese_perf = sum(dp["performance"]
                                    for dp in japanese_data) / len(japanese_data)
            insights["japanese"] = {
                "average_performance": avg_japanese_perf,
                "sessions_count": len(japanese_data),
                "recommendation": "increase_difficulty" if avg_japanese_perf > 0.8 else "maintain" if avg_japanese_perf > 0.6 else "decrease_difficulty"
            }

        return insights

    def _analyze_behavioral_patterns(self, behaviors: List[ReadingBehavior]) -> Dict:
        """Analyze behavioral patterns from reading sessions."""
        if not behaviors:
            return {}

        # Analyze reading times
        reading_times = []
        for behavior in behaviors:
            if behavior.context and "time_of_day" in behavior.context:
                reading_times.append(behavior.context["time_of_day"])

        # Analyze devices used
        devices = []
        for behavior in behaviors:
            if behavior.context and "device_type" in behavior.context:
                devices.append(behavior.context["device_type"])

        # Analyze session lengths
        session_lengths = []
        for behavior in behaviors:
            if behavior.start_time and behavior.end_time:
                length = (behavior.end_time -
                          behavior.start_time).total_seconds() / 60
                session_lengths.append(length)

        patterns = {}

        if reading_times:
            time_counts = defaultdict(int)
            for time in reading_times:
                time_counts[time] += 1
            patterns["preferred_reading_times"] = dict(time_counts)

        if devices:
            device_counts = defaultdict(int)
            for device in devices:
                device_counts[device] += 1
            patterns["device_usage"] = dict(device_counts)

        if session_lengths:
            patterns["session_length_stats"] = {
                "average_minutes": sum(session_lengths) / len(session_lengths),
                "shortest_minutes": min(session_lengths),
                "longest_minutes": max(session_lengths)
            }

        return patterns

    async def assess_skill_progression(self, user_id: str, content_id: str,
                                       performance_data: Dict, db: Session) -> Dict:
        """Assess skill progression and recommend next difficulty level."""
        # Get user's recent performance in this topic/language
        content = db.query(ContentItem).filter(
            ContentItem.id == content_id).first()
        if not content:
            return {"error": "Content not found"}

        content_language = content.language or "english"
        content_topics = content.analysis.get(
            "topics", []) if content.analysis else []

        # Get recent behaviors for this user in similar content
        cutoff_date = datetime.utcnow() - timedelta(days=self.skill_development_window_days)
        recent_behaviors = db.query(ReadingBehavior).filter(
            and_(
                ReadingBehavior.user_id == user_id,
                ReadingBehavior.created_at >= cutoff_date,
                ReadingBehavior.end_time.isnot(None)
            )
        ).order_by(ReadingBehavior.created_at).all()

        # Filter behaviors by language and similar topics
        relevant_behaviors = []
        for behavior in recent_behaviors:
            behavior_content = db.query(ContentItem).filter(
                ContentItem.id == behavior.content_id).first()
            if behavior_content and behavior_content.language == content_language:
                relevant_behaviors.append(behavior)

        if len(relevant_behaviors) < 2:
            return {
                "progression_status": "insufficient_data",
                "recommendation": "continue_current_level",
                "reason": "Need more reading sessions to assess progression"
            }

        # Analyze performance trends
        performance_scores = []
        difficulty_levels = []

        for behavior in relevant_behaviors:
            if behavior.completion_rate is not None and behavior.reading_speed:
                # Calculate performance score for this session
                performance_score = self._calculate_session_performance_score(
                    behavior)
                performance_scores.append(performance_score)

                # Get content difficulty
                behavior_content = db.query(ContentItem).filter(
                    ContentItem.id == behavior.content_id).first()
                if behavior_content and behavior_content.analysis:
                    if content_language == "english":
                        difficulty = behavior_content.analysis.get(
                            "reading_level", {}).get("flesch_kincaid", 8.0)
                    else:
                        difficulty = behavior_content.analysis.get(
                            "reading_level", {}).get("kanji_density", 0.3)
                    difficulty_levels.append(difficulty)

        if not performance_scores:
            return {
                "progression_status": "insufficient_data",
                "recommendation": "continue_current_level"
            }

        # Calculate trends
        performance_trend = self._calculate_trend(performance_scores)
        difficulty_trend = self._calculate_trend(
            difficulty_levels) if difficulty_levels else {"trend": "stable"}

        # Determine progression recommendation
        current_performance = performance_data.get(
            "performance_score", performance_scores[-1])

        progression_assessment = {
            "progression_status": self._assess_progression_status(performance_trend, difficulty_trend),
            "current_performance": current_performance,
            "performance_trend": performance_trend,
            "difficulty_trend": difficulty_trend,
            "recommendation": self._generate_progression_recommendation(
                performance_trend, difficulty_trend, current_performance
            ),
            "confidence": self._calculate_progression_confidence(performance_scores, difficulty_levels)
        }

        return progression_assessment

    def _assess_progression_status(self, performance_trend: Dict, difficulty_trend: Dict) -> str:
        """Assess overall skill progression status."""
        perf_trend = performance_trend.get("trend", "stable")
        diff_trend = difficulty_trend.get("trend", "stable")

        if perf_trend == "improving" and diff_trend == "improving":
            return "excellent_progression"
        elif perf_trend == "improving":
            return "performance_improving"
        elif diff_trend == "improving" and perf_trend == "stable":
            return "handling_increased_difficulty"
        elif perf_trend == "declining":
            return "struggling"
        else:
            return "stable"

    def _generate_progression_recommendation(self, performance_trend: Dict,
                                             difficulty_trend: Dict, current_performance: float) -> Dict:
        """Generate specific progression recommendations."""
        perf_trend = performance_trend.get("trend", "stable")

        if current_performance > self.difficulty_adjustment_threshold and perf_trend == "improving":
            return {
                "action": "increase_difficulty",
                "reason": "Strong performance with improving trend indicates readiness for challenge",
                "suggested_increase": "moderate"
            }
        elif current_performance < self.struggle_threshold:
            return {
                "action": "decrease_difficulty",
                "reason": "Performance below threshold indicates current level is too challenging",
                "suggested_decrease": "significant"
            }
        elif perf_trend == "declining":
            return {
                "action": "stabilize_difficulty",
                "reason": "Declining performance suggests need to consolidate current skills",
                "suggested_action": "practice_current_level"
            }
        else:
            return {
                "action": "maintain_difficulty",
                "reason": "Performance is stable and appropriate for current level",
                "suggested_action": "continue_current_level"
            }

    def _calculate_progression_confidence(self, performance_scores: List[float],
                                          difficulty_levels: List[float]) -> float:
        """Calculate confidence in progression assessment."""
        if len(performance_scores) < 3:
            return 0.3  # Low confidence with few data points
        elif len(performance_scores) < 5:
            return 0.6  # Medium confidence
        else:
            # High confidence with sufficient data
            # Factor in consistency of performance
            performance_std = np.std(performance_scores) if len(
                performance_scores) > 1 else 0
            # Lower std = higher consistency
            consistency_factor = max(0.5, 1.0 - performance_std)
            return min(0.9, 0.7 + (consistency_factor * 0.2))

    async def track_adaptive_difficulty_adjustment(self, user_id: str, content_id: str,
                                                   original_difficulty: float, adjusted_difficulty: float,
                                                   adjustment_reason: str, db: Session) -> None:
        """Track adaptive difficulty adjustments for learning analytics."""
        # This could be stored in a separate table for analytics
        # For now, we'll add it to the user's reading behavior context
        adjustment_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "content_id": content_id,
            "original_difficulty": original_difficulty,
            "adjusted_difficulty": adjusted_difficulty,
            "adjustment_reason": adjustment_reason,
            "adjustment_magnitude": abs(adjusted_difficulty - original_difficulty)
        }

        # Store in user profile for analytics
        profile = await user_profile_engine.get_or_create_profile(user_id, db)
        if not hasattr(profile, 'difficulty_adjustments'):
            profile.difficulty_adjustments = []

        # Keep only recent adjustments (last 50)
        if len(profile.difficulty_adjustments) >= 50:
            profile.difficulty_adjustments = profile.difficulty_adjustments[-49:]

        profile.difficulty_adjustments.append(adjustment_record)
        db.commit()

    async def generate_personalized_learning_path(self, user_id: str, db: Session) -> Dict:
        """Generate a personalized learning path based on skill progression analysis."""
        # Get user profile and recent performance
        profile = await user_profile_engine.get_or_create_profile(user_id, db)

        # Analyze performance across different languages and topics
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        recent_behaviors = db.query(ReadingBehavior).filter(
            and_(
                ReadingBehavior.user_id == user_id,
                ReadingBehavior.created_at >= cutoff_date,
                ReadingBehavior.end_time.isnot(None)
            )
        ).all()

        if not recent_behaviors:
            return {"message": "Insufficient data for learning path generation"}

        # Group behaviors by language and topic
        language_performance = defaultdict(list)
        topic_performance = defaultdict(list)

        for behavior in recent_behaviors:
            content = db.query(ContentItem).filter(
                ContentItem.id == behavior.content_id).first()
            if content and behavior.completion_rate is not None:
                language = content.language or "english"
                language_performance[language].append({
                    "performance": self._calculate_session_performance_score(behavior),
                    "difficulty": self._extract_content_difficulty(content, language),
                    "timestamp": behavior.created_at
                })

                # Extract topics
                if content.analysis and "topics" in content.analysis:
                    for topic_data in content.analysis["topics"]:
                        topic = topic_data.get("topic", "general")
                        topic_performance[topic].append({
                            "performance": self._calculate_session_performance_score(behavior),
                            "difficulty": self._extract_content_difficulty(content, language),
                            "timestamp": behavior.created_at
                        })

        # Generate learning path recommendations
        learning_path = {
            "user_id": user_id,
            "generated_at": datetime.utcnow().isoformat(),
            "language_recommendations": self._generate_language_learning_recommendations(language_performance),
            "topic_recommendations": self._generate_topic_learning_recommendations(topic_performance),
            "overall_strategy": self._determine_overall_learning_strategy(language_performance, topic_performance),
            "next_milestones": self._identify_learning_milestones(profile, language_performance, topic_performance)
        }

        return learning_path

    def _extract_content_difficulty(self, content: ContentItem, language: str) -> float:
        """Extract difficulty level from content analysis."""
        if not content.analysis:
            return 8.0 if language == "english" else 0.3

        if language == "english":
            return content.analysis.get("reading_level", {}).get("flesch_kincaid", 8.0)
        else:
            return content.analysis.get("reading_level", {}).get("kanji_density", 0.3)

    def _generate_language_learning_recommendations(self, language_performance: Dict) -> Dict:
        """Generate language-specific learning recommendations."""
        recommendations = {}

        for language, performances in language_performance.items():
            if not performances:
                continue

            avg_performance = sum(p["performance"]
                                  for p in performances) / len(performances)
            recent_performances = sorted(
                performances, key=lambda x: x["timestamp"])[-5:]
            recent_avg = sum(p["performance"]
                             for p in recent_performances) / len(recent_performances)

            trend = "improving" if recent_avg > avg_performance else "stable" if abs(
                recent_avg - avg_performance) < 0.1 else "declining"

            if avg_performance > 0.8:
                recommendation = "ready_for_advanced_content"
            elif avg_performance > 0.6:
                recommendation = "continue_intermediate_level"
            else:
                recommendation = "focus_on_fundamentals"

            recommendations[language] = {
                "average_performance": avg_performance,
                "recent_trend": trend,
                "recommendation": recommendation,
                "sessions_analyzed": len(performances),
                "suggested_difficulty_adjustment": self._suggest_difficulty_adjustment(avg_performance, trend)
            }

        return recommendations

    def _generate_topic_learning_recommendations(self, topic_performance: Dict) -> Dict:
        """Generate topic-specific learning recommendations."""
        recommendations = {}

        for topic, performances in topic_performance.items():
            if len(performances) < 2:  # Need at least 2 sessions for meaningful analysis
                continue

            avg_performance = sum(p["performance"]
                                  for p in performances) / len(performances)
            performance_trend = self._calculate_trend(
                [p["performance"] for p in performances])

            if avg_performance > 0.8 and performance_trend.get("trend") == "improving":
                recommendation = "explore_advanced_topics"
            elif avg_performance > 0.6:
                recommendation = "continue_current_depth"
            else:
                recommendation = "build_foundational_knowledge"

            recommendations[topic] = {
                "average_performance": avg_performance,
                "trend": performance_trend,
                "recommendation": recommendation,
                "sessions_count": len(performances)
            }

        return recommendations

    def _determine_overall_learning_strategy(self, language_performance: Dict, topic_performance: Dict) -> Dict:
        """Determine overall learning strategy based on performance patterns."""
        # Calculate overall performance across all languages and topics
        all_performances = []
        for lang_perfs in language_performance.values():
            all_performances.extend([p["performance"] for p in lang_perfs])

        if not all_performances:
            return {"strategy": "insufficient_data"}

        overall_avg = sum(all_performances) / len(all_performances)
        performance_consistency = 1.0 - np.std(all_performances)

        if overall_avg > 0.8 and performance_consistency > 0.7:
            strategy = "accelerated_learning"
            focus = "Challenge yourself with advanced content across multiple topics"
        elif overall_avg > 0.6:
            strategy = "balanced_progression"
            focus = "Continue steady progression with occasional challenges"
        elif performance_consistency < 0.5:
            strategy = "consistency_building"
            focus = "Focus on building consistent performance before increasing difficulty"
        else:
            strategy = "foundational_strengthening"
            focus = "Strengthen fundamental skills before advancing"

        return {
            "strategy": strategy,
            "focus": focus,
            "overall_performance": overall_avg,
            "consistency_score": performance_consistency
        }

    def _identify_learning_milestones(self, profile: UserProfile, language_performance: Dict,
                                      topic_performance: Dict) -> List[Dict]:
        """Identify specific learning milestones for the user."""
        milestones = []

        # Language-based milestones
        for language, performances in language_performance.items():
            avg_perf = sum(p["performance"]
                           for p in performances) / len(performances)
            current_level = profile.reading_levels.get(
                language, {}).get("level", 0)

            if language == "english":
                if avg_perf > 0.8 and current_level < 12:
                    milestones.append({
                        "type": "language_advancement",
                        "language": language,
                        "milestone": "Advance to college-level reading",
                        "current_level": current_level,
                        "target_level": min(12, current_level + 2),
                        "estimated_sessions": 10
                    })
            else:  # Japanese
                if avg_perf > 0.8 and current_level < 0.7:
                    milestones.append({
                        "type": "language_advancement",
                        "language": language,
                        "milestone": "Advance to intermediate Japanese reading",
                        "current_level": current_level,
                        "target_level": min(0.7, current_level + 0.1),
                        "estimated_sessions": 15
                    })

        # Topic-based milestones
        strong_topics = [topic for topic, perfs in topic_performance.items()
                         if sum(p["performance"] for p in perfs) / len(perfs) > 0.8]

        if len(strong_topics) >= 3:
            milestones.append({
                "type": "topic_mastery",
                "milestone": "Explore interdisciplinary content",
                "strong_topics": strong_topics,
                "suggestion": "Try content that combines multiple areas of strength"
            })

        return milestones

    def _suggest_difficulty_adjustment(self, avg_performance: float, trend: str) -> str:
        """Suggest difficulty adjustment based on performance and trend."""
        if avg_performance > 0.8 and trend == "improving":
            return "increase_moderate"
        elif avg_performance > 0.7 and trend == "stable":
            return "increase_slight"
        elif avg_performance < 0.5:
            return "decrease_moderate"
        elif trend == "declining":
            return "decrease_slight"
        else:
            return "maintain"

    async def _generate_progress_recommendations(self, user_id: str, progress_metrics: Dict,
                                                 skill_trends: Dict, db: Session) -> List[Dict]:
        """Generate recommendations based on progress analysis."""
        recommendations = []

        # Completion rate recommendations
        completion_rate = progress_metrics.get("average_content_completion", 0)
        if completion_rate < 0.5:
            recommendations.append({
                "type": "completion_improvement",
                "message": "Focus on completing more content to build reading stamina",
                "priority": "high"
            })

        # Reading speed recommendations
        reading_speed = progress_metrics.get("average_reading_speed_wpm", 0)
        if reading_speed < 150:
            recommendations.append({
                "type": "speed_improvement",
                "message": "Practice reading exercises to improve reading speed",
                "priority": "medium"
            })
        elif reading_speed > 300:
            recommendations.append({
                "type": "comprehension_focus",
                "message": "Ensure comprehension isn't sacrificed for speed",
                "priority": "medium"
            })

        # Trend-based recommendations
        completion_trend = skill_trends.get(
            "completion_rate_trend", {}).get("trend")
        if completion_trend == "declining":
            recommendations.append({
                "type": "difficulty_adjustment",
                "message": "Consider easier content to rebuild confidence",
                "priority": "high"
            })
        elif completion_trend == "improving":
            recommendations.append({
                "type": "challenge_increase",
                "message": "Ready for more challenging content",
                "priority": "medium"
            })

        return recommendations
        """Generate recommendations based on progress analysis."""
        recommendations = []

        # Completion rate recommendations
        completion_rate = progress_metrics.get("average_content_completion", 0)
        if completion_rate < 0.5:
            recommendations.append({
                "type": "completion_improvement",
                "message": "Focus on completing more content to build reading stamina",
                "priority": "high"
            })

        # Reading speed recommendations
        reading_speed = progress_metrics.get("average_reading_speed_wpm", 0)
        if reading_speed < 150:
            recommendations.append({
                "type": "speed_improvement",
                "message": "Practice reading exercises to improve reading speed",
                "priority": "medium"
            })
        elif reading_speed > 300:
            recommendations.append({
                "type": "comprehension_focus",
                "message": "Ensure comprehension isn't sacrificed for speed",
                "priority": "medium"
            })

        # Trend-based recommendations
        completion_trend = skill_trends.get(
            "completion_rate_trend", {}).get("trend")
        if completion_trend == "declining":
            recommendations.append({
                "type": "difficulty_adjustment",
                "message": "Consider easier content to rebuild confidence",
                "priority": "high"
            })
        elif completion_trend == "improving":
            recommendations.append({
                "type": "challenge_increase",
                "message": "Ready for more challenging content",
                "priority": "medium"
            })

        return recommendations


# Global instance
reading_progress_tracker = ReadingProgressTracker()
