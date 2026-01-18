#!/bin/bash

# Monitor ECS Deployment Logs
# This script helps monitor ECS logs during deployment to see migration progress

set -e

echo "📊 Monitoring Noah Backend Deployment Logs..."

# Configuration
AWS_REGION=${AWS_REGION:-"ap-northeast-1"}
STACK_NAME="NoahInfrastructureStack"
LOG_GROUP="/ecs/noah-backend"

# Get ECS cluster and service names
echo "🔍 Getting ECS resources..."
ECS_CLUSTER=$(aws cloudformation describe-stack-resources \
  --stack-name $STACK_NAME \
  --query 'StackResources[?ResourceType==`AWS::ECS::Cluster`].PhysicalResourceId' \
  --output text 2>/dev/null || echo "")

ECS_SERVICE=$(aws cloudformation describe-stack-resources \
  --stack-name $STACK_NAME \
  --query 'StackResources[?ResourceType==`AWS::ECS::Service`].PhysicalResourceId' \
  --output text 2>/dev/null || echo "")

if [[ -z "$ECS_CLUSTER" || -z "$ECS_SERVICE" ]]; then
  echo "❌ Could not find ECS resources. Make sure infrastructure is deployed."
  exit 1
fi

echo "✅ Found ECS resources:"
echo "  Cluster: $ECS_CLUSTER"
echo "  Service: $ECS_SERVICE"

# Check service status
echo ""
echo "📋 Current ECS Service Status:"
aws ecs describe-services \
  --cluster $ECS_CLUSTER \
  --services $ECS_SERVICE \
  --query 'services[0].{Status:status,RunningCount:runningCount,PendingCount:pendingCount,DesiredCount:desiredCount}' \
  --output table

# Monitor logs
echo ""
echo "📄 Monitoring logs for migration and startup messages..."
echo "Press Ctrl+C to stop monitoring"
echo ""

# Function to get latest log stream
get_latest_stream() {
  aws logs describe-log-streams \
    --log-group-name $LOG_GROUP \
    --order-by LastEventTime \
    --descending \
    --max-items 1 \
    --query 'logStreams[0].logStreamName' \
    --output text 2>/dev/null || echo ""
}

# Function to check for specific migration messages
check_migration_status() {
  local stream=$1
  if [ -n "$stream" ]; then
    # Look for migration-related messages in the last 10 minutes
    local start_time=$(date -d '10 minutes ago' +%s)000
    
    echo "🔍 Checking for migration messages in stream: $stream"
    
    # Get recent log events
    aws logs get-log-events \
      --log-group-name $LOG_GROUP \
      --log-stream-name "$stream" \
      --start-time $start_time \
      --query 'events[].message' \
      --output text 2>/dev/null | \
      grep -i -E "(migration|alembic|database.*connection|database.*successful|upgrade.*head|noah.*startup)" || \
      echo "No migration messages found yet"
  fi
}

# Initial check
LATEST_STREAM=$(get_latest_stream)
if [ -n "$LATEST_STREAM" ]; then
  check_migration_status "$LATEST_STREAM"
else
  echo "⚠️  No log streams found yet. Waiting for deployment to start..."
fi

echo ""
echo "🔄 Starting real-time log monitoring..."
echo "Look for these key messages:"
echo "  ✅ 'Database connection successful'"
echo "  ✅ 'Database migrations completed successfully'"
echo "  ✅ 'Noah Reading Agent startup completed'"
echo ""

# Start tailing logs
if [ -n "$LATEST_STREAM" ]; then
  aws logs tail $LOG_GROUP --follow --since 5m --filter-pattern "migration OR alembic OR database OR startup OR Noah" 2>/dev/null || \
  aws logs tail $LOG_GROUP --follow --since 5m 2>/dev/null || \
  echo "❌ Could not tail logs. You may need to check manually in CloudWatch."
else
  echo "⚠️  No log stream available for tailing. Check CloudWatch console manually."
fi

echo ""
echo "💡 To check logs manually:"
echo "  1. Go to CloudWatch Logs in AWS Console"
echo "  2. Find log group: $LOG_GROUP"
echo "  3. Look for recent log streams"
echo "  4. Search for: migration, alembic, database, startup"