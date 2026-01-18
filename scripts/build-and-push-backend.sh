#!/bin/bash

# Build and Push Noah Backend Docker Image
# This script builds the backend Docker image and pushes it to ECR

set -e

echo "🐳 Building and Pushing Noah Backend..."

# Configuration
AWS_REGION="ap-northeast-1"
ECR_REPOSITORY="noah-backend"
STACK_NAME="NoahInfrastructureStack"

# Check AWS CLI and credentials
echo "🔐 Checking AWS credentials..."
if ! aws sts get-caller-identity &> /dev/null; then
  echo "❌ AWS credentials not configured or invalid"
  exit 1
fi

# Get ECR repository URI from CloudFormation
echo "📋 Getting ECR repository URI..."
ECR_URI=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --query 'Stacks[0].Outputs[?OutputKey==`EcrRepositoryUri`].OutputValue' \
  --output text 2>/dev/null || echo "")

if [[ -z "$ECR_URI" || "$ECR_URI" == "None" ]]; then
  echo "❌ ECR repository URI not found. Make sure infrastructure is deployed first."
  echo "Run: ./scripts/deploy-infrastructure.sh"
  exit 1
fi

echo "✅ Found ECR repository: $ECR_URI"

# Login to ECR
echo "🔑 Logging into ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_URI

# Build Docker image
echo "🔨 Building Docker image..."
cd python-backend

# Create a simple .dockerignore if it doesn't exist
if [ ! -f .dockerignore ]; then
  cat > .dockerignore << EOF
.git
.pytest_cache
__pycache__
*.pyc
*.pyo
*.pyd
.env
.venv
venv/
.coverage
.tox
.cache
.DS_Store
*.egg-info/
dist/
build/
EOF
fi

# Build the image
IMAGE_TAG=$(git rev-parse --short HEAD 2>/dev/null || echo "latest")
docker build -t $ECR_REPOSITORY:$IMAGE_TAG .
docker tag $ECR_REPOSITORY:$IMAGE_TAG $ECR_URI:$IMAGE_TAG
docker tag $ECR_REPOSITORY:$IMAGE_TAG $ECR_URI:latest

echo "📤 Pushing Docker image..."
docker push $ECR_URI:$IMAGE_TAG
docker push $ECR_URI:latest

echo "✅ Docker image pushed successfully!"
echo "Image URI: $ECR_URI:$IMAGE_TAG"

# Update ECS service if it exists
echo "🔄 Checking if ECS service needs update..."
ECS_CLUSTER=$(aws cloudformation describe-stack-resources \
  --stack-name $STACK_NAME \
  --query 'StackResources[?ResourceType==`AWS::ECS::Cluster`].PhysicalResourceId' \
  --output text 2>/dev/null || echo "")

ECS_SERVICE=$(aws cloudformation describe-stack-resources \
  --stack-name $STACK_NAME \
  --query 'StackResources[?ResourceType==`AWS::ECS::Service`].PhysicalResourceId' \
  --output text 2>/dev/null || echo "")

if [[ -n "$ECS_CLUSTER" && -n "$ECS_SERVICE" && "$ECS_CLUSTER" != "None" && "$ECS_SERVICE" != "None" ]]; then
  echo "🚀 Updating ECS service with new image..."
  
  # Get current task definition
  TASK_DEFINITION=$(aws ecs describe-task-definition --task-definition $ECS_SERVICE --query 'taskDefinition')
  
  # Update image URI in task definition
  NEW_TASK_DEFINITION=$(echo $TASK_DEFINITION | jq --arg IMAGE "$ECR_URI:$IMAGE_TAG" '.containerDefinitions[0].image = $IMAGE | del(.taskDefinitionArn) | del(.revision) | del(.status) | del(.requiresAttributes) | del(.placementConstraints) | del(.compatibilities) | del(.registeredAt) | del(.registeredBy)')
  
  # Register new task definition
  NEW_TASK_DEF_ARN=$(echo $NEW_TASK_DEFINITION | aws ecs register-task-definition --cli-input-json file:///dev/stdin --query 'taskDefinition.taskDefinitionArn' --output text)
  
  # Update service
  aws ecs update-service --cluster $ECS_CLUSTER --service $ECS_SERVICE --task-definition $NEW_TASK_DEF_ARN
  
  echo "⏳ Waiting for deployment to complete..."
  aws ecs wait services-stable --cluster $ECS_CLUSTER --services $ECS_SERVICE
  
  echo "✅ ECS service updated successfully!"
else
  echo "ℹ️  ECS service not found or not ready. Deploy infrastructure first."
fi

cd ..

echo ""
echo "🎉 Backend build and push completed!"
echo "Next steps:"
echo "1. Test the deployment: ./scripts/health-monitoring-dashboard.sh"
echo "2. Check logs in CloudWatch: /aws/ecs/noah-backend"