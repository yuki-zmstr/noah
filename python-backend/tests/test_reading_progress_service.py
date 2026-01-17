"""Tests for reading progress tracking service."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock
from sqlalchemy.orm import Session

from src.services.reading_progress_service import ReadingProgressTracker
from src.models.user_profile import UserProfile, ReadingBehavior
from src.models.content import ContentItem
from src.schemas.user_profile import ReadingContext


class TestReadingProgressTracker:
    """Test cases for ReadingProgressTracker."""

    @pytest.fixture
    def tracker(self):
        """Create a ReadingProgressTracker instance."""
        return ReadingProgressTracker()

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return Mock(spec=Session)

    @pytest.fixture
    def sample_user_profile(self):
        """Create a sample user profile."""
        return UserProfile(
            user_id="test_user",
            preferences={
                "topics": [],
                "content_types": [],
                "contextual_preferences": [],
                "evolution_history": []
            },
            reading_levels={
                "english": {"level": 8.0, "confidence": 0.7, "assessment_count": 5},
                "japanese": {"level": 0.3, "confidence": 0.6, "assessment_count": 3}
            }
        )

    @pytest.fixture
    def sample_content(self):
        """Create a sample content item."""
        return ContentItem(
            id="test_content",
            title="Test Article",
            content="This is a test article for reading progress tracking.",
            language="english",
            analysis={
                "reading_level": {"flesch_kincaid": 8.5},
                "topics": [{"topic": "technology", "confidence": 0.8}]
            },
            content_metadata={"content_type": "article",
                              "author": "Test Author"}
        )

    @pytest.fixture
    def sample_reading_context(self):
        """Create a sample reading context."""
        return ReadingContext(
            time_of_day="morning",
            device_type="desktop",
            location="home",
            available_time=30,
            user_mood="focused"
        )

    def test_difficulty_assessment_appropriate(self, tracker, sample_user_profile, sample_content):
        """Test content difficulty assessment when content is appropriate."""
        # Content level (8.5) vs user level (8.0) should be "appropriate"
        result = tracker._assess_content_difficulty(
            sample_user_profile, sample_content, None
        )

        assert result["assessment"] == "appropriate"
        assert result["content_level"] == 8.5
        assert result["user_level"] == 8.0
        assert result["language"] == "english"

    def test_difficulty_assessment_too_difficult(self, tracker, sample_user_profile, sample_content):
        """Test content difficulty assessment when content is too difficult."""
        # Modify content to be much more difficult
        sample_content.analysis["reading_level"]["flesch_kincaid"] = 15.0

        result = tracker._assess_content_difficulty(
            sample_user_profile, sample_content, None
        )

        assert result["assessment"] == "too_difficult"
        assert result["difficulty_ratio"] > 1.5

    def test_difficulty_assessment_too_easy(self, tracker, sample_user_profile, sample_content):
        """Test content difficulty assessment when content is too easy."""
        # Modify content to be much easier
        sample_content.analysis["reading_level"]["flesch_kincaid"] = 4.0

        result = tracker._assess_content_difficulty(
            sample_user_profile, sample_content, None
        )

        assert result["assessment"] == "too_easy"
        assert result["difficulty_ratio"] < 0.8

    def test_difficulty_assessment_with_context(self, tracker, sample_user_profile,
                                                sample_content, sample_reading_context):
        """Test content difficulty assessment with context adjustments."""
        # Test with tired mood (should prefer easier content)
        tired_context = ReadingContext(
            time_of_day="evening",
            device_type="mobile",
            user_mood="tired",
            available_time=10
        )

        result = tracker._assess_content_difficulty(
            sample_user_profile, sample_content, tired_context
        )

        # Should adjust difficulty down due to tired mood and short time
        assert result["adjusted_ratio"] < result["difficulty_ratio"]

    def test_adaptive_suggestions_too_difficult(self, tracker, sample_user_profile, sample_content):
        """Test adaptive suggestions for content that's too difficult."""
        difficulty_assessment = {
            "assessment": "too_difficult",
            "difficulty_ratio": 2.0
        }

        suggestions = tracker._generate_adaptive_suggestions(
            sample_user_profile, sample_content, difficulty_assessment
        )

        # Should suggest content adaptation and reading strategies
        suggestion_types = [s["type"] for s in suggestions]
        assert "content_adaptation" in suggestion_types
        assert "reading_strategy" in suggestion_types
        assert any(s["priority"] == "high" for s in suggestions)

    def test_adaptive_suggestions_too_easy(self, tracker, sample_user_profile, sample_content):
        """Test adaptive suggestions for content that's too easy."""
        difficulty_assessment = {
            "assessment": "too_easy",
            "difficulty_ratio": 0.5
        }

        suggestions = tracker._generate_adaptive_suggestions(
            sample_user_profile, sample_content, difficulty_assessment
        )

        # Should suggest complexity increase
        suggestion_types = [s["type"] for s in suggestions]
        assert "complexity_increase" in suggestion_types

    def test_behavioral_metrics_update(self, tracker):
        """Test updating behavioral metrics with progress data."""
        behavior = ReadingBehavior(
            pause_patterns=[],
            interactions=[],
            reading_speed=0.0
        )

        progress_data = {
            "pause_event": {"type": "thinking", "duration": 5},
            "interaction_event": {"type": "highlight", "text": "important point"},
            "engagement_data": {"scroll_events": 3, "highlight_events": 1},
            "words_read": 150,
            "time_elapsed": 60  # 1 minute
        }

        metrics = tracker._update_behavioral_metrics(behavior, progress_data)

        assert len(metrics["pause_patterns"]) == 1
        assert len(metrics["interactions"]) == 1
        assert metrics["current_reading_speed"] == 150.0  # 150 WPM
        assert metrics["engagement_metrics"]["scroll_events"] == 3

    def test_performance_indicators_calculation(self, tracker):
        """Test calculation of performance indicators."""
        metrics = {
            "current_reading_speed": 250,  # Good speed
            "engagement_metrics": {"scroll_events": 5, "highlight_events": 2},
            # Moderate pauses
            "pause_patterns": [{"duration": 3}, {"duration": 5}],
            "interactions": [{"type": "highlight"}, {"type": "note"}]
        }

        progress_data = {"completion_rate": 0.8}

        indicators = tracker._calculate_performance_indicators(
            metrics, progress_data)

        assert "reading_speed_percentile" in indicators
        assert "engagement_score" in indicators
        assert "comprehension_estimate" in indicators
        assert "overall_performance" in indicators
        assert 0 <= indicators["overall_performance"] <= 1

    def test_pause_pattern_analysis(self, tracker):
        """Test analysis of pause patterns."""
        pause_patterns = [
            {"duration": 3},   # short
            {"duration": 15},  # medium
            {"duration": 45},  # long
            {"duration": 2},   # short
            {"duration": 20}   # medium
        ]

        analysis = tracker._analyze_pause_patterns(pause_patterns)

        assert analysis["total_pauses"] == 5
        assert analysis["pause_distribution"]["short"] == 2
        assert analysis["pause_distribution"]["medium"] == 2
        assert analysis["pause_distribution"]["long"] == 1
        assert "interpretation" in analysis

    def test_interaction_analysis(self, tracker):
        """Test analysis of user interactions."""
        interactions = [
            {"type": "highlight"},
            {"type": "note"},
            {"type": "highlight"},
            {"type": "lookup"},
            {"type": "bookmark"}
        ]

        analysis = tracker._analyze_interactions(interactions)

        assert analysis["total_interactions"] == 5
        assert analysis["interaction_types"]["highlight"] == 2
        assert analysis["interaction_types"]["note"] == 1
        assert "engagement_level" in analysis
        assert "learning_indicators" in analysis

    def test_session_performance_score_calculation(self, tracker):
        """Test calculation of session performance score."""
        behavior = ReadingBehavior(
            completion_rate=0.9,
            reading_speed=220,
            pause_patterns=[{"duration": 5}],  # One moderate pause
            interactions=[{"type": "highlight"}, {
                "type": "note"}]  # Good engagement
        )

        score = tracker._calculate_session_performance_score(behavior)

        assert 0 <= score <= 1
        # Should be a good score given high completion rate and decent speed
        assert score > 0.6

    def test_skill_development_indicators(self, tracker):
        """Test identification of skill development indicators."""
        behavior = ReadingBehavior(reading_speed=250)

        pause_analysis = {
            "pause_frequency": 0.15,
            "total_pauses": 3
        }

        interaction_analysis = {
            "engagement_level": "high",
            "learning_indicators": ["active_highlighting", "note_taking"]
        }

        indicators = tracker._identify_skill_development_indicators(
            behavior, pause_analysis, interaction_analysis
        )

        assert indicators["reading_fluency"] == "good"  # 250 WPM is good
        # 0.15 frequency is reasonable
        assert indicators["comprehension_flow"] == "good"
        assert indicators["engagement"] == "high"
        assert indicators["active_learning"] is True

    def test_trend_calculation(self, tracker):
        """Test trend calculation for skill development."""
        # Improving trend
        improving_values = [0.6, 0.65, 0.7, 0.75, 0.8]
        trend = tracker._calculate_trend(improving_values)

        assert trend["trend"] == "improving"
        assert trend["slope"] > 0
        assert trend["change_percentage"] > 0

        # Declining trend
        declining_values = [0.8, 0.75, 0.7, 0.65, 0.6]
        trend = tracker._calculate_trend(declining_values)

        assert trend["trend"] == "declining"
        assert trend["slope"] < 0
        assert trend["change_percentage"] < 0

        # Stable trend
        stable_values = [0.7, 0.71, 0.69, 0.7, 0.71]
        trend = tracker._calculate_trend(stable_values)

        assert trend["trend"] == "stable"

    def test_progress_metrics_calculation(self, tracker):
        """Test calculation of progress metrics from behaviors."""
        behaviors = []

        # Create sample behaviors
        for i in range(5):
            behavior = ReadingBehavior(
                start_time=datetime.utcnow() - timedelta(hours=i),
                end_time=datetime.utcnow() - timedelta(hours=i) + timedelta(minutes=30),
                completion_rate=0.8 + (i * 0.02),  # Slightly improving
                reading_speed=200 + (i * 10)  # Improving speed
            )
            behaviors.append(behavior)

        metrics = tracker._calculate_progress_metrics(behaviors)

        assert metrics["total_sessions"] == 5
        assert metrics["completed_sessions"] == 5
        assert metrics["completion_rate"] == 1.0  # All completed
        assert metrics["average_content_completion"] > 0.8
        assert metrics["average_reading_speed_wpm"] > 200

    def test_optimal_difficulty_range_finding(self, tracker):
        """Test finding optimal difficulty range for user."""
        difficulty_performance = [
            {"difficulty": 6.0, "performance": 0.9},  # Easy, high performance
            {"difficulty": 8.0, "performance": 0.85},  # Medium, high performance
            {"difficulty": 10.0, "performance": 0.7},  # Hard, medium performance
            # Very hard, low performance
            {"difficulty": 12.0, "performance": 0.4},
        ]

        optimal_range = tracker._find_optimal_difficulty_range(
            difficulty_performance)

        assert optimal_range["min_difficulty"] == 6.0
        # Only includes high/medium performance
        assert optimal_range["max_difficulty"] == 10.0
        assert optimal_range["sample_size"] == 3

    def test_difficulty_adaptation_assessment(self, tracker):
        """Test assessment of difficulty adaptation needs."""
        # High performance - should increase difficulty
        high_performance = [
            {"performance": 0.9}, {"performance": 0.88}, {"performance": 0.92}
        ]

        result = tracker._assess_difficulty_adaptation_need(high_performance)
        assert result == "increase_difficulty"

        # Low performance - should decrease difficulty
        low_performance = [
            {"performance": 0.4}, {"performance": 0.3}, {"performance": 0.45}
        ]

        result = tracker._assess_difficulty_adaptation_need(low_performance)
        assert result == "decrease_difficulty"

        # Medium performance - should maintain
        medium_performance = [
            {"performance": 0.7}, {"performance": 0.65}, {"performance": 0.72}
        ]

        result = tracker._assess_difficulty_adaptation_need(medium_performance)
        assert result == "maintain_current"

    def test_language_specific_insights(self, tracker):
        """Test generation of language-specific insights."""
        difficulty_performance = [
            {"difficulty": 8.0, "performance": 0.8, "language": "english"},
            {"difficulty": 9.0, "performance": 0.75, "language": "english"},
            {"difficulty": 0.3, "performance": 0.9, "language": "japanese"},
            {"difficulty": 0.4, "performance": 0.85, "language": "japanese"}
        ]

        insights = tracker._generate_language_specific_insights(
            difficulty_performance)

        assert "english" in insights
        assert "japanese" in insights
        assert insights["english"]["sessions_count"] == 2
        assert insights["japanese"]["sessions_count"] == 2
        assert "recommendation" in insights["english"]
        assert "recommendation" in insights["japanese"]
