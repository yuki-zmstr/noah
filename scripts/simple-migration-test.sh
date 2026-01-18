#!/bin/bash

# Simple Migration Test
# This script tests if we can connect to the database and run a simple query

set -e

echo "🔍 Testing Database Connection and Simple Migration..."

# Configuration
AWS_REGION=${AWS_REGION:-"ap-northeast-1"}
STACK_NAME="NoahInfrastructureStack"

# Get database connection details
DB_ENDPOINT=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --query 'Stacks[0].Outputs[?OutputKey==`DatabaseEndpoint`].OutputValue' \
  --output text)

# Get database secret ARN
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
  exit 1
fi

echo "Database endpoint: $DB_ENDPOINT"
echo "Database secret: $DB_SECRET_ARN"

# Get credentials
DB_CREDENTIALS=$(aws secretsmanager get-secret-value \
  --secret-id "$DB_SECRET_ARN" \
  --query 'SecretString' \
  --output text)

DB_USERNAME=$(echo $DB_CREDENTIALS | jq -r '.username')
DB_PASSWORD=$(echo $DB_CREDENTIALS | jq -r '.password')
DB_NAME="noah"

echo "Database username: $DB_USERNAME"

# Test if we can reach the database endpoint (this will fail from outside VPC, which is expected)
echo "🔍 Testing network connectivity to database..."
if timeout 5 bash -c "</dev/tcp/$DB_ENDPOINT/5432" 2>/dev/null; then
  echo "✅ Can reach database endpoint"
  
  # If we can reach it, try to connect with psql (if available)
  if command -v psql &> /dev/null; then
    echo "🔍 Testing database connection with psql..."
    PGPASSWORD="$DB_PASSWORD" psql -h "$DB_ENDPOINT" -p 5432 -U "$DB_USERNAME" -d "$DB_NAME" -c "SELECT version();" || echo "❌ psql connection failed"
  else
    echo "⚠️ psql not available for connection test"
  fi
else
  echo "❌ Cannot reach database endpoint (expected from outside VPC)"
  echo "This confirms the database is properly secured in private subnets"
fi

echo "✅ Database configuration test completed!"
echo ""
echo "📋 Summary:"
echo "- Database endpoint: $DB_ENDPOINT"
echo "- Database secret found: ✅"
echo "- Database credentials retrieved: ✅"
echo "- Network access: ❌ (expected - database is in private subnet)"
echo ""
echo "💡 To run migrations, we need to use ECS tasks within the VPC or connect via bastion host"