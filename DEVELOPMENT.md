# Noah Reading Agent - Development Guide

## Project Structure

```
noah-reading-agent/
├── frontend/              # Vue.js frontend application
│   ├── src/
│   │   ├── components/    # Reusable Vue components
│   │   ├── views/         # Page components
│   │   ├── router/        # Vue Router configuration
│   │   ├── stores/        # Pinia state management
│   │   └── utils/         # Utility functions
│   ├── public/            # Static assets
│   └── dist/              # Build output
├── python-backend/        # Python FastAPI backend
│   ├── src/
│   │   ├── api/           # FastAPI route handlers
│   │   ├── models/        # SQLAlchemy models
│   │   ├── schemas/       # Pydantic schemas
│   │   ├── services/      # Business logic services
│   │   └── config.py      # Configuration
│   ├── tests/             # Test files
│   └── requirements.txt   # Python dependencies
├── infrastructure/        # AWS CDK infrastructure code
│   ├── lib/               # CDK stack definitions
│   ├── bin/               # CDK app entry point
│   └── cdk.out/           # CDK synthesis output
├── database/              # Database schemas and migrations
│   └── init/              # Initial database setup
├── scripts/               # Development and deployment scripts
└── docs/                  # Additional documentation
```

## Technology Stack

### Frontend

- **Vue.js 3** with Composition API
- **TypeScript** for type safety
- **Tailwind CSS** for styling
- **Vite** for build tooling
- **Pinia** for state management
- **Vue Router** for navigation
- **Vitest** for testing

### Backend

- **Python 3.9+** with FastAPI
- **SQLAlchemy** for ORM
- **Pydantic** for data validation
- **AWS Agent Core** for agent orchestration
- **PostgreSQL** for user data storage
- **Redis** for caching and sessions
- **OpenSearch** for vector similarity search
- **Uvicorn** for ASGI server
- **Pytest** for testing

### Infrastructure

- **AWS CDK** for infrastructure as code
- **AWS ECS Fargate** for container orchestration
- **AWS RDS PostgreSQL** for production database
- **AWS OpenSearch** for production search
- **AWS S3** for static assets and content storage
- **AWS CloudFront** for CDN
- **AWS Application Load Balancer** for load balancing

## Development Setup

### Prerequisites

