# Implementation Plan: Noah Reading Agent

## Overview

This implementation plan creates Noah, a conversational reading agent using Vue.js for the frontend chatbot interface, Python FastAPI for the backend API with SQLAlchemy for database management, and AWS Agent Core for agent orchestration and NLU capabilities. The system will provide personalized book recommendations, lightweight content analysis, multilingual support (English/Japanese), purchase link generation, and discovery mode functionality.

**ARCHITECTURE CHANGES:** Content adaptation features have been removed to create a lighter, more deployable system. The focus is now on content curation and recommendation rather than content modification. OpenAI's embedding API replaces heavy local ML models for better performance and smaller Docker images.

**PRIORITY: Deploy first to test message functionality in production environment**

## Tasks

## Phase 1: Deployment Infrastructure (PRIORITY)

- [x] 1. Set up AWS deployment infrastructure
  - [x] 1.1 Configure Amazon Cognito for user authentication
    - Create Cognito User Pool with email + password authentication
    - Configure JWT token settings and security policies
    - Set up user registration and login flows
    - Add password policies and MFA options
    - _Requirements: User authentication and security_

  - [x] 1.2 Deploy frontend with AWS Amplify Hosting
    - Configure Amplify Hosting for Vue.js application
    - Set up automatic builds from Git repository
    - Configure custom domain and SSL certificates
    - Integrate with CloudFront for CDN distribution
    - Set up environment variables for different stages (dev/prod)
    - _Requirements: Frontend hosting and distribution_

  - [x] 1.3 Deploy backend API infrastructure
    - Set up ECS Fargate or Lambda for FastAPI backend
    - Configure Application Load Balancer for API endpoints
    - Set up RDS PostgreSQL for user data and conversations
    - Configure VPC, subnets, and security groups
    - Set up CloudWatch logging and monitoring
    - _Requirements: Backend API hosting and database_

  - [x] 1.4 Configure CloudFront distribution
    - Set up CloudFront for global content delivery
    - Configure caching policies for static assets and API responses
    - Set up custom error pages and redirects
    - Configure security headers and CORS policies
    - _Requirements: Performance and global distribution_

  - [x] 1.5 Test basic message functionality in production
    - Deploy minimal chat interface with hardcoded responses
    - Test WebSocket connections in production environment
    - Verify Cognito authentication flow works end-to-end
    - Test message storage and retrieval from RDS
    - Validate CORS and security configurations
    - _Requirements: Basic chat functionality validation_

## Phase 2: Core System Integration

- [x] 2. Set up project structure and development environment
  - Create Vue.js frontend project with TypeScript and Tailwind CSS
  - Set up Python FastAPI backend with SQLAlchemy and PostgreSQL
  - Configure AWS Agent Core integration for agent orchestration
  - Configure development environment with virtual environments and dependencies
  - Set up development databases (PostgreSQL for profiles, Vector DB for content)
  - _Requirements: All system requirements_

- [x] 3. Implement core data models and database schema
  - [x] 3.1 Create database schemas for user profiles, content, and conversations
    - Design PostgreSQL tables for user profiles, reading behavior, and preferences
    - Set up vector database schema for content embeddings and similarity search
    - Create conversation history and session management tables
    - _Requirements: 1.1, 1.3, 6.1, 10.5_

  - [ ]\* 3.2 Write property test for data model consistency
    - **Property 1: Comprehensive Reading Behavior Tracking**
    - **Validates: Requirements 1.1, 5.1**

  - [x] 3.3 Implement SQLAlchemy models and FastAPI schemas with AWS Agent Core integration
    - Create SQLAlchemy models for UserProfile, ContentItem, ConversationMessage, PurchaseLink
    - Add Pydantic schemas for API request/response validation
    - Configure database connections and session management with FastAPI
    - Integrate AWS Agent Core for agent orchestration and state management
    - _Requirements: 2.1, 9.1, 10.1, 11.1_

