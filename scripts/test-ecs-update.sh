#!/bin/bash

# Test ECS Service Update Logic
# This script tests the ECS service update task definition generation

set -e

echo "🧪 Testing ECS Service Update Logic..."

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

# Get current task definition from the service
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
NEW_IMAGE="$ECR_URI:test-$(date +%s)"

echo "Test image URI: $NEW_IMAGE"

# Save the task definition to a file
echo "$TASK_DEFINITION" > /tmp/current-task-def.json

# Create jq script for updating the task definition
cat > /tmp/update-jq-script.jq << 'EOF'
def remove_fields: del(.taskDefinitionArn, .revision, .status, .requiresAttributes, .placementConstraints, .compatibilities, .registeredAt, .registeredBy);

.containerDefinitions[0].image = $IMAGE |
remove_fields
EOF

echo "📝 Creating updated task definition..."

# Update image URI in task definition
jq --arg IMAGE "$NEW_IMAGE" -f /tmp/update-jq-script.jq /tmp/current-task-def.json > /tmp/new-task-def.json

# Verify the JSON is valid
if ! jq empty /tmp/new-task-def.json; then
  echo "❌ Generated task definition JSON is invalid"
  echo "Current task definition:"
  cat /tmp/current-task-def.json
  echo "New task definition:"
  cat /tmp/new-task-def.json
  exit 1
fi

echo "✅ Task definition updated successfully"

# Show the changes
echo "📋 Task definition changes:"
echo "Original image: $(jq -r '.containerDefinitions[0].image' /tmp/current-task-def.json)"
echo "New image: $(jq -r '.containerDefinitions[0].image' /tmp/new-task-def.json)"
echo "Family: $(jq -r '.family' /tmp/new-task-def.json)"

# Test registering the task definition (but don't actually use it)
echo "🧪 Testing task definition registration..."
NEW_TASK_DEF_ARN=$(aws ecs register-task-definition --cli-input-json file:///tmp/new-task-def.json --query 'taskDefinition.taskDefinitionArn' --output text)

echo "✅ New task definition registered successfully: $NEW_TASK_DEF_ARN"

# Clean up the test task definition
echo "🧹 Cleaning up test task definition..."
aws ecs deregister-task-definition --task-definition $NEW_TASK_DEF_ARN > /dev/null

# Clean up temporary files
rm -f /tmp/current-task-def.json /tmp/new-task-def.json /tmp/update-jq-script.jq

echo "✅ ECS service update test completed successfully!"