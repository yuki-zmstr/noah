# Authentication Implementation

This document describes the simple login screen implementation with email and password authentication, ensuring chat history is tied to each user.

## Overview

The authentication system has been implemented with the following components:

### Frontend Components

1. **Auth Store** (`frontend/src/stores/auth.ts`)
   - Manages user authentication state
   - Handles login/logout functionality
   - Persists user session in localStorage
   - Creates consistent user IDs based on email

2. **Login Form** (`frontend/src/components/LoginForm.vue`)
   - Simple email/password login interface with sign-up toggle
   - Sign-up mode adds a confirm password field
   - Clean, modern design with Noah branding (circular "N" logo)
   - Loading states and error handling
   - Demo credentials note for testing

3. **Login View** (`frontend/src/views/LoginView.vue`)
   - Wrapper component for the login form

4. **Router Guards** (`frontend/src/router/index.ts`)
   - Authentication guards for protected routes
   - Automatic redirection to login for unauthenticated users
   - Prevents authenticated users from accessing login page

### Chat History Integration

1. **Updated Chat Store** (`frontend/src/stores/chat.ts`)
   - Ties chat sessions to authenticated users
   - Stores messages per user in localStorage with user-specific keys
   - Loads user-specific message history on session initialization
   - Clears user data on logout

2. **Updated Chat View** (`frontend/src/views/ChatView.vue`)
   - Shows user email in header
   - Logout functionality
   - Personalized welcome message
   - User-specific session management

### Backend Integration

The backend already supports user-specific conversations:

1. **Conversation Service** (`python-backend/src/services/conversation_service.py`)
   - Extracts user ID from session ID
   - Creates user-specific conversation sessions
   - Ensures user profiles exist

2. **Chat Streaming** (`python-backend/src/api/endpoints/chat_streaming.py`)
   - Accepts user_id in chat requests
   - Tracks user-specific interactions

## Features

### Authentication Features

- ✅ Simple email/password login
- ✅ Sign-up mode with confirm password validation
- ✅ Toggle between sign-in and sign-up modes
- ✅ Session persistence with localStorage
- ✅ Automatic authentication on app startup
- ✅ Route guards for protected pages
- ✅ Logout functionality

### Chat History Features

- ✅ User-specific chat sessions
- ✅ Persistent message history per user
- ✅ Automatic session initialization with user ID
- ✅ Clean separation of user data
- ✅ Message history cleared on logout

## Demo Usage

For demonstration purposes, the login accepts any email and password combination. The system creates a consistent user ID based on the email address, ensuring the same user gets the same chat history when logging in with the same email.

### Test Credentials

- **Email**: Any valid email format (e.g., `user@example.com`)
- **Password**: Any password

### User ID Generation

User IDs are generated consistently using: `user_${btoa(email).replace(/[^a-zA-Z0-9]/g, '').substring(0, 16)}`

This ensures:

- Same email always gets same user ID
- User ID is URL-safe and database-friendly
- Chat history persists across sessions

## Production Integration

To integrate with AWS Cognito in production:

1. **Update Auth Store** (`frontend/src/stores/auth.ts`)
   - Replace mock login with AWS Cognito SDK calls
   - Handle JWT tokens properly
   - Implement token refresh logic

2. **Backend Authentication**
   - The existing `auth_service.py` already supports Cognito JWT validation
   - Update endpoints to require authentication headers
   - Extract user ID from JWT tokens

3. **Environment Configuration**
   - Set up Cognito User Pool and Client IDs
   - Configure environment variables for AWS region and pool settings

## File Structure

```
frontend/src/
├── stores/
│   ├── auth.ts              # Authentication store
│   └── chat.ts              # Updated chat store with user integration
├── components/
│   └── LoginForm.vue        # Login form component
├── views/
│   ├── LoginView.vue        # Login page
│   └── ChatView.vue         # Updated chat view with auth
├── router/
│   └── index.ts             # Updated router with auth guards
└── App.vue                  # Updated app with auth initialization

python-backend/src/
├── services/
│   ├── auth_service.py      # Existing Cognito auth service
│   └── conversation_service.py  # User-aware conversation handling
└── api/endpoints/
    ├── chat_streaming.py    # User-specific chat streaming
    └── conversations.py     # User conversation management
```

## Security Considerations

1. **Demo Mode**: Current implementation is for demonstration only
2. **Production Security**:
   - Implement proper JWT validation
   - Use HTTPS for all authentication requests
   - Implement proper session management
   - Add rate limiting for login attempts
3. **Data Privacy**: User chat history is stored locally and tied to user accounts

## Next Steps

1. **AWS Cognito Integration**: Replace mock authentication with real Cognito calls
2. **Backend Authentication**: Add authentication middleware to all endpoints
3. **User Management**: Add user registration, password reset, etc.
4. **Enhanced Security**: Implement proper token management and refresh logic