1. **Node.js 18+** - [Download](https://nodejs.org/)
2. **Docker & Docker Compose** - [Download](https://www.docker.com/)
3. **AWS CLI** (for deployment) - [Install Guide](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
4. **Git** - [Download](https://git-scm.com/)

### Quick Start

1. **Clone the repository:**

   ```bash
   git clone <repository-url>
   cd noah-reading-agent
   ```

2. **Run the setup script:**

   ```bash
   ./scripts/setup-dev.sh
   ```

3. **Start development servers:**

   ```bash
   npm run dev
   ```

4. **Access the application:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - OpenSearch Dashboards: http://localhost:5601

### Manual Setup

If you prefer to set up manually:

1. **Install dependencies:**

   ```bash
   npm install
   cd frontend && npm install && cd ..
   cd python-backend && pip install -r requirements.txt && cd ..
   cd infrastructure && npm install && cd ..
   ```

2. **Set up environment variables:**

   ```bash
   cp .env.example .env
   cp frontend/.env.example frontend/.env
   # Edit .env files with your configuration
   ```

3. **Start databases:**

   ```bash
   docker compose up -d
   ```

4. **Start development servers:**

   ```bash
   # Terminal 1: Frontend
   cd frontend && npm run dev

   # Terminal 2: Backend
   cd python-backend && python -m uvicorn src.main:app --reload
   ```

## Environment Configuration

### Backend Environment Variables

Key environment variables for the backend (see `.env.example`):

- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `OPENSEARCH_ENDPOINT` - OpenSearch endpoint
- `BEDROCK_AGENT_ID` - AWS Bedrock Agent ID
- `AMAZON_PRODUCT_API_KEY` - Amazon Product API key
- `JWT_SECRET` - JWT signing secret

### Frontend Environment Variables

Key environment variables for the frontend (see `frontend/.env.example`):

- `VITE_API_BASE_URL` - Backend API base URL
- `VITE_ENABLE_DISCOVERY_MODE` - Enable discovery mode feature
- `VITE_ENABLE_MULTILINGUAL` - Enable multilingual support

## Development Workflow

### Running Tests

```bash
# Run all tests
npm test

# Run frontend tests
npm run test:frontend

# Run backend tests
cd python-backend && python -m pytest

# Run tests in watch mode
cd frontend && npm run test:watch
cd python-backend && python -m pytest --watch
```

### Code Quality

```bash
# Lint code
cd frontend && npm run lint
cd python-backend && black src/ && isort src/

# Type checking
cd frontend && npm run type-check
cd python-backend && mypy src/
```

### Database Management

```bash
# Start databases
docker compose up -d

# Stop databases
docker compose down

# Reset databases (WARNING: This will delete all data)
docker compose down -v
docker compose up -d
```

### Building for Production

```bash
# Build all components
npm run build

# Build individual components
npm run build:frontend
cd python-backend && python -m build
```

## Deployment

### AWS Deployment

1. **Configure AWS credentials:**

   ```bash
   aws configure
   ```

2. **Deploy infrastructure:**

   ```bash
   cd infrastructure
   npm run deploy
   ```

3. **Build and deploy application:**
   ```bash
   npm run build
   # Deploy built artifacts to AWS (implementation specific)
   ```

### Environment-Specific Deployments

- **Development**: Local Docker containers
- **Staging**: AWS with reduced resources
- **Production**: Full AWS infrastructure with high availability

## Architecture Overview

### Data Flow

1. **User Interaction**: User sends message through Vue.js frontend
2. **API Communication**: Message sent via HTTP API to Python FastAPI backend
3. **Agent Processing**: AWS Agent Core processes the message with conversation context
4. **Content Analysis**: Content processor analyzes and scores potential recommendations
5. **Recommendation Generation**: Recommendation engine generates personalized suggestions
6. **Response Delivery**: Noah responds with recommendations and explanations
7. **Feedback Loop**: User feedback is processed to improve future recommendations

### Key Components

- **Conversation Manager**: Handles natural language understanding and response generation
- **User Profile Engine**: Maintains and updates user preferences and reading levels
- **Content Processor**: Analyzes content for complexity, topics, and cultural context
- **Recommendation Generator**: Creates personalized content suggestions
- **Discovery Mode Engine**: Provides serendipitous recommendations outside user preferences
- **Purchase Link Generator**: Creates purchase links for recommended books

## API Documentation

### REST Endpoints

- `GET /api/v1/users/{user_id}` - Get user profile
- `PUT /api/v1/users/{user_id}` - Update user preferences
- `GET /api/v1/content/recommendations/{user_id}` - Get content recommendations
- `POST /api/v1/content/analyze` - Analyze content
- `GET /api/v1/conversations/sessions/{session_id}/messages` - Get conversation history
- `POST /api/v1/conversations/messages` - Send message to agent

## Troubleshooting

### Common Issues

1. **Database connection errors**: Ensure Docker containers are running
2. **Port conflicts**: Check if ports 3000, 8000, 5432, 6379, 9200 are available
3. **Environment variables**: Verify all required environment variables are set
4. **AWS permissions**: Ensure AWS credentials have necessary permissions for Bedrock and other services

### Debugging

- Check logs in `python-backend/logs/` directory or console output
- Use browser developer tools for frontend debugging
- Monitor Docker container logs: `docker compose logs -f`
- Check database connectivity: `docker compose exec postgres psql -U noah_user -d noah_dev`

## Contributing

1. Create a feature branch from `main`
2. Make your changes with appropriate tests
3. Ensure all tests pass and code is linted
4. Submit a pull request with a clear description

## Additional Resources

- [Vue.js Documentation](https://vuejs.org/)
- [AWS CDK Documentation](https://docs.aws.amazon.com/cdk/)
- [AWS Bedrock Agent Documentation](https://docs.aws.amazon.com/bedrock/)
- [OpenSearch Documentation](https://opensearch.org/docs/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
