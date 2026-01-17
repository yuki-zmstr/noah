"""Tests for enhanced reading progress tracking functionality."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock
from sqlalchemy.orm import Session

from src.services.reading_progress_service import ReadingProgressTracker
from src.models.user_profile import UserProfile, ReadingBehavior
from src.models.content import ContentItem


class TestEnhancedReadingProgressTracker:
    """Test cases for enhanced ReadingProgressTracker functionality."""

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
    def sample_behaviors(self):
        """Create sample reading behaviors for testing."""
        behaviors = []
        base_time = datetime.utcnow() - timedelta(days=10)

        for i in range(5):
            behavior = ReadingBehavior(
                user_id="test_user",
                content_id=f"content_{i}",
                session_id=f"session_{i}",
                start_time=base_time + timedelta(days=i),
                end_time=base_time + timedelta(days=i, hours=1),
                completion_rate=0.6 + (i * 0.05),  # Improving trend
                reading_speed=200 + (i * 10),  # Improving speed
                created_at=base_time + timedelta(days=i)
            )
            behaviors.append(behavior)

        return behaviors

    def test_assess_progression_status_excellent(self, tracker):
        """Test progression status assessment for excellent progression."""
        performance_trend = {"trend": "improving", "slope": 0.05}
        difficulty_trend = {"trend": "improving", "slope": 0.02}

        status = tracker._assess_progression_status(
            performance_trend, difficulty_trend)
        assert status == "excellent_progression"

    def test_assess_progression_status_struggling(self, tracker):
        """Test progression status assessment for struggling performance."""
        performance_trend = {"trend": "declining", "slope": -0.03}
        difficulty_trend = {"trend": "stable", "slope": 0.001}

        status = tracker._assess_progression_status(
            performance_trend, difficulty_trend)
        assert status == "struggling"

    def test_generate_progression_recommendation_increase_difficulty(self, tracker):
        """Test progression recommendation for increasing difficulty."""
        performance_trend = {"trend": "improving", "slope": 0.05}
        difficulty_trend = {"trend": "stable", "slope": 0.001}
        current_performance = 0.85

        recommendation = tracker._generate_progression_recommendation(
            performance_trend, difficulty_trend, current_performance
        )

        assert recommendation["action"] == "increase_difficulty"
        assert "readiness for challenge" in recommendation["reason"]
        assert recommendation["suggested_increase"] == "moderate"

    def test_generate_progression_recommendation_decrease_difficulty(self, tracker):
        """Test progression recommendation for decreasing difficulty."""
        performance_trend = {"trend": "stable", "slope": 0.001}
        difficulty_trend = {"trend": "stable", "slope": 0.001}
        current_performance = 0.3  # Below struggle threshold

        recommendation = tracker._generate_progression_recommendation(
            performance_trend, difficulty_trend, current_performance
        )

        assert recommendation["action"] == "decrease_difficulty"
        assert "too challenging" in recommendation["reason"]
        assert recommendation["suggested_decrease"] == "significant"

    def test_calculate_progression_confidence_high(self, tracker):
        """Test progression confidence calculation with sufficient data."""
        performance_scores = [0.7, 0.72, 0.75, 0.73,
                              0.76, 0.78]  # Consistent performance
        difficulty_levels = [8.0, 8.1, 8.2, 8.3, 8.4, 8.5]

        confidence = tracker._calculate_progression_confidence(
            performance_scores, difficulty_levels)

        assert confidence > 0.7  # Should be high confidence
        assert confidence <= 0.9  # But not exceed maximum

    def test_calculate_progression_confidence_low(self, tracker):
        """Test progression confidence calculation with insufficient data."""
        performance_scores = [0.7, 0.8]  # Only 2 data points
        difficulty_levels = [8.0, 8.5]

        confidence = tracker._calculate_progression_confidence(
            performance_scores, difficulty_levels)

        assert confidence == 0.3  # Low confidence with few data points

    def test_extract_content_difficulty_english(self, tracker):
        """Test content difficulty extraction for English content."""
        content = ContentItem(
            id="test",
            title="Test",
            content="Test content",
            language="english",
            analysis={"reading_level": {"flesch_kincaid": 9.5}}
        )

        difficulty = tracker._extract_content_difficulty(content, "english")
        assert difficulty == 9.5

    def test_extract_content_difficulty_japanese(self, tracker):
        """Test content difficulty extraction for Japanese content."""
        content = ContentItem(
            id="test",
            title="Test",
            content="Test content",
            language="japanese",
            analysis={"reading_level": {"kanji_density": 0.4}}
        )

        difficulty = tracker._extract_content_difficulty(content, "japanese")
        assert difficulty == 0.4

    def test_extract_content_difficulty_no_analysis(self, tracker):
        """Test content difficulty extraction when no analysis is available."""
        content = ContentItem(
            id="test",
            title="Test",
            content="Test content",
            language="english",
            analysis=None
        )

        difficulty = tracker._extract_content_difficulty(content, "english")
        assert difficulty == 8.0  # Default for English

    def test_generate_language_learning_recommendations(self, tracker):
        """Test language-specific learning recommendations."""
        language_performance = {
            "english": [
                {"performance": 0.85, "difficulty": 8.0,
                    "timestamp": datetime.utcnow()},
                {"performance": 0.87, "difficulty": 8.2,
                    "timestamp": datetime.utcnow()},
                {"performance": 0.89, "difficulty": 8.5,
                    "timestamp": datetime.utcnow()}
            ],
            "japanese": [
                {"performance": 0.6, "difficulty": 0.3,
                    "timestamp": datetime.utcnow()},
                {"performance": 0.55, "difficulty": 0.35,
                    "timestamp": datetime.utcnow()}
            ]
        }

        recommendations = tracker._generate_language_learning_recommendations(
            language_performance)

        assert "english" in recommendations
        assert "japanese" in recommendations
        assert recommendations["english"]["recommendation"] == "ready_for_advanced_content"
        assert recommendations["japanese"]["recommendation"] == "continue_intermediate_level"

    def test_determine_overall_learning_strategy_accelerated(self, tracker):
        """Test overall learning strategy determination for accelerated learning."""
        language_performance = {
            "english": [
                {"performance": 0.85, "difficulty": 8.0,
                    "timestamp": datetime.utcnow()},
                {"performance": 0.87, "difficulty": 8.2,
                    "timestamp": datetime.utcnow()}
            ]
        }
        topic_performance = {
            "technology": [
                {"performance": 0.9, "difficulty": 8.5,
                    "timestamp": datetime.utcnow()}
            ]
        }

        strategy = tracker._determine_overall_learning_strategy(
            language_performance, topic_performance)

        assert strategy["strategy"] == "accelerated_learning"
        assert "advanced content" in strategy["focus"]
        assert strategy["overall_performance"] > 0.8

    def test_suggest_difficulty_adjustment_increase_moderate(self, tracker):
        """Test difficulty adjustment suggestion for moderate increase."""
        suggestion = tracker._suggest_difficulty_adjustment(0.85, "improving")
        assert suggestion == "increase_moderate"

    def test_suggest_difficulty_adjustment_decrease_moderate(self, tracker):
        """Test difficulty adjustment suggestion for moderate decrease."""
        suggestion = tracker._suggest_difficulty_adjustment(0.4, "stable")
        assert suggestion == "decrease_moderate"

    def test_suggest_difficulty_adjustment_maintain(self, tracker):
        """Test difficulty adjustment suggestion for maintaining current level."""
        suggestion = tracker._suggest_difficulty_adjustment(0.7, "stable")
        assert suggestion == "maintain"

    def test_identify_learning_milestones_english_advancement(self, tracker, sample_user_profile):
        """Test learning milestone identification for English advancement."""
        language_performance = {
            "english": [
                {"performance": 0.85, "difficulty": 8.0,
                    "timestamp": datetime.utcnow()},
                {"performance": 0.87, "difficulty": 8.2,
                    "timestamp": datetime.utcnow()}
            ]
        }
        topic_performance = {}

        milestones = tracker._identify_learning_milestones(
            sample_user_profile, language_performance, topic_performance
        )

        # Should suggest advancement to college-level reading
        english_milestones = [
            m for m in milestones if m.get("language") == "english"]
        assert len(english_milestones) > 0
        assert "college-level" in english_milestones[0]["milestone"]

    def test_identify_learning_milestones_topic_mastery(self, tracker, sample_user_profile):
        """Test learning milestone identification for topic mastery."""
        language_performance = {"english": [
            {"performance": 0.7, "difficulty": 8.0, "timestamp": datetime.utcnow()}]}
        topic_performance = {
            "technology": [{"performance": 0.85, "difficulty": 8.0, "timestamp": datetime.utcnow()}],
            "science": [{"performance": 0.87, "difficulty": 8.2, "timestamp": datetime.utcnow()}],
            "history": [{"performance": 0.83, "difficulty": 7.8, "timestamp": datetime.utcnow()}],
            "literature": [{"performance": 0.89, "difficulty": 8.5, "timestamp": datetime.utcnow()}]
        }

        milestones = tracker._identify_learning_milestones(
            sample_user_profile, language_performance, topic_performance
        )

        # Should suggest interdisciplinary content
        topic_milestones = [m for m in milestones if m.get(
            "type") == "topic_mastery"]
        assert len(topic_milestones) > 0
        assert "interdisciplinary" in topic_milestones[0]["milestone"]
        assert len(topic_milestones[0]["strong_topics"]) >= 3
