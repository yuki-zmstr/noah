#!/bin/bash

# Check Migration Status
# This script checks the current migration status of the database

set -e

echo "📋 Checking database migration status..."

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

# Get the current task definition from the service
CURRENT_TASK_DEF_ARN=$(aws ecs describe-services \
  --cluster $ECS_CLUSTER \
  --services $ECS_SERVICE \
  --query 'services[0].taskDefinition' \
  --output text)

# Get the task definition details
TASK_DEFINITION=$(aws ecs describe-task-definition \
  --task-definition $CURRENT_TASK_DEF_ARN \
  --query 'taskDefinition')

# Get ECR repository URI and use the specified image
ECR_URI=$(aws ecr describe-repositories --repository-names $ECR_REPOSITORY --query 'repositories[0].repositoryUri' --output text)
MIGRATION_IMAGE="$ECR_URI:$IMAGE_TAG"

echo "Using migration image: $MIGRATION_IMAGE"

# Create a modified task definition for checking migration status
echo "📝 Creating migration status check task definition..."

# Save the original task definition to a file
echo "$TASK_DEFINITION" > /tmp/original-task-def.json

# Create the migration status check task definition using jq
jq --arg IMAGE "$MIGRATION_IMAGE" '
  .family = "noah-migration-status" |
  .containerDefinitions[0].image = $IMAGE |
  .containerDefinitions[0].name = "migration-status-container" |
  .containerDefinitions[0].command = ["uv", "run", "alembic", "current", "-v"] |
  del(.taskDefinitionArn, .revision, .status, .requiresAttributes, .placementConstraints, .compatibilities, .registeredAt, .registeredBy)
' /tmp/original-task-def.json > /tmp/migration-status-task-def.json

# Register the migration status task definition
echo "📝 Registering migration status task definition..."
MIGRATION_TASK_DEF_ARN=$(aws ecs register-task-definition --cli-input-json file:///tmp/migration-status-task-def.json --query 'taskDefinition.taskDefinitionArn' --output text)

echo "Migration status task definition registered: $MIGRATION_TASK_DEF_ARN"

# Get network configuration from the existing service
NETWORK_CONFIG=$(aws ecs describe-services \
  --cluster $ECS_CLUSTER \
  --services $ECS_SERVICE \
  --query 'services[0].networkConfiguration' \
  --output json)

# Run the migration status task
echo "🚀 Running migration status check task..."
TASK_ARN=$(aws ecs run-task \
  --cluster $ECS_CLUSTER \
  --task-definition $MIGRATION_TASK_DEF_ARN \
  --launch-type FARGATE \
  --network-configuration "$NETWORK_CONFIG" \
  --query 'tasks[0].taskArn' \
  --output text)

echo "Migration status task started: $TASK_ARN"

# Wait for task to complete
echo "⏳ Waiting for migration status task to complete..."
aws ecs wait tasks-stopped --cluster $ECS_CLUSTER --tasks $TASK_ARN

# Check task exit code
TASK_STATUS=$(aws ecs describe-tasks \
  --cluster $ECS_CLUSTER \
  --tasks $TASK_ARN \
  --query 'tasks[0].containers[0].exitCode' \
  --output text)

# Get the log group name from the task definition
LOG_GROUP=$(jq -r '.containerDefinitions[0].logConfiguration.options."awslogs-group"' /tmp/migration-status-task-def.json)

# Get logs
echo "📋 Migration status output:"
TASK_ID=$(echo $TASK_ARN | cut -d'/' -f3)

# Wait a moment for logs to be available
sleep 5

# Get logs from the specific stream
aws logs get-log-events \
  --log-group-name "$LOG_GROUP" \
  --log-stream-name "noah-backend/migration-status-container/$TASK_ID" \
  --query 'events[].message' \
  --output text || echo "Could not retrieve logs"

if [ "$TASK_STATUS" = "0" ]; then
  echo "✅ Migration status check completed successfully!"
else
  echo "❌ Migration status check failed with exit code: $TASK_STATUS"
fi

# Clean up the task definition
echo "🧹 Cleaning up migration status task definition..."
aws ecs deregister-task-definition --task-definition $MIGRATION_TASK_DEF_ARN > /dev/null

# Clean up temp files
rm -f /tmp/original-task-def.json /tmp/migration-status-task-def.json

echo "✅ Migration status check completed!"