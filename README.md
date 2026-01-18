# Noah Reading Agent

A personalized reading agent system that learns and adapts to user reading interests, comprehension levels, and preferences to provide tailored content recommendations, summaries, and reading assistance.

## Architecture

- **Frontend**: Vue.js 3 with TypeScript and Tailwind CSS
- **Backend**: Python FastAPI with AWS Agent Core integration
- **Infrastructure**: AWS CDK for cloud deployment
- **Databases**: PostgreSQL for user profiles, Vector DB for content embeddings

## Features

- Conversational chatbot interface
- Multilingual support (English/Japanese)
- Personalized book recommendations
- Content adaptation based on reading level
- Purchase link generation
- Discovery mode for exploring new genres
- Persistent conversation memory

## Development Setup

### Prerequisites

- Node.js 18+
- Docker and Docker Compose
- AWS CLI configured
- Python 3.9+ (for backend)

### Quick Start

1. Install dependencies:

```bash
npm install
```

2. Start development databases:

```bash
docker compose up -d
```

3. Start development servers:

```bash
npm run dev
```

### Database Access

For connecting to the production RDS database using DBeaver or other PostgreSQL clients, see [DATABASE_CONNECTION.md](DATABASE_CONNECTION.md).

### Project Structure

```
noah-reading-agent/
├── frontend/          # Vue.js frontend application
├── python-backend/    # Python FastAPI backend
├── infrastructure/    # AWS CDK infrastructure code
├── docker-compose.yml # Development databases
└── README.md
```

## Environment Variables

For detailed setup instructions, see [ENVIRONMENT_SETUP.md](ENVIRONMENT_SETUP.md).

**Quick start for development:**

1. Copy `.env.example` to `.env` and `frontend/.env.example` to `frontend/.env`
2. Generate JWT secrets: `node -e "console.log(require('crypto').randomBytes(64).toString('hex'))"`
3. Update the JWT_SECRET and SESSION_SECRET in your `.env` file
4. Other variables are pre-configured for Docker development

**Required for production:**

- AWS credentials for Bedrock Agent
- Database URLs for production databases
- API keys for Amazon Product API and Google Search API

## Testing

Run all tests:

```bash
npm test
```

Run specific test suites:

```bash
npm run test:frontend
cd python-backend && python -m pytest
```

## Deployment

Deploy to AWS:

```bash
npm run deploy
```