- [x] 4. Build conversational chatbot interface
  - [x] 4.1 Create Vue.js chat component with message history
    - Build responsive chat interface with message bubbles and typing indicators
    - Implement real-time messaging with WebSocket connection
    - Add support for rich content display (book recommendations, purchase links)
    - _Requirements: 10.1, 10.2, 10.4_

  - [x] 4.2 Implement natural language understanding with AWS Agent Core and FastAPI
    - Integrate AWS Agent Core for intent classification and NLU capabilities
    - Build entity extraction for book titles, authors, genres, and preferences using Agent Core
    - Add conversation context management and session state tracking with FastAPI
    - Implement persistent conversation history with user isolation using SQLAlchemy
    - _Requirements: 10.3, 10.5, 10.6, 13.1, 13.2, 13.4, 13.5_

  - [ ]\* 4.3 Write property test for conversational interface
    - **Property 17: Conversational Interface Consistency**
    - **Validates: Requirements 10.1, 10.2, 10.3, 10.4, 10.5, 10.6**

## Phase 3: Enhanced AI Capabilities

- [ ] 5. Replace hardcoded responses with dynamic AI generation
  - [ ] 5.1 Implement proper AI response generation
    - Replace fallback responses with OpenAI/Anthropic API integration
    - Create dynamic response templates based on user context and intent
    - Implement conversation memory and context awareness
    - Add personality and tone consistency for Noah character
    - _Requirements: 10.3, 10.5, 10.6_

  - [ ] 5.2 Enhance intent recognition and entity extraction
    - Improve intent classification beyond basic keyword matching
    - Add sophisticated entity extraction for books, authors, genres
    - Implement context-aware conversation flow management
    - Add support for complex multi-turn conversations
    - _Requirements: 10.3, 13.1, 13.2_

- [x] 6. Implement content processing and analysis system (simplified)
  - [x] 6.1 Build lightweight multilingual content processor
    - Create English content analyzer using NLTK for basic readability metrics
    - Implement Japanese content analyzer with simple heuristics for complexity assessment
    - Add topic extraction using frequency analysis and regex patterns
    - Generate content embeddings using OpenAI's text-embedding-3-small API
    - _Requirements: 2.1, 2.3, 4.1, 4.2, 4.3, 9.1, 9.2, 9.3_

  - [x] 6.2 ~~Create content adaptation engine~~ (REMOVED - Feature simplified for lighter deployment)
    - ~~Build vocabulary simplification using word frequency databases~~
    - ~~Implement sentence structure simplification while preserving meaning~~
    - ~~Add cultural context preservation for Japanese content adaptation~~
    - _Requirements: Content adaptation removed to reduce image size and complexity_

  - [ ]\* 6.3 Write property test for content analysis
    - **Property 4: Lightweight Content Analysis**
    - **Validates: Requirements 2.1, 2.2, 2.3, 4.1, 4.2, 9.2, 9.3**

  - [ ]\* ~~6.4 Write property test for content adaptation~~ (REMOVED)

## Phase 4: User Experience and Recommendations

- [x] 7. Build user profile and preference learning system
  - [x] 7.1 Implement user profile engine
    - Create preference modeling using collaborative filtering and content-based approaches
    - Build reading level assessment for English and Japanese separately
    - Implement preference evolution tracking with temporal analysis
    - _Requirements: 1.1, 1.2, 1.3, 5.1, 5.5, 9.4_

  - [x] 7.2 Create feedback processing system
    - Build explicit feedback integration (ratings, likes, contextual comments)
    - Implement implicit feedback analysis (reading time, completion rates, interactions)
    - Add preference transparency and explanation generation
    - _Requirements: 1.2, 7.1, 7.2, 7.3, 7.5, 8.1, 8.2_

  - [ ]\* 7.3 Write property test for feedback integration
    - **Property 2: Feedback Integration Consistency**
    - **Validates: Requirements 1.2, 7.1, 7.2, 7.5**

  - [ ]\* 7.4 Write property test for preference evolution
    - **Property 3: Preference Evolution Detection**
    - **Validates: Requirements 1.3, 7.4**

- [x] 8. Checkpoint - Core systems integration test
  - Ensure all core systems (chat, content processing, user profiles) work together
  - Test multilingual content processing with sample English and Japanese content
  - Verify conversation flow with basic recommendation requests
  - Ask the user if questions arise

- [x] 9. Implement recommendation and discovery systems
  - [x] 9.1 Build contextual recommendation engine
    - Create recommendation algorithm considering interest scores, reading level, and context
    - Implement time-based and mood-based filtering
    - Add diversity mechanisms to prevent filter bubbles
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

  - [x] 9.2 Create discovery mode ("I'm feeling lucky") engine
    - Build genre and topic exploration algorithms
    - Implement serendipitous recommendation using collaborative filtering
    - Add discovery tracking and user response analysis
    - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 12.6_

  - [ ]\* 9.3 Write property test for contextual recommendations
    - **Property 5: Contextual Recommendation Generation**
    - **Validates: Requirements 3.1, 3.2, 3.3**

  - [ ]\* 9.4 Write property test for discovery mode
    - **Property 19: Discovery Mode Divergence**
    - **Validates: Requirements 12.1, 12.2, 12.3, 12.4, 12.5, 12.6**

## Phase 5: Production Features

- [x] 10. Complete backend-frontend integration and real-time communication
  - [x] 10.1 Connect chat interface to backend API endpoints
    - Replace mock responses with real API calls to conversation service
    - Implement proper WebSocket connection between frontend and backend
    - Test real-time message delivery and recommendation display
    - Add error handling for API failures and connection issues
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6_

  - [x] 10.2 Integrate recommendation delivery through chat interface
    - Connect recommendation engine to chat message flow
    - Display contextual recommendations with explanations in chat
    - Implement discovery mode activation through chat commands
    - Add feedback collection through chat interface interactions
    - _Requirements: 3.1, 3.2, 3.3, 12.1, 12.2, 7.1, 7.2_

- [ ] 11. Complete purchase link generation system
  - [ ] 11.1 Finish Amazon API integration
    - Complete Amazon Product Advertising API setup and testing
    - Implement robust ISBN/ASIN resolution for accurate product matching
    - Add affiliate link generation with proper tracking and error handling
    - Test with real book data and handle API rate limits
    - _Requirements: 11.1, 11.3, 11.4_

  - [ ] 11.2 Implement web search link generator
    - Build Google/Bing search query generation for books not found on Amazon
    - Add alternative retailer suggestions (Barnes & Noble, local bookstores)
    - Implement library catalog search integration for borrowing options
    - Create fallback mechanisms when purchase links are unavailable
    - _Requirements: 11.2, 11.5_

  - [ ]\* 11.3 Write property test for purchase link generation
    - **Property 18: Purchase Link Generation**
    - **Validates: Requirements 11.1, 11.2, 11.3, 11.4, 11.5**

- [x] 12. Content storage and retrieval system (completed)
  - [x] 12.1 Build content storage with metadata
    - Create content ingestion pipeline with automatic metadata extraction
    - Implement vector similarity search for content recommendations
    - Add saved content management with user-specific metadata
    - _Requirements: 6.1, 6.2, 6.4_

  - [x] 12.2 Create reading progress tracking
    - Build reading session tracking with behavioral metrics
    - Implement adaptive difficulty adjustment based on user performance
    - Add progressive complexity management for skill development
    - _Requirements: 5.1, 5.2, 5.3, 5.4_

  - [ ]\* 12.3 Write property test for content storage
    - **Property 10: Content Storage and Retrieval Consistency**
    - **Validates: Requirements 6.1, 6.2, 6.4**

- [x] 13. Build preference transparency and control features
  - [x] 13.1 Complete preference dashboard in Vue.js
    - Build user interface for viewing learned preferences and explanations
    - Implement preference editing and override functionality
    - Add recommendation explanation display with reasoning
    - Connect to backend preference transparency service
    - _Requirements: 8.1, 8.2, 8.3, 8.5_

  - [x] 13.2 Implement immediate preference updates
    - Create real-time preference modification system
    - Build recommendation refresh mechanism for preference changes
    - Add preference change impact visualization
    - Test preference updates through both UI and chat interface
    - _Requirements: 8.4_

  - [ ]\* 13.3 Write property test for preference transparency
    - **Property 12: Preference Transparency and Control**
    - **Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.5**

