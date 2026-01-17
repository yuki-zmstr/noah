"""Tests for reading progress API endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from src.main import app
from src.schemas.user_profile import ReadingContext


class TestReadingProgressAPI:
    """Test cases for reading progress API endpoints."""

    @pytest.fixture
    def client(self):
        """Create a test client."""
        return TestClient(app)

    @pytest.fixture
    def sample_session_data(self):
        """Sample session data for testing."""
        return {
            "session_id": "test_session_123",
            "behavior_id": 1,
            "content_title": "Test Article",
            "difficulty_assessment": {
                "assessment": "appropriate",
                "difficulty_ratio": 1.1,
                "content_level": 8.5,
                "user_level": 8.0,
                "language": "english",
                "confidence": 0.7
            },
            "adaptive_suggestions": [
                {
                    "type": "optimal_challenge",
                    "suggestion": "This content is at an optimal difficulty level",
                    "priority": "info"
                }
            ],
            "tracking_metrics": {
                "start_time": datetime.utcnow().isoformat(),
                "pause_patterns": [],
                "interactions": [],
                "engagement_metrics": {}
            }
        }

    @patch('src.services.reading_progress_service.reading_progress_tracker.start_reading_session')
    def test_start_reading_session_success(self, mock_start_session, client, sample_session_data):
        """Test successful reading session start."""
        mock_start_session.return_value = sample_session_data

        request_data = {
            "user_id": "test_user",
            "content_id": "test_content",
            "context": {
                "time_of_day": "morning",
                "device_type": "desktop",
                "location": "home",
                "available_time": 30,
                "user_mood": "focused"
            }
        }

        response = client.post(
            "/reading-progress/sessions/start", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "session_id" in data["data"]
        assert data["data"]["content_title"] == "Test Article"

    @patch('src.services.reading_progress_service.reading_progress_tracker.start_reading_session')
    def test_start_reading_session_content_not_found(self, mock_start_session, client):
        """Test reading session start with non-existent content."""
        mock_start_session.side_effect = ValueError(
            "Content test_content not found")

        request_data = {
            "user_id": "test_user",
            "content_id": "nonexistent_content"
        }

        response = client.post(
            "/reading-progress/sessions/start", json=request_data)

        assert response.status_code == 400
        assert "Content test_content not found" in response.json()["detail"]

    @patch('src.services.reading_progress_service.reading_progress_tracker.update_reading_progress')
    def test_update_reading_progress_success(self, mock_update_progress, client):
        """Test successful reading progress update."""
        mock_update_progress.return_value = {
            "session_id": "test_session_123",
            "performance_indicators": {
                "reading_speed_percentile": 0.7,
                "engagement_score": 0.6,
                "comprehension_estimate": 0.8,
                "overall_performance": 0.7
            },
            "adaptive_adjustments": [],
            "behavioral_metrics": {
                "pause_patterns": [{"type": "thinking", "duration": 5}],
                "interactions": [{"type": "highlight"}],
                "current_reading_speed": 220
            },
            "recommendations": [
                {
                    "type": "positive_feedback",
                    "message": "Good reading pace!",
                    "priority": "info"
                }
            ]
        }

        request_data = {
            "session_id": "test_session_123",
            "progress_data": {
                "completion_rate": 0.5,
                "words_read": 150,
                "time_elapsed": 60,
                "pause_event": {"type": "thinking", "duration": 5},
                "interaction_event": {"type": "highlight", "text": "important"}
            }
        }

        response = client.put(
            "/reading-progress/sessions/progress", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "performance_indicators" in data["data"]
        assert data["data"]["performance_indicators"]["overall_performance"] == 0.7

    @patch('src.services.reading_progress_service.reading_progress_tracker.update_reading_progress')
    def test_update_reading_progress_session_not_found(self, mock_update_progress, client):
        """Test reading progress update with non-existent session."""
        mock_update_progress.side_effect = ValueError(
            "Reading session nonexistent_session not found")

        request_data = {
            "session_id": "nonexistent_session",
            "progress_data": {"completion_rate": 0.5}
        }

        response = client.put(
            "/reading-progress/sessions/progress", json=request_data)

        assert response.status_code == 400
        assert "Reading session nonexistent_session not found" in response.json()[
            "detail"]

    @patch('src.services.reading_progress_service.reading_progress_tracker.complete_reading_session')
    def test_complete_reading_session_success(self, mock_complete_session, client):
        """Test successful reading session completion."""
        mock_complete_session.return_value = {
            "session_id": "test_session_123",
            "session_duration_minutes": 25.5,
            "completion_rate": 0.9,
            "session_analysis": {
                "performance_score": 0.8,
                "session_quality": "good",
                "skill_development_indicators": {
                    "reading_fluency": "good",
                    "comprehension_flow": "excellent",
                    "engagement": "high"
                }
            },
            "skill_insights": {
                "completion_rate_trend": {"trend": "improving"},
                "reading_speed_trend": {"trend": "stable"}
            },
            "difficulty_recommendations": {
                "next_difficulty": "maintain",
                "reason": "Current difficulty level appears appropriate"
            },
            "next_content_suggestions": [
                {
                    "type": "continue_level",
                    "message": "Continue with similar difficulty level content",
                    "priority": "medium"
                }
            ]
        }

        request_data = {
            "session_id": "test_session_123",
            "completion_data": {
                "completion_rate": 0.9,
                "final_reading_speed": 230
            }
        }

        response = client.post(
            "/reading-progress/sessions/complete", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["completion_rate"] == 0.9
        assert data["data"]["session_analysis"]["session_quality"] == "good"

    @patch('src.services.reading_progress_service.reading_progress_tracker.get_progress_analytics')
    def test_get_progress_analytics_success(self, mock_get_analytics, client):
        """Test successful progress analytics retrieval."""
        mock_get_analytics.return_value = {
            "user_id": "test_user",
            "analysis_period_days": 30,
            "total_sessions": 15,
            "progress_metrics": {
                "total_sessions": 15,
                "completed_sessions": 12,
                "completion_rate": 0.8,
                "average_content_completion": 0.85,
                "average_reading_speed_wpm": 220,
                "average_session_duration_minutes": 28.5,
                "total_reading_time_hours": 5.7
            },
            "skill_development_trends": {
                "completion_rate_trend": {"trend": "improving", "change_percentage": 15.2},
                "reading_speed_trend": {"trend": "stable", "change_percentage": 2.1},
                "skill_development_summary": "Good progress - comprehension is improving steadily"
            },
            "difficulty_insights": {
                "optimal_difficulty_range": {
                    "min_difficulty": 7.0,
                    "max_difficulty": 9.5,
                    "average_optimal": 8.2
                },
                "difficulty_adaptation_needed": "maintain_current"
            },
            "behavioral_patterns": {
                "preferred_reading_times": {"morning": 8, "evening": 4},
                "device_usage": {"desktop": 10, "mobile": 5},
                "session_length_stats": {
                    "average_minutes": 28.5,
                    "shortest_minutes": 15.0,
                    "longest_minutes": 45.0
                }
            },
            "recommendations": [
                {
                    "type": "challenge_increase",
                    "message": "Ready for more challenging content",
                    "priority": "medium"
                }
            ]
        }

        response = client.get(
            "/reading-progress/analytics/test_user?time_period_days=30")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["user_id"] == "test_user"
        assert data["data"]["total_sessions"] == 15
        assert "progress_metrics" in data["data"]
        assert "skill_development_trends" in data["data"]

    @patch('src.database.get_db')
    def test_get_session_status_success(self, mock_get_db, client):
        """Test successful session status retrieval."""
        # Mock database and behavior
        mock_db = Mock()
        mock_get_db.return_value = mock_db

        mock_behavior = Mock()
        mock_behavior.session_id = "test_session_123"
        mock_behavior.user_id = "test_user"
        mock_behavior.content_id = "test_content"
        mock_behavior.start_time = datetime(2024, 1, 1, 10, 0, 0)
        mock_behavior.end_time = None
        mock_behavior.completion_rate = 0.6
        mock_behavior.reading_speed = 200
        mock_behavior.context = {"device_type": "desktop"}

        mock_db.query.return_value.filter.return_value.first.return_value = mock_behavior

        response = client.get(
            "/reading-progress/sessions/test_session_123/status")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["session_id"] == "test_session_123"
        assert data["data"]["user_id"] == "test_user"
        assert data["data"]["is_completed"] is False

    @patch('src.database.get_db')
    def test_get_session_status_not_found(self, mock_get_db, client):
        """Test session status retrieval for non-existent session."""
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None

        response = client.get(
            "/reading-progress/sessions/nonexistent_session/status")

        assert response.status_code == 404
        assert "Reading session not found" in response.json()["detail"]

    @patch('src.database.get_db')
    def test_get_recent_sessions_success(self, mock_get_db, client):
        """Test successful recent sessions retrieval."""
        mock_db = Mock()
        mock_get_db.return_value = mock_db

        # Mock recent sessions
        mock_sessions = []
        for i in range(3):
            session = Mock()
            session.session_id = f"session_{i}"
            session.content_id = f"content_{i}"
            session.start_time = datetime(2024, 1, i+1, 10, 0, 0)
            session.end_time = datetime(
                2024, 1, i+1, 10, 30, 0) if i < 2 else None
            session.completion_rate = 0.8 + (i * 0.05)
            session.reading_speed = 200 + (i * 10)
            session.created_at = datetime(2024, 1, i+1, 10, 0, 0)
            mock_sessions.append(session)

        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = mock_sessions

        response = client.get(
            "/reading-progress/users/test_user/recent-sessions?limit=5")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["user_id"] == "test_user"
        assert len(data["data"]["sessions"]) == 3
        assert data["data"]["sessions"][0]["session_id"] == "session_0"

    @patch('src.services.reading_progress_service.reading_progress_tracker._generate_skill_development_insights')
    def test_get_skill_insights_success(self, mock_get_insights, client):
        """Test successful skill insights retrieval."""
        mock_get_insights.return_value = {
            "completion_rate_trend": {
                "trend": "improving",
                "slope": 0.02,
                "change_percentage": 12.5
            },
            "reading_speed_trend": {
                "trend": "stable",
                "slope": 0.001,
                "change_percentage": 1.2
            },
            "difficulty_progression": {
                "trend": "improving",
                "change_percentage": 8.3
            }
        }

        response = client.get(
            "/reading-progress/users/test_user/skill-insights")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "completion_rate_trend" in data["data"]
        assert data["data"]["completion_rate_trend"]["trend"] == "improving"

    @patch('src.database.get_db')
    @patch('src.services.reading_progress_service.reading_progress_tracker._analyze_completed_session')
    @patch('src.services.reading_progress_service.reading_progress_tracker._update_difficulty_recommendations')
    def test_get_difficulty_recommendations_success(self, mock_update_recommendations,
                                                    mock_analyze_session, mock_get_db, client):
        """Test successful difficulty recommendations retrieval."""
        # Mock database
        mock_db = Mock()
        mock_get_db.return_value = mock_db

        # Mock recent behavior
        mock_behavior = Mock()
        mock_behavior.session_id = "recent_session"
        mock_behavior.user_id = "test_user"
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_behavior

        # Mock session analysis
        mock_analyze_session.return_value = {
            "performance_score": 0.75,
            "session_quality": "good"
        }

        # Mock difficulty recommendations
        mock_update_recommendations.return_value = {
            "next_difficulty": "maintain",
            "reason": "Current difficulty level appears appropriate",
            "progression_note": "User is successfully handling increasing difficulty"
        }

        response = client.get(
            "/reading-progress/users/test_user/difficulty-recommendations")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["user_id"] == "test_user"
        assert data["data"]["session_performance"] == 0.75
        assert data["data"]["recommendations"]["next_difficulty"] == "maintain"

    @patch('src.database.get_db')
    def test_get_difficulty_recommendations_no_recent_sessions(self, mock_get_db, client):
        """Test difficulty recommendations when no recent sessions exist."""
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

        response = client.get(
            "/reading-progress/users/test_user/difficulty-recommendations")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "No recent completed sessions found" in data["data"]["message"]
