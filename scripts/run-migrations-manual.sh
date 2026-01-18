#!/bin/bash

# Manual Migration Runner
# This script runs database migrations using the same approach as the deployment workflow

set -e

echo "🗄️ Running database migrations manually via ECS task..."

# Configuration
AWS_REGION=${AWS_REGION:-"ap-northeast-1"}
STACK_NAME="NoahInfrastructureStack"
ECR_REPOSITORY="noah-backend"

# Allow override of image tag
IMAGE_TAG=${IMAGE_TAG:-"latest"}

# Get ECS cluster and service information
ECS_CLUSTER=$(aws cloudformation describe-stack-resources \
  --stack-name $STACK_NAME \
  --query 'StackResources[?ResourceType==`AWS::ECS::Cluster`].PhysicalResourceId' \
  --output text)

ECS_SERVICE=$(aws cloudformation describe-stack-resources \
  --stack-name $STACK_NAME \
  --query 'StackResources[?ResourceType==`AWS::ECS::Service`].PhysicalResourceId' \
  --output text)

echo "Using ECS cluster: $ECS_CLUSTER"
echo "Using ECS service: $ECS_SERVICE"

# Get the current task definition from the service
CURRENT_TASK_DEF_ARN=$(aws ecs describe-services \
  --cluster $ECS_CLUSTER \
  --services $ECS_SERVICE \
  --query 'services[0].taskDefinition' \
  --output text)

echo "Current task definition: $CURRENT_TASK_DEF_ARN"

# Get the task definition details
TASK_DEFINITION=$(aws ecs describe-task-definition \
  --task-definition $CURRENT_TASK_DEF_ARN \
  --query 'taskDefinition')

# Get ECR repository URI and use the specified image
ECR_URI=$(aws ecr describe-repositories --repository-names $ECR_REPOSITORY --query 'repositories[0].repositoryUri' --output text)
MIGRATION_IMAGE="$ECR_URI:$IMAGE_TAG"

echo "Using migration image: $MIGRATION_IMAGE"

# Create a modified task definition for migrations
echo "📝 Creating migration task definition..."

# Save the original task definition to a file
echo "$TASK_DEFINITION" > /tmp/original-task-def.json

# Create the migration task definition using jq
jq --arg IMAGE "$MIGRATION_IMAGE" '
  .family = "noah-migrations-manual" |
  .containerDefinitions[0].image = $IMAGE |
  .containerDefinitions[0].name = "migration-container" |
  .containerDefinitions[0].command = ["uv", "run", "alembic", "upgrade", "head"] |
  del(.taskDefinitionArn, .revision, .status, .requiresAttributes, .placementConstraints, .compatibilities, .registeredAt, .registeredBy)
' /tmp/original-task-def.json > /tmp/migration-task-def.json

# Verify the JSON is valid
if ! jq empty /tmp/migration-task-def.json; then
  echo "❌ Generated task definition JSON is invalid"
  echo "Original task definition:"
  cat /tmp/original-task-def.json
  echo "Generated migration task definition:"
  cat /tmp/migration-task-def.json
  exit 1
fi

echo "✅ Migration task definition created successfully"

# Register the migration task definition
echo "📝 Registering migration task definition..."
MIGRATION_TASK_DEF_ARN=$(aws ecs register-task-definition --cli-input-json file:///tmp/migration-task-def.json --query 'taskDefinition.taskDefinitionArn' --output text)

echo "Migration task definition registered: $MIGRATION_TASK_DEF_ARN"

# Get network configuration from the existing service
NETWORK_CONFIG=$(aws ecs describe-services \
  --cluster $ECS_CLUSTER \
  --services $ECS_SERVICE \
  --query 'services[0].networkConfiguration' \
  --output json)

echo "Network configuration: $NETWORK_CONFIG"

# Run the migration task
echo "🚀 Running migration task..."
TASK_ARN=$(aws ecs run-task \
  --cluster $ECS_CLUSTER \
  --task-definition $MIGRATION_TASK_DEF_ARN \
  --launch-type FARGATE \
  --network-configuration "$NETWORK_CONFIG" \
  --query 'tasks[0].taskArn' \
  --output text)

echo "Migration task started: $TASK_ARN"

# Wait for task to complete
echo "⏳ Waiting for migration task to complete..."
aws ecs wait tasks-stopped --cluster $ECS_CLUSTER --tasks $TASK_ARN

# Check task exit code
TASK_STATUS=$(aws ecs describe-tasks \
  --cluster $ECS_CLUSTER \
  --tasks $TASK_ARN \
  --query 'tasks[0].containers[0].exitCode' \
  --output text)

if [ "$TASK_STATUS" = "0" ]; then
  echo "✅ Migration task completed successfully!"
else
  echo "❌ Migration task failed with exit code: $TASK_STATUS"
  
  # Get logs for debugging
  echo "📋 Migration task logs:"
  TASK_ID=$(echo $TASK_ARN | cut -d'/' -f3)
  
  # Get the log group name from the task definition
  LOG_GROUP=$(jq -r '.containerDefinitions[0].logConfiguration.options."awslogs-group"' /tmp/migration-task-def.json)
  
  # Try to get logs with different approaches
  echo "Attempting to retrieve logs for task: $TASK_ID from log group: $LOG_GROUP"
  
  # First, list available log streams
  echo "Available log streams:"
  aws logs describe-log-streams \
    --log-group-name "$LOG_GROUP" \
    --query 'logStreams[].logStreamName' \
    --output text || echo "Could not list log streams"
  
  # Try to get logs from the most recent stream
  RECENT_STREAM=$(aws logs describe-log-streams \
    --log-group-name "$LOG_GROUP" \
    --order-by LastEventTime \
    --descending \
    --max-items 1 \
    --query 'logStreams[0].logStreamName' \
    --output text 2>/dev/null || echo "")
  
  if [ -n "$RECENT_STREAM" ] && [ "$RECENT_STREAM" != "None" ]; then
    echo "Getting logs from stream: $RECENT_STREAM"
    aws logs get-log-events \
      --log-group-name "$LOG_GROUP" \
      --log-stream-name "$RECENT_STREAM" \
      --query 'events[].message' \
      --output text || echo "Could not retrieve logs from recent stream"
  else
    echo "No log streams found or could not determine recent stream"
  fi
  
  exit 1
fi

# Clean up the task definition
echo "🧹 Cleaning up migration task definition..."
aws ecs deregister-task-definition --task-definition $MIGRATION_TASK_DEF_ARN > /dev/null

# Clean up temp files
rm -f /tmp/original-task-def.json /tmp/migration-task-def.json

echo "✅ Database migrations completed successfully!"