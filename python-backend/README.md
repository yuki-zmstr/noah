# Noah Reading Agent - Python Backend

This is the Python FastAPI backend for Noah Reading Agent, integrated with AWS Agent Core for intelligent conversational capabilities. This project uses [uv](https://docs.astral.sh/uv/) for fast and reliable Python package management.

## Features

- **FastAPI**: Modern, fast web framework for building APIs
- **SQLAlchemy**: Powerful ORM for database management
- **AWS Agent Core**: Integration for NLU and conversational AI
- **PostgreSQL**: Primary database for user profiles and content
- **Vector Database**: Support for content embeddings and similarity search
- **Multilingual Support**: English and Japanese content processing
- **uv**: Fast Python package manager for dependency management

## Quick Start

### Prerequisites

- Python 3.9 or higher
- [uv](https://docs.astral.sh/uv/getting-started/installation/) package manager
- PostgreSQL database
- AWS account with Agent Core access

### Setup

1. **Run the setup script:**

   ```bash
   python setup.py
   ```

2. **Or manually with uv:**

   ```bash
   # Install uv if not already installed
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # Create virtual environment and install dependencies
   uv venv
   uv pip install -e .
   uv pip install -e .[dev,test]
   ```

3. **Configure environment:**

   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Start the development server:**

   ```bash
   # Activate virtual environment
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate

   # Run with uv
   uv run python -m uvicorn src.main:app --reload

   # Or run directly
   python -m uvicorn src.main:app --reload
   ```

The API will be available at `http://localhost:8000`

### Manual Setup (Alternative)

If you prefer manual setup:

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -e .

# Copy environment file
cp .env.example .env

# Start server
python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

## Configuration

Update the `.env` file with your settings:

```env
# Database
DATABASE_URL=postgresql://noah_user:noah_password@localhost:5432/noah_db

# AWS Agent Core
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AGENT_CORE_ENDPOINT=https://agent-core.us-east-1.amazonaws.com
AGENT_CORE_API_KEY=your_agent_core_api_key

# Vector Database
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_ENVIRONMENT=us-east-1-aws
```

## API Documentation

Once running, visit:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Project Structure

```
python-backend/
├── src/
│   ├── api/
│   │   ├── endpoints/          # API route handlers
│   │   └── routes.py          # Router configuration
│   ├── models/                # SQLAlchemy models
│   ├── schemas/               # Pydantic schemas
│   ├── services/              # Business logic services
│   ├── config.py             # Configuration settings
│   ├── database.py           # Database setup
│   └── main.py               # FastAPI application
├── tests/                    # Test files
├── requirements.txt          # Python dependencies
├── pyproject.toml           # Project configuration
└── setup.py                 # Setup script
```

## Development

### Running Tests

```bash
python -m pytest
```

### Code Formatting

```bash
black src/
isort src/
```

### Type Checking

```bash
mypy src/
```

## AWS Agent Core Integration

The backend integrates with AWS Agent Core for:

- **Intent Analysis**: Understanding user requests
- **Entity Extraction**: Identifying books, authors, genres
- **Response Generation**: Creating natural conversational responses
- **Context Management**: Maintaining conversation state

See `src/services/agent_core.py` for implementation details.

## Database Models

### Core Models

- **UserProfile**: User preferences and reading levels
- **ContentItem**: Books and articles with metadata
- **ConversationSession**: Chat sessions and context
- **ConversationMessage**: Individual messages
- **ReadingBehavior**: User reading patterns
- **PurchaseLink**: Book purchase options

### Relationships

The models are designed with proper relationships to support:

- User preference learning
- Content recommendations
- Conversation history
- Reading behavior tracking

## API Endpoints

### Users

- `POST /api/v1/users/` - Create user profile
- `GET /api/v1/users/{user_id}` - Get user profile
- `PUT /api/v1/users/{user_id}` - Update user profile

### Content

- `POST /api/v1/content/` - Add content item
- `GET /api/v1/content/{content_id}` - Get content
- `GET /api/v1/content/` - List content items

### Conversations

- `POST /api/v1/conversations/sessions` - Create session
- `POST /api/v1/conversations/messages` - Send message
- `GET /api/v1/conversations/sessions/{session_id}/messages` - Get messages

### Recommendations

- `GET /api/v1/recommendations/users/{user_id}` - Get recommendations
- `GET /api/v1/recommendations/discovery/{user_id}` - Discovery mode
- `POST /api/v1/recommendations/users/{user_id}/feedback` - Submit feedback

## Deployment

The backend is designed to deploy on AWS using:

- **ECS Fargate**: Container orchestration
- **RDS PostgreSQL**: Managed database
- **API Gateway**: Request routing
- **CloudWatch**: Monitoring and logging

See the infrastructure directory for deployment configuration.