## Phase 6: Advanced Features and Optimization

- [ ] 14. Implement performance optimization and monitoring
  - [ ] 14.1 Add caching and performance optimization
    - Implement Redis caching for frequent recommendations and content analysis
    - Optimize database queries and add appropriate indexes
    - Add content delivery network for static assets
    - Monitor and optimize vector search performance
    - _Requirements: All system requirements_

  - [ ] 14.2 Set up comprehensive monitoring and logging
    - Configure CloudWatch for application and infrastructure monitoring
    - Set up custom metrics for chat interactions and user engagement
    - Add error tracking and alerting for production issues
    - Implement performance monitoring and optimization alerts
    - _Requirements: All system requirements_

  - [ ] 14.3 Set up CI/CD pipeline
    - Create GitHub Actions for automated testing and deployment
    - Set up staging and production environments
    - Add automated rollback mechanisms
    - Implement blue-green deployment for zero-downtime updates
    - _Requirements: All system requirements_

- [ ]\* 15. Integrate Strands Agents framework for enhanced agentic capabilities
  - [-] 15.1 Install and configure strands-agents packages
    - Install strands-agents and strands-agents-tools packages via pip
    - Configure strands framework integration with existing FastAPI backend
    - Set up agent orchestration using strands for improved conversation management
    - _Requirements: 10.3, 10.5, 13.1, 13.2_

  - [ ] 15.2 Enhance conversational agent with strands capabilities
    - Migrate existing AWS Agent Core functionality to strands framework
    - Implement multi-agent workflows for complex recommendation scenarios
    - Add tool integration for content processing and recommendation generation
    - _Requirements: 10.1, 10.2, 10.6, 3.1, 3.2_

  - [ ] 15.3 Implement Strands streaming functionality for real-time responses
    - Replace current WebSocket text chunking with Strands agent.stream_async() method
    - Implement convert_event() function to handle Bedrock API streaming events
    - Add support for streaming text chunks and tool usage notifications via WebSocket
    - Integrate streaming with existing conversation service and WebSocket manager
    - Test real-time AI response generation with proper tool visibility
    - _Requirements: 10.1, 10.2, 10.4, 10.5_

  - [ ]\* 15.4 Write property test for strands agent integration
    - **Property 20: Strands Agent Workflow Consistency**
    - **Validates: Requirements 10.3, 10.5, 13.1, 13.2**

- [ ] 16. Integration testing and final validation
  - [ ]\* 16.1 Write comprehensive integration tests
    - Test complete user journey from chat interaction to book recommendation
    - Verify multilingual content processing and cultural context preservation
    - Test discovery mode and purchase link generation workflows
    - Validate user data isolation and privacy requirements
    - _Requirements: All system requirements_

  - [ ] 16.2 Final system validation and optimization
    - Ensure all tests pass and system meets performance requirements
    - Verify multilingual support works correctly for English and Japanese
    - Test conversational interface, discovery mode, and purchase link generation
    - Validate preference transparency and user control features
    - Conduct end-to-end testing with real users
    - _Requirements: All system requirements_

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties using Hypothesis library
- Unit tests validate specific examples and edge cases using pytest
- The system uses Vue.js + TypeScript for frontend, Python FastAPI + SQLAlchemy for backend with AWS Agent Core integration, and AWS for hosting
- **ARCHITECTURE SIMPLIFIED:** Content adaptation engine removed to reduce Docker image size from ~4GB to ~1GB
- **DEPENDENCIES OPTIMIZED:** Replaced torch, transformers, sentence-transformers, spaCy with lightweight OpenAI API integration
- **FOCUS SHIFTED:** From content modification to content curation and intelligent recommendation
- Most core functionality is implemented - remaining work focuses on integration, completion of purchase links, preference UI, and deployment
