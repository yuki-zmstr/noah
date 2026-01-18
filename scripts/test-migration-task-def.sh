#!/bin/bash

# Test Migration Task Definition Generation
# This script tests the task definition generation logic locally

set -e

echo "🧪 Testing Migration Task Definition Generation..."

# Configuration
AWS_REGION=${AWS_REGION:-"ap-northeast-1"}
STACK_NAME="NoahInfrastructureStack"
ECR_REPOSITORY="noah-backend"

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

# Get ECR repository URI and use a test image
ECR_URI=$(aws ecr describe-repositories --repository-names $ECR_REPOSITORY --query 'repositories[0].repositoryUri' --output text)
MIGRATION_IMAGE="$ECR_URI:latest"

echo "Using migration image: $MIGRATION_IMAGE"

# Create a modified task definition for migrations
echo "📝 Creating migration task definition..."

# Save the original task definition to a file
echo "$TASK_DEFINITION" > /tmp/original-task-def.json

# Create the migration task definition using jq
jq --arg IMAGE "$MIGRATION_IMAGE" '
  .family = "noah-migrations-test" |
  .containerDefinitions[0].image = $IMAGE |
  .containerDefinitions[0].name = "migration-container" |
  .containerDefinitions[0].command = ["uv", "run", "alembic", "upgrade", "head"] |
  .containerDefinitions[0].logConfiguration.options."awslogs-group" = "/ecs/noah-migrations" |
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

# Show the generated task definition
echo "📋 Generated migration task definition:"
jq . /tmp/migration-task-def.json

# Test registering the task definition (dry run)
echo "🧪 Testing task definition registration..."
MIGRATION_TASK_DEF_ARN=$(aws ecs register-task-definition --cli-input-json file:///tmp/migration-task-def.json --query 'taskDefinition.taskDefinitionArn' --output text)

echo "✅ Migration task definition registered successfully: $MIGRATION_TASK_DEF_ARN"

# Clean up the test task definition
echo "🧹 Cleaning up test task definition..."
aws ecs deregister-task-definition --task-definition $MIGRATION_TASK_DEF_ARN > /dev/null

echo "✅ Test completed successfully!"

# Clean up temp files
rm -f /tmp/original-task-def.json /tmp/migration-task-def.json