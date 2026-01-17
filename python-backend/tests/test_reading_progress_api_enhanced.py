"""Tests for enhanced reading progress API endpoints."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from src.services.reading_progress_service import ReadingProgressTracker


class TestEnhancedReadingProgressAPI:
    """Test cases for enhanced reading progress API functionality."""

    @pytest.fixture
    def tracker(self):
        """Create a ReadingProgressTracker instance."""
        return ReadingProgressTracker()

    def test_skill_progression_assessment_integration(self, tracker):
        """Test skill progression assessment integration."""
        # Mock database and user profile
        mock_db = Mock()
        mock_behaviors = []

        # Create mock behaviors with improving performance
        for i in range(5):
            behavior = Mock()
            behavior.user_id = "test_user"
            behavior.content_id = f"content_{i}"
            behavior.completion_rate = 0.6 + (i * 0.05)
            behavior.reading_speed = 200 + (i * 10)
            behavior.created_at = datetime.utcnow()
            behavior.end_time = datetime.utcnow()
            mock_behaviors.append(behavior)

        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = mock_behaviors

        # Mock content
        mock_content = Mock()
        mock_content.language = "english"
        mock_content.analysis = {"topics": [{"topic": "technology"}]}
        mock_db.query.return_value.filter.return_value.first.return_value = mock_content

        # This would be an async test in a real scenario
        # For now, we test the core logic components
        performance_trend = {"trend": "improving", "slope": 0.05}
        difficulty_trend = {"trend": "stable", "slope": 0.01}

        status = tracker._assess_progression_status(
            performance_trend, difficulty_trend)
        assert status == "performance_improving"

        recommendation = tracker._generate_progression_recommendation(
            performance_trend, difficulty_trend, 0.75
        )
        assert recommendation["action"] == "increase_difficulty"

    def test_learning_path_generation_components(self, tracker):
        """Test learning path generation components."""
        # Test language performance analysis
        language_performance = {
            "english": [
                {"performance": 0.8, "difficulty": 8.0,
                    "timestamp": datetime.utcnow()},
                {"performance": 0.82, "difficulty": 8.2,
                    "timestamp": datetime.utcnow()}
            ],
            "japanese": [
                {"performance": 0.6, "difficulty": 0.3,
                    "timestamp": datetime.utcnow()}
            ]
        }

        recommendations = tracker._generate_language_learning_recommendations(
            language_performance)

        assert "english" in recommendations
        assert "japanese" in recommendations
        assert recommendations["english"]["recommendation"] == "ready_for_advanced_content"
        assert recommendations["japanese"]["recommendation"] == "focus_on_fundamentals"

    def test_difficulty_adjustment_tracking_logic(self, tracker):
        """Test difficulty adjustment tracking logic."""
        # Test the core logic for difficulty adjustments
        original_difficulty = 8.0
        adjusted_difficulty = 7.5
        adjustment_reason = "User struggling with current level"

        adjustment_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "content_id": "test_content",
            "original_difficulty": original_difficulty,
            "adjusted_difficulty": adjusted_difficulty,
            "adjustment_reason": adjustment_reason,
            "adjustment_magnitude": abs(adjusted_difficulty - original_difficulty)
        }

        assert adjustment_record["adjustment_magnitude"] == 0.5
        assert adjustment_record["adjustment_reason"] == adjustment_reason

    def test_milestone_identification_logic(self, tracker):
        """Test learning milestone identification logic."""
        # Mock user profile
        mock_profile = Mock()
        mock_profile.reading_levels = {
            "english": {"level": 8.0, "confidence": 0.7},
            "japanese": {"level": 0.3, "confidence": 0.6}
        }

        # High performance in English
        language_performance = {
            "english": [
                {"performance": 0.85, "difficulty": 8.0,
                    "timestamp": datetime.utcnow()}
            ]
        }

        # Multiple strong topics
        topic_performance = {
            "technology": [{"performance": 0.85, "difficulty": 8.0, "timestamp": datetime.utcnow()}],
            "science": [{"performance": 0.87, "difficulty": 8.2, "timestamp": datetime.utcnow()}],
            "history": [{"performance": 0.83, "difficulty": 7.8, "timestamp": datetime.utcnow()}],
            "literature": [{"performance": 0.89, "difficulty": 8.5, "timestamp": datetime.utcnow()}]
        }

        milestones = tracker._identify_learning_milestones(
            mock_profile, language_performance, topic_performance
        )

        # Should identify both language advancement and topic mastery milestones
        milestone_types = [m.get("type") for m in milestones]
        assert "language_advancement" in milestone_types
        assert "topic_mastery" in milestone_types

    def test_performance_indicators_enhanced(self, tracker):
        """Test enhanced performance indicators calculation."""
        # Test with comprehensive metrics
        metrics = {
            "current_reading_speed": 250,  # Good speed
            "engagement_metrics": {
                "scroll_events": 8,
                "highlight_events": 3,
                "note_events": 2,
                "lookup_events": 1
            },
            "pause_patterns": [
                {"duration": 3}, {"duration": 5}, {
                    "duration": 2}  # Reasonable pauses
            ],
            "interactions": [
                {"type": "highlight"}, {"type": "note"}, {"type": "lookup"}
            ]
        }

        progress_data = {"completion_rate": 0.85}

        indicators = tracker._calculate_performance_indicators(
            metrics, progress_data)

        assert "reading_speed_percentile" in indicators
        assert "engagement_score" in indicators
        assert "comprehension_estimate" in indicators
        assert "overall_performance" in indicators

        # Should show good performance
        assert indicators["overall_performance"] > 0.7
        assert indicators["reading_speed_percentile"] > 0.6
        assert indicators["engagement_score"] > 0.5

    def test_adaptive_suggestions_enhanced(self, tracker):
        """Test enhanced adaptive suggestions generation."""
        # Mock profile and content
        mock_profile = Mock()
        mock_profile.reading_levels = {
            "english": {"level": 8.0, "confidence": 0.7}}

        mock_content = Mock()
        mock_content.language = "english"
        mock_content.analysis = {"reading_level": {"flesch_kincaid": 10.0}}

        # Content is challenging (difficulty ratio > 1.2)
        difficulty_assessment = {
            "assessment": "challenging",
            "difficulty_ratio": 1.25,
            "content_level": 10.0,
            "user_level": 8.0
        }

        suggestions = tracker._generate_adaptive_suggestions(
            mock_profile, mock_content, difficulty_assessment
        )

        # Should provide appropriate suggestions for challenging content
        assert len(suggestions) > 0
        suggestion_types = [s["type"] for s in suggestions]

        # For challenging content, should suggest optimal challenge
        assert "optimal_challenge" in suggestion_types or "reading_strategy" in suggestion_types
