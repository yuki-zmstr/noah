# Noah Reading Agent - Backend API Documentation

## Overview

The Noah Reading Agent backend provides a comprehensive REST API for managing user profiles, content, conversations, recommendations, and reading progress tracking. The API is built with FastAPI and follows RESTful principles with comprehensive error handling and monitoring.

**Base URL**: `/api/v1`

## Table of Contents

1. [Authentication & Configuration](#authentication--configuration)
2. [User Management APIs](#user-management-apis)
3. [Content Management APIs](#content-management-apis)
4. [Content Storage APIs](#content-storage-apis)
5. [Conversation APIs](#conversation-apis)
6. [Chat Streaming APIs](#chat-streaming-apis)
7. [Recommendation APIs](#recommendation-apis)
8. [Reading Progress APIs](#reading-progress-apis)
9. [Preference Management APIs](#preference-management-apis)
10. [Agent Configuration APIs](#agent-configuration-apis)
11. [Monitoring & Health APIs](#monitoring--health-apis)
12. [Data Models](#data-models)
13. [Error Handling](#error-handling)

---

## Authentication & Configuration

### Get Application Configuration

```http
GET /api/config
```

Returns frontend configuration including feature flags and agent settings.

**Response:**

```json
{
  "app_name": "Noah Reading Agent",
  "version": "0.1.0",
  "debug": false,
  "cors_origins": ["https://example.com"],
  "features": {
    "aws_agent_core": true,
    "strands_agents": true,
    "multilingual_support": true,
    "discovery_mode": true,
    "streaming_responses": true
  },
  "agent_config": {
    "strands_enabled": true,
    "model": "claude-3-sonnet",
    "streaming": true
  }
}
```

### Debug Headers (Development Only)

```http
GET /api/debug/headers
```

Returns request headers for debugging proxy configuration (only available in debug mode).

---

## User Management APIs

### Create User Profile

```http
POST /api/v1/users/
```

**Request Body:**

```json
{
  "user_id": "user123",
  "preferences": {
    "topics": [
      {
        "topic": "science fiction",
        "weight": 0.8,
        "confidence": 0.9,
        "last_updated": "2024-01-01T00:00:00Z",
        "evolution_trend": "increasing"
      }
    ],
    "content_types": [
      {
        "type": "novel",
        "preference": 0.7,
        "last_updated": "2024-01-01T00:00:00Z"
      }
    ],
    "contextual_preferences": [],
    "evolution_history": []
  },
  "reading_levels": {
    "english": {
      "current_level": "advanced",
      "confidence": 0.85
    },
    "japanese": {
      "current_level": "intermediate",
      "confidence": 0.6
    }
  }
}
```

**Response:** `201 Created`

```json
{
  "user_id": "user123",
  "preferences": {
    /* preference object */
  },
  "reading_levels": {
    /* reading levels object */
  },
  "last_updated": "2024-01-01T00:00:00Z",
  "created_at": "2024-01-01T00:00:00Z"
}
```

### Get User Profile

```http
GET /api/v1/users/{user_id}
```

**Response:** `200 OK` - Returns user profile data

### Update User Profile

```http
PUT /api/v1/users/{user_id}
```

**Request Body:** Same as create user profile

### Delete User Profile

```http
DELETE /api/v1/users/{user_id}
```

**Response:** `200 OK`

```json
{
  "message": "User profile deleted successfully"
}
```

---

## Content Management APIs

### Create Content Item

```http
POST /api/v1/content/
```

**Request Body:**

```json
{
  "title": "Sample Article",
  "content": "Article content here...",
  "language": "english",
  "metadata": {
    "author": "John Doe",
    "source": "Example Blog",
    "publish_date": "2024-01-01T00:00:00Z",
    "content_type": "article",
    "estimated_reading_time": 5,
    "tags": ["technology", "AI"]
  }
}
```

**Response:** `201 Created` - Returns processed content item with analysis

### Analyze Text Sample

```http
POST /api/v1/content/analyze
```

**Request Body:**

```json
{
  "text": "Sample text to analyze...",
  "language": "english"
}
```

**Response:** `200 OK`

```json
{
  "topics": [
    {
      "topic": "technology",
      "confidence": 0.85,
      "relevance": 0.9
    }
  ],
  "reading_level": {
    "level": "intermediate",
    "score": 0.7,
    "metrics": {
      "flesch_kincaid": 8.5,
      "gunning_fog": 9.2
    }
  },
  "complexity": {
    "score": 0.6,
    "factors": ["vocabulary", "sentence_structure"]
  },
  "key_phrases": ["artificial intelligence", "machine learning"]
}
```

### Get Content Analysis

```http
GET /api/v1/content/{content_id}/analysis
```

**Response:** `200 OK` - Returns content analysis data

### Search Similar Content

```http
GET /api/v1/content/search/similar?query={query}&language={language}&limit={limit}
```

**Parameters:**

- `query` (required): Search query text
- `language` (required): Content language
- `limit` (optional): Number of results (default: 10)

**Response:** `200 OK`

```json
{
  "results": [
    {
      "content_id": "content123",
      "title": "Similar Article",
      "similarity_score": 0.85,
      "metadata": {
        /* content metadata */
      }
    }
  ]
}
```

### Filter Content by Reading Level

```http
GET /api/v1/content/filter/reading-level?language={language}&reading_level={level}&limit={limit}
```

### Get Content Topics

```http
GET /api/v1/content/topics?language={language}
```

**Response:** `200 OK`

```json
{
  "topics": ["science fiction", "technology", "history", "biography"]
}
```

### Get Content Item

```http
GET /api/v1/content/{content_id}
```

### List Content Items

```http
GET /api/v1/content/?language={language}&limit={limit}&offset={offset}
```

---

## Content Storage APIs

### Ingest Content

```http
POST /api/content-storage/ingest
```

**Request Body:**

```json
{
  "title": "Article Title",
  "content": "Full article content...",
  "language": "english",
  "author": "Author Name",
  "source": "Source Website",
  "content_type": "article",
  "tags": ["tag1", "tag2"],
  "user_id": "user123"
}
```

**Response:** `201 Created` - Returns processed content with vector embeddings

### Save Content for User

```http
POST /api/content-storage/save
```

**Request Body:**

```json
{
  "content_id": "content123",
  "user_id": "user123",
  "user_rating": 4,
  "user_notes": "Great article!",
  "tags": ["favorite", "reference"],
  "save_reason": "for_later_reading"
}
```

### Search Content by Similarity

```http
POST /api/content-storage/search
```

**Request Body:**

```json
{
  "query_text": "artificial intelligence applications",
  "language": "english",
  "reading_level": "intermediate",
  "user_id": "user123",
  "limit": 10,
  "include_user_content": true
}
```

**Response:** `200 OK`

```json
{
  "query_text": "artificial intelligence applications",
  "results": [
    {
      "content": {
        /* content item */
      },
      "similarity_score": 0.92,
      "match_metadata": {
        "matched_topics": ["AI", "technology"],
        "reading_level_match": 0.85
      }
    }
  ],
  "total_results": 15,
  "search_method": "vector_similarity"
}
```

### Get User Saved Content

```http
GET /api/content-storage/user/{user_id}/saved?limit={limit}&offset={offset}
```

### Get Content Recommendations

```http
POST /api/content-storage/recommendations
```

**Request Body:**

```json
{
  "user_id": "user123",
  "topics": ["science fiction", "technology"],
  "language": "english",
  "reading_level": "advanced",
  "limit": 10,
  "exclude_saved": true
}
```

### Get Content by ID

```http
GET /api/content-storage/content/{content_id}
```

### Update Content Metadata

```http
PUT /api/content-storage/content/{content_id}/metadata
```

### Get Available Topics

```http
GET /api/content-storage/topics/{language}
```

### Get Content Storage Statistics

```http
GET /api/content-storage/stats
```

**Response:** `200 OK`

```json
{
  "total_content": 1250,
  "by_language": {
    "english": 800,
    "japanese": 450
  },
  "by_reading_level": {
    "beginner": 300,
    "intermediate": 600,
    "advanced": 350
  },
  "vector_index_available": true
}
```

---

## Conversation APIs

### Test Message Functionality

```http
POST /api/v1/conversations/test-message
```

**Request Body:**

```json
{
  "content": "Hello, can you recommend a book?",
  "user_id": "test-user"
}
```

**Response:** `200 OK`

```json
{
  "status": "success",
  "user_message": "Hello, can you recommend a book?",
  "bot_response": "Hello! I'm Noah, your reading agent. I'm here to help you discover amazing books!",
  "session_id": "test-session-test-user",
  "timestamp": "2024-01-01T00:00:00Z",
  "test_mode": true
}
```

### Conversation Health Check

```http
GET /api/v1/conversations/health
```

### Create Conversation Session

```http
POST /api/v1/conversations/sessions
```

**Request Body:**

```json
{
  "session_id": "session123",
  "user_id": "user123",
  "context": {
    "current_topic": "science fiction",
    "recent_recommendations": [],
    "user_mood": "curious",
    "discovery_mode_active": false,
    "preferred_language": "english"
  },
  "is_persistent": true
}
```

### Get Conversation Session

```http
GET /api/v1/conversations/sessions/{session_id}
```

### Create Message

```http
POST /api/v1/conversations/messages
```

**Request Body:**

```json
{
  "message_id": "msg123",
  "session_id": "session123",
  "sender": "user",
  "content": "Can you recommend a science fiction book?",
  "intent": {
    "type": "recommendation_request",
    "genre": "science fiction"
  }
}
```

### Get Session Messages

```http
GET /api/v1/conversations/sessions/{session_id}/messages?limit={limit}&offset={offset}
```

### Get User Sessions

```http
GET /api/v1/conversations/users/{user_id}/sessions
```

---

## Chat Streaming APIs

### Stream Chat Response

```http
POST /api/v1/chat/stream
```

**Request Body:**

```json
{
  "message": "Can you recommend a book about artificial intelligence?",
  "session_id": "session123",
  "user_id": "user123",
  "metadata": {
    "context": "casual_browsing",
    "device": "mobile"
  }
}
```

**Response:** `200 OK` - Server-Sent Events stream

```
data: {"type": "start", "timestamp": "2024-01-01T00:00:00Z"}

data: {"type": "content", "content": "I'd be happy to recommend", "timestamp": "2024-01-01T00:00:00Z"}

data: {"type": "content", "content": " some great AI books!", "timestamp": "2024-01-01T00:00:00Z"}

data: {"type": "tool_call", "tool": "get_recommendations", "parameters": {"topic": "artificial intelligence"}}

data: {"type": "recommendations", "recommendations": [{"title": "The Alignment Problem", "author": "Brian Christian"}]}

data: {"type": "end", "timestamp": "2024-01-01T00:00:00Z"}
```

### Get Conversation History

```http
POST /api/v1/chat/history
```

**Request Body:**

```json
{
  "session_id": "session123",
  "limit": 50
}
```

### Update Preferences Notification

```http
POST /api/v1/chat/preferences/update?user_id={user_id}
```

**Request Body:**

```json
{
  "type": "topic",
  "key": "science fiction",
  "value": 0.9,
  "timestamp": "2024-01-01T00:00:00Z"
}
```

---

## Recommendation APIs

### Get Contextual Recommendations

```http
POST /api/v1/recommendations/users/{user_id}/contextual
```

**Request Body:**

```json
{
  "context": {
    "time_of_day": "evening",
    "device_type": "tablet",
    "location": "home",
    "available_time": 60,
    "user_mood": "relaxed"
  },
  "limit": 10,
  "language": "english"
}
```

**Response:** `200 OK`

```json
{
  "user_id": "user123",
  "recommendations": [
    {
      "content_id": "content123",
      "title": "The Martian",
      "language": "english",
      "metadata": {
        "author": "Andy Weir",
        "reading_time": 45
      },
      "recommendation_score": 0.92,
      "recommendation_reason": "Perfect for evening reading with your interest in science fiction"
    }
  ],
  "context_applied": {
    /* context object */
  },
  "total_count": 5
}
```

### Get Recommendations (Legacy)

```http
GET /api/v1/recommendations/users/{user_id}?limit={limit}&language={language}&discovery_mode={boolean}
```

### Submit Feedback

```http
POST /api/v1/recommendations/users/{user_id}/feedback
```

**Request Body:**

```json
{
  "content_id": "content123",
  "feedback_type": "like",
  "rating": 4,
  "context": {
    "reading_session": "completed",
    "enjoyment_level": "high"
  }
}
```

### Get Discovery Recommendations

```http
GET /api/v1/recommendations/discovery/{user_id}?limit={limit}&language={language}
```

**Response:** `200 OK`

```json
{
  "user_id": "user123",
  "discovery_recommendations": [
    {
      "content_id": "content456",
      "title": "Unexpected Genre Book",
      "divergence_score": 0.7,
      "bridging_topics": ["technology", "philosophy"],
      "discovery_reason": "Explores technology themes from a philosophical perspective"
    }
  ],
  "total_count": 3
}
```

### Track Discovery Response

```http
POST /api/v1/recommendations/discovery/{user_id}/response
```

**Request Body:**

```json
{
  "content_id": "content456",
  "response": "interested"
}
```

---

## Reading Progress APIs

### Start Reading Session

```http
POST /api/v1/reading-progress/sessions/start
```

**Request Body:**

```json
{
  "user_id": "user123",
  "content_id": "content123",
  "context": {
    "time_of_day": "morning",
    "device_type": "tablet",
    "available_time": 30
  }
}
```

**Response:** `200 OK`

```json
{
  "success": true,
  "data": {
    "session_id": "session123",
    "adaptive_difficulty": "intermediate",
    "estimated_completion_time": 25,
    "initial_assessment": {
      "user_skill_level": 0.75,
      "content_difficulty": 0.7,
      "match_score": 0.85
    }
  }
}
```

### Update Reading Progress

```http
PUT /api/v1/reading-progress/sessions/progress
```

**Request Body:**

```json
{
  "session_id": "session123",
  "progress_data": {
    "completion_rate": 0.3,
    "words_read": 500,
    "time_elapsed": 600,
    "pause_event": {
      "type": "voluntary",
      "duration": 30
    },
    "engagement_data": {
      "scroll_speed": "normal",
      "interaction_frequency": "high"
    }
  }
}
```

### Complete Reading Session

```http
POST /api/v1/reading-progress/sessions/complete
```

**Request Body:**

```json
{
  "session_id": "session123",
  "completion_data": {
    "final_completion_rate": 1.0,
    "total_time_minutes": 25,
    "comprehension_indicators": {
      "engagement_score": 0.9,
      "completion_speed": "optimal"
    }
  }
}
```

**Response:** `200 OK`

```json
{
  "success": true,
  "data": {
    "session_summary": {
      "performance_score": 0.85,
      "skill_development": "positive",
      "difficulty_assessment": "well_matched"
    },
    "adaptive_suggestions": [
      {
        "type": "difficulty_increase",
        "suggestion": "Try slightly more challenging content",
        "priority": "medium"
      }
    ]
  }
}
```

### Get Progress Analytics

```http
GET /api/v1/reading-progress/analytics/{user_id}?time_period_days={days}
```

**Response:** `200 OK`

```json
{
  "success": true,
  "data": {
    "user_id": "user123",
    "analysis_period_days": 30,
    "total_sessions": 15,
    "progress_metrics": {
      "completion_rate": 0.87,
      "average_reading_speed_wpm": 250,
      "total_reading_time_hours": 12.5
    },
    "skill_development_trends": {
      "completion_rate_trend": "improving",
      "reading_speed_trend": "stable",
      "skill_development_summary": "Consistent progress with strong comprehension"
    },
    "recommendations": [
      {
        "type": "content_difficulty",
        "message": "Ready for more advanced content",
        "priority": "high"
      }
    ]
  }
}
```

### Get Session Status

```http
GET /api/v1/reading-progress/sessions/{session_id}/status
```

### Get Recent Sessions

```http
GET /api/v1/reading-progress/users/{user_id}/recent-sessions?limit={limit}
```

### Get Skill Insights

```http
GET /api/v1/reading-progress/users/{user_id}/skill-insights
```

### Get Difficulty Recommendations

```http
GET /api/v1/reading-progress/users/{user_id}/difficulty-recommendations
```

### Get Skill Progression

```http
GET /api/v1/reading-progress/users/{user_id}/skill-progression?content_id={content_id}
```

### Get Learning Path

```http
GET /api/v1/reading-progress/users/{user_id}/learning-path
```

### Track Difficulty Adjustment

```http
POST /api/v1/reading-progress/users/{user_id}/difficulty-adjustment
```

**Request Body:**

```json
{
  "content_id": "content123",
  "original_difficulty": "intermediate",
  "adjusted_difficulty": "advanced",
  "reason": "user_performing_above_expected"
}
```

---

## Preference Management APIs

### Get Preference Transparency

```http
GET /api/v1/preferences/{user_id}/transparency
```

**Response:** `200 OK`

```json
{
  "user_id": "user123",
  "learned_preferences": {
    "topics": [
      {
        "topic": "science fiction",
        "weight": 0.85,
        "confidence": 0.9,
        "source": "reading_behavior",
        "last_updated": "2024-01-01T00:00:00Z"
      }
    ],
    "content_types": [
      {
        "type": "novel",
        "preference": 0.7,
        "source": "explicit_feedback"
      }
    ]
  },
  "explanation": {
    "how_learned": "Based on your reading history and feedback",
    "confidence_factors": ["consistent_engagement", "positive_feedback"],
    "evolution_summary": "Preferences have been stable with slight increase in sci-fi interest"
  }
}
```

### Update User Preferences

```http
PUT /api/v1/preferences/{user_id}/preferences
```

**Request Body:**

```json
{
  "topics": [
    {
      "topic": "science fiction",
      "weight": 0.9,
      "confidence": 1.0,
      "last_updated": "2024-01-01T00:00:00Z",
      "evolution_trend": "manual_override"
    }
  ],
  "content_types": [
    {
      "type": "novel",
      "preference": 0.8,
      "last_updated": "2024-01-01T00:00:00Z"
    }
  ],
  "contextual_preferences": [],
  "evolution_history": []
}
```

### Update Reading Levels

```http
PUT /api/v1/preferences/{user_id}/reading-levels
```

**Request Body:**

```json
{
  "english": {
    "current_level": "advanced",
    "confidence": 0.9
  },
  "japanese": {
    "current_level": "intermediate",
    "confidence": 0.7
  }
}
```

### Override Specific Preference

```http
POST /api/v1/preferences/{user_id}/preferences/override
```

**Request Body:**

```json
{
  "type": "topic",
  "key": "mystery",
  "value": 0.8
}
```

### Get Preference Evolution

```http
GET /api/v1/preferences/{user_id}/evolution
```

**Response:** `200 OK`

```json
{
  "user_id": "user123",
  "evolution_timeline": [
    {
      "timestamp": "2024-01-01T00:00:00Z",
      "change_type": "topic_weight_increase",
      "topic": "science fiction",
      "old_value": 0.7,
      "new_value": 0.85,
      "trigger": "positive_feedback"
    }
  ],
  "trends": {
    "most_stable_preferences": ["science fiction", "technology"],
    "most_volatile_preferences": ["romance"],
    "overall_stability": "high"
  }
}
```

---

## Agent Configuration APIs

### Get Agent Information

```http
GET /api/v1/agents/info
```

**Response:** `200 OK`

```json
{
  "status": "success",
  "agent_configuration": {
    "service_type": "strands_agents",
    "strands_available": true,
    "agent_info": {
      "model": "claude-3-sonnet",
      "tools": ["recommendations", "discovery", "content_analysis"]
    }
  },
  "strands_config": {
    "enabled": true,
    "model": "claude-3-sonnet",
    "temperature": 0.7,
    "max_tokens": 4000,
    "streaming_enabled": true,
    "tools_enabled": {
      "recommendations": true,
      "discovery": true,
      "feedback": true,
      "content_analysis": true
    }
  }
}
```

### Validate Agent Configuration

```http
GET /api/v1/agents/config/validate
```

**Response:** `200 OK`

```json
{
  "status": "success",
  "validation": {
    "valid": true,
    "errors": [],
    "warnings": ["Temperature is set quite high"]
  }
}
```

### Get Agent Capabilities

```http
GET /api/v1/agents/capabilities
```

**Response:** `200 OK`

```json
{
  "status": "success",
  "service_type": "strands_agents",
  "capabilities": {
    "conversation": {
      "natural_language_understanding": true,
      "context_awareness": true,
      "streaming_responses": true,
      "multilingual_support": true,
      "conversation_memory": true
    },
    "recommendations": {
      "personalized_suggestions": true,
      "contextual_filtering": true,
      "reading_level_matching": true,
      "interest_scoring": true
    },
    "discovery": {
      "serendipitous_recommendations": true,
      "genre_exploration": true,
      "preference_divergence": true
    }
  },
  "tools_available": [
    "get_recommendations",
    "analyze_content",
    "track_feedback"
  ]
}
```

### Check Agent Health

```http
GET /api/v1/agents/health
```

**Response:** `200 OK`

```json
{
  "status": "healthy",
  "services": {
    "conversation": {
      "status": "healthy",
      "type": "strands_agents",
      "available": true
    },
    "strands_config": {
      "status": "healthy",
      "valid": true,
      "errors": [],
      "warnings": []
    }
  },
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### Test Agent Conversation

```http
POST /api/v1/agents/test
```

**Response:** `200 OK`

```json
{
  "status": "success",
  "test_type": "strands_agent",
  "test_message": "Hello, can you recommend a book?",
  "response": {
    "content": "I'd be happy to recommend some books! What genres interest you?",
    "tool_calls": 1,
    "processing_time": 1.2
  }
}
```

---

## Monitoring & Health APIs

### Health Check

```http
GET /health
```

**Response:** `200 OK`

```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z",
  "version": "0.1.0",
  "uptime_seconds": 3600.5,
  "services": {
    "database": "healthy",
    "monitoring": "healthy",
    "strands_agents": "healthy"
  },
  "metrics": {
    "health_check_duration_ms": 15.2
  }
}
```

### Get Metrics Summary

```http
GET /api/v1/monitoring/metrics/summary?period_minutes={minutes}
```

**Response:** `200 OK`

```json
{
  "timestamp": "2024-01-01T00:00:00Z",
  "period_minutes": 60,
  "request_count": 1250,
  "error_count": 5,
  "avg_response_time_ms": 125.5,
  "performance_summary": {
    "chat_interaction": {
      "avg_duration_ms": 850.2,
      "success_rate": 0.98,
      "total_operations": 450
    },
    "recommendation_generation": {
      "avg_duration_ms": 320.1,
      "success_rate": 0.99,
      "total_operations": 200
    }
  }
}
```

### Flush Metrics

```http
POST /api/v1/monitoring/metrics/flush
```

### Get Recent Logs

```http
GET /api/v1/monitoring/logs/recent?level={level}&limit={limit}
```

### Get Operation Performance

```http
GET /api/v1/monitoring/performance/operations
```

### Test Alert

```http
POST /api/v1/monitoring/test/alert?level={level}&message={message}
```

### Test Metric

```http
POST /api/v1/monitoring/test/metric?name={name}&value={value}&unit={unit}
```

---

## Data Models

### User Profile

```json
{
  "user_id": "string",
  "preferences": {
    "topics": [
      {
        "topic": "string",
        "weight": "float",
        "confidence": "float",
        "last_updated": "datetime",
        "evolution_trend": "string"
      }
    ],
    "content_types": [
      {
        "type": "string",
        "preference": "float",
        "last_updated": "datetime"
      }
    ],
    "contextual_preferences": [
      {
        "factor": "string",
        "value": "string",
        "weight": "float",
        "last_updated": "datetime"
      }
    ],
    "evolution_history": []
  },
  "reading_levels": {
    "english": {
      "current_level": "string",
      "confidence": "float"
    },
    "japanese": {
      "current_level": "string",
      "confidence": "float"
    }
  },
  "last_updated": "datetime",
  "created_at": "datetime"
}
```

### Content Item

```json
{
  "id": "string",
  "title": "string",
  "content": "string",
  "language": "string",
  "metadata": {
    "author": "string",
    "source": "string",
    "publish_date": "datetime",
    "content_type": "string",
    "estimated_reading_time": "integer",
    "tags": ["string"],
    "word_count": "integer",
    "reading_level": "string",
    "complexity_score": "float"
  },
  "analysis": {
    "topics": [
      {
        "topic": "string",
        "confidence": "float",
        "relevance": "float"
      }
    ],
    "reading_level": {
      "level": "string",
      "score": "float",
      "metrics": {}
    },
    "complexity": {
      "score": "float",
      "factors": ["string"]
    },
    "embedding": ["float"],
    "key_phrases": ["string"]
  },
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### Conversation Session

```json
{
  "session_id": "string",
  "user_id": "string",
  "context": {
    "current_topic": "string",
    "recent_recommendations": ["string"],
    "user_mood": "string",
    "discovery_mode_active": "boolean",
    "preferred_language": "string"
  },
  "start_time": "datetime",
  "last_activity": "datetime",
  "is_persistent": "boolean"
}
```

### Reading Behavior

```json
{
  "id": "integer",
  "content_id": "string",
  "user_id": "string",
  "session_id": "string",
  "start_time": "datetime",
  "end_time": "datetime",
  "completion_rate": "float",
  "reading_speed": "float",
  "pause_patterns": [
    {
      "type": "string",
      "duration": "integer",
      "timestamp": "datetime"
    }
  ],
  "interactions": [
    {
      "type": "string",
      "data": {},
      "timestamp": "datetime"
    }
  ],
  "context": {},
  "created_at": "datetime"
}
```

---

## Error Handling

### Standard Error Response

```json
{
  "detail": "Error message",
  "status_code": 400,
  "timestamp": "2024-01-01T00:00:00Z",
  "path": "/api/v1/endpoint",
  "error_type": "ValidationError"
}
```

### HTTP Status Codes

- **200 OK**: Successful request
- **201 Created**: Resource created successfully
- **400 Bad Request**: Invalid request data
- **401 Unauthorized**: Authentication required
- **403 Forbidden**: Access denied
- **404 Not Found**: Resource not found
- **422 Unprocessable Entity**: Validation error
- **500 Internal Server Error**: Server error
- **503 Service Unavailable**: Service temporarily unavailable

### Common Error Types

- `ValidationError`: Request data validation failed
- `NotFoundError`: Requested resource not found
- `AuthenticationError`: Authentication failed
- `AuthorizationError`: Access denied
- `ServiceUnavailableError`: External service unavailable
- `DatabaseError`: Database operation failed
- `ProcessingError`: Content processing failed

---

## Rate Limiting

The API implements rate limiting to ensure fair usage:

- **General endpoints**: 100 requests per minute per user
- **Chat streaming**: 20 requests per minute per user
- **Content ingestion**: 10 requests per minute per user
- **Analytics endpoints**: 30 requests per minute per user

Rate limit headers are included in responses:

- `X-RateLimit-Limit`: Request limit per window
- `X-RateLimit-Remaining`: Remaining requests in current window
- `X-RateLimit-Reset`: Time when the rate limit resets

---

## Pagination

List endpoints support pagination with the following parameters:

- `limit`: Number of items per page (default: 10, max: 100)
- `offset`: Number of items to skip (default: 0)

Paginated responses include:

```json
{
  "items": [],
  "total": 150,
  "limit": 10,
  "offset": 0,
  "has_next": true,
  "has_previous": false
}
```

---

## WebSocket Alternative

The API uses HTTP streaming instead of WebSockets for real-time communication. The `/api/v1/chat/stream` endpoint provides Server-Sent Events for streaming chat responses, which offers better compatibility with load balancers and proxies.

---

## Development and Testing

### Local Development

- Base URL: `http://localhost:8000`
- Debug endpoints available at `/api/debug/*`
- Interactive API documentation at `/docs`

### Production

- Debug endpoints disabled
- Comprehensive monitoring and logging
- Rate limiting enforced
- CORS configured for specific origins

This documentation covers all available backend APIs for the Noah Reading Agent. For specific implementation details or additional endpoints, refer to the source code in the `python-backend/src/api/endpoints/` directory.
