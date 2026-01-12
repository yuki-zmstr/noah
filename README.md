# Noah Reading Agent

A personalized reading agent system that learns and adapts to user reading interests, comprehension levels, and preferences to provide tailored content recommendations, summaries, and reading assistance.

## Architecture

- **Frontend**: Vue.js 3 with TypeScript and Tailwind CSS
- **Backend**: Strands agent with AWS Agent Core integration
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

### Project Structure

```
noah-reading-agent/
├── frontend/          # Vue.js frontend application
├── backend/           # Strands agent backend
├── infrastructure/    # AWS CDK infrastructure code
├── docker-compose.yml # Development databases
└── README.md
```

## Environment Variables

Copy `.env.example` to `.env` and configure:

- Database connections
- AWS credentials
- API keys (Amazon Product API, etc.)

## Testing

Run all tests:

```bash
npm test
```

Run specific test suites:

```bash
npm run test:frontend
npm run test:backend
```

## Deployment

Deploy to AWS:

```bash
npm run deploy
```
