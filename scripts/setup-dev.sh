#!/bin/bash

# Noah Reading Agent Development Setup Script

set -e

echo "🚀 Setting up Noah Reading Agent development environment..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Install root dependencies
echo "📦 Installing root dependencies..."
npm install

# Install frontend dependencies
echo "📦 Installing frontend dependencies..."
cd frontend && npm install && cd ..

# Install backend dependencies
echo "📦 Installing backend dependencies..."
cd backend && npm install && cd ..

# Install infrastructure dependencies
echo "📦 Installing infrastructure dependencies..."
cd infrastructure && npm install && cd ..

# Copy environment files if they don't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please update .env with your configuration"
fi

if [ ! -f frontend/.env ]; then
    echo "📝 Creating frontend .env file from template..."
    cp frontend/.env.example frontend/.env
fi

# Start development databases
echo "🐳 Starting development databases..."
docker compose up -d

# Wait for databases to be ready
echo "⏳ Waiting for databases to be ready..."
sleep 10

# Check database health
echo "🔍 Checking database health..."
docker compose ps

echo "✅ Development environment setup complete!"
echo ""
echo "Next steps:"
echo "1. Update .env files with your configuration"
echo "2. Run 'npm run dev' to start development servers"
echo "3. Visit http://localhost:3000 to see the frontend"
echo "4. Backend API will be available at http://localhost:8000"
echo ""
echo "Database URLs:"
echo "- PostgreSQL: postgresql://noah_user:noah_password@localhost:5432/noah_dev"
echo "- Redis: redis://localhost:6379"
echo "- OpenSearch: http://localhost:9200"
echo "- OpenSearch Dashboards: http://localhost:5601"