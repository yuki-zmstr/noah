#!/bin/bash

# Test Database Connection
# This script tests the database connection using the same logic as the deployment
# Updated: Migration test completed successfully
# Updated: ECS service update fix applied

set -e

echo "🔍 Testing Database Connection..."

# Configuration
AWS_REGION=${AWS_REGION:-"ap-northeast-1"}
STACK_NAME="NoahInfrastructureStack"

# Get database connection details
echo "📋 Getting database connection details..."
DB_ENDPOINT=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --query 'Stacks[0].Outputs[?OutputKey==`DatabaseEndpoint`].OutputValue' \
  --output text)

echo "Database endpoint: $DB_ENDPOINT"

# Get database credentials from Secrets Manager
echo "📋 Finding database secret..."
DB_SECRET_ARN=$(aws secretsmanager list-secrets \
  --query 'SecretList[?contains(Name, `NoahInfrastructureStack`)].ARN' \
  --output text | head -1)

if [ -z "$DB_SECRET_ARN" ]; then
  echo "Trying alternative secret discovery method..."
  DB_SECRET_ARN=$(aws secretsmanager list-secrets \
    --query 'SecretList[?contains(Name, `Noah`)].ARN' \
    --output text | head -1)
fi

if [ -z "$DB_SECRET_ARN" ]; then
  echo "❌ Could not find database secret"
  echo "Available secrets:"
  aws secretsmanager list-secrets --query 'SecretList[].Name' --output text
  exit 1
fi

echo "Found database secret: $DB_SECRET_ARN"

# Get credentials
DB_CREDENTIALS=$(aws secretsmanager get-secret-value \
  --secret-id "$DB_SECRET_ARN" \
  --query 'SecretString' \
  --output text)

DB_USERNAME=$(echo $DB_CREDENTIALS | jq -r '.username')
DB_PASSWORD=$(echo $DB_CREDENTIALS | jq -r '.password')
DB_NAME="noah"

echo "Database username: $DB_USERNAME"
echo "Database name: $DB_NAME"

# Test connection using psql if available
if command -v psql &> /dev/null; then
  echo "🔍 Testing connection with psql..."
  PGPASSWORD="$DB_PASSWORD" psql -h "$DB_ENDPOINT" -p 5432 -U "$DB_USERNAME" -d "$DB_NAME" -c "SELECT version();" || echo "❌ psql connection failed"
else
  echo "⚠️ psql not available, skipping direct connection test"
fi

# Test connection using Python if available
if command -v python3 &> /dev/null; then
  echo "🔍 Testing connection with Python..."
  python3 -c "
import psycopg2
try:
    conn = psycopg2.connect(
        host='$DB_ENDPOINT',
        port=5432,
        database='$DB_NAME',
        user='$DB_USERNAME',
        password='$DB_PASSWORD'
    )
    cursor = conn.cursor()
    cursor.execute('SELECT version();')
    version = cursor.fetchone()
    print('✅ Python connection successful!')
    print(f'Database version: {version[0]}')
    cursor.close()
    conn.close()
except Exception as e:
    print(f'❌ Python connection failed: {e}')
" || echo "❌ Python connection test failed (psycopg2 may not be installed)"
fi

echo "✅ Database connection test completed!"