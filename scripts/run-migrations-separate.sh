#!/bin/bash

# Run Database Migrations Separately from App Deployment
# This script runs migrations as a separate step before deploying the app

set -e

echo "🗄️ Running Database Migrations Separately..."

# Configuration
AWS_REGION=${AWS_REGION:-"ap-northeast-1"}
STACK_NAME="NoahInfrastructureStack"

# Get database connection details
echo "📋 Getting database connection details..."
DB_ENDPOINT=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --query 'Stacks[0].Outputs[?OutputKey==`DatabaseEndpoint`].OutputValue' \
  --output text)

# Get database credentials from Secrets Manager
DB_SECRET_ARN=$(aws rds describe-db-instances \
  --query 'DBInstances[?contains(DBInstanceIdentifier, `noahinfrastructurestack`)].MasterUserSecret.SecretArn' \
  --output text | head -1)

DB_CREDENTIALS=$(aws secretsmanager get-secret-value \
  --secret-id "$DB_SECRET_ARN" \
  --query 'SecretString' \
  --output text)

DB_USERNAME=$(echo $DB_CREDENTIALS | jq -r '.username')
DB_PASSWORD=$(echo $DB_CREDENTIALS | jq -r '.password')
DB_NAME="noah"

# Create temporary migration container
echo "🐳 Creating temporary migration container..."
MIGRATION_IMAGE="noah-migrations:$(date +%s)"

# Create a lightweight migration Dockerfile
cat > /tmp/Dockerfile.migrations << EOF
FROM python:3.11-slim

RUN apt-get update && apt-get install -y postgresql-client && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

WORKDIR /app

# Copy only migration-related files
COPY pyproject.toml uv.lock* ./
COPY alembic.ini ./
COPY alembic/ ./alembic/
COPY src/models/ ./src/models/
COPY src/database.py ./src/database.py
COPY src/config.py ./src/config.py

# Install dependencies
RUN uv sync --frozen --no-cache

# Migration script
COPY run_migrations.py ./

CMD ["uv", "run", "python", "run_migrations.py"]
EOF

# Create migration runner script
cat > /tmp/run_migrations.py << 'EOF'
#!/usr/bin/env python3
"""Standalone migration runner."""

import os
import sys
import subprocess
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migrations():
    """Run Alembic migrations."""
    try:
        logger.info("Starting database migrations...")
        
        # Run migrations
        result = subprocess.run(
            ["uv", "run", "alembic", "upgrade", "head"],
            check=True,
            capture_output=True,
            text=True
        )
        
        logger.info("Migrations completed successfully")
        logger.info(f"Output: {result.stdout}")
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Migration failed: {e}")
        logger.error(f"Error output: {e.stderr}")
        return False

if __name__ == "__main__":
    success = run_migrations()
    sys.exit(0 if success else 1)
EOF

# Build migration image
echo "🔨 Building migration container..."
cd python-backend
cp /tmp/Dockerfile.migrations ./Dockerfile.migrations
cp /tmp/run_migrations.py ./run_migrations.py

docker build -f Dockerfile.migrations -t $MIGRATION_IMAGE .

# Run migrations in container
echo "🚀 Running migrations..."
docker run --rm \
  -e DATABASE_HOST="$DB_ENDPOINT" \
  -e DATABASE_PORT="5432" \
  -e DATABASE_NAME="$DB_NAME" \
  -e DATABASE_USER="$DB_USERNAME" \
  -e DATABASE_PASSWORD="$DB_PASSWORD" \
  $MIGRATION_IMAGE

# Cleanup
docker rmi $MIGRATION_IMAGE
rm -f Dockerfile.migrations run_migrations.py

echo "✅ Migrations completed successfully!"