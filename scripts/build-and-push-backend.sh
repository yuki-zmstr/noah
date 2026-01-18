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
  
  # Extract cluster and service names from ARNs
  CLUSTER_NAME=$(echo $ECS_CLUSTER | cut -d'/' -f2)
  SERVICE_NAME=$(echo $ECS_SERVICE | cut -d'/' -f3)
  
  # Get current task definition ARN from the service
  echo "📋 Getting current task definition from service..."
  CURRENT_TASK_DEF_ARN=$(aws ecs describe-services \
    --cluster $CLUSTER_NAME \
    --services $SERVICE_NAME \
    --query 'services[0].taskDefinition' \
    --output text)
  
  if [[ -z "$CURRENT_TASK_DEF_ARN" || "$CURRENT_TASK_DEF_ARN" == "None" ]]; then
    echo "❌ Could not get current task definition from service"
    exit 1
  fi
  
  echo "Current task definition: $CURRENT_TASK_DEF_ARN"
  
  # Get current task definition
  echo "📋 Getting current task definition..."
  TASK_DEFINITION=$(aws ecs describe-task-definition --task-definition $CURRENT_TASK_DEF_ARN --query 'taskDefinition' --output json)
  
  # Create a temporary file for the new task definition
  TEMP_TASK_DEF=$(mktemp)
  
  # Update image URI in task definition and clean up fields
  echo $TASK_DEFINITION | jq --arg IMAGE "$ECR_URI:$IMAGE_TAG" '
    .containerDefinitions[0].image = $IMAGE |
    del(.taskDefinitionArn, .revision, .status, .requiresAttributes, .placementConstraints, .compatibilities, .registeredAt, .registeredBy)
  ' > $TEMP_TASK_DEF
  
  # Validate the JSON before using it
  if ! jq empty $TEMP_TASK_DEF 2>/dev/null; then
    echo "❌ Generated task definition JSON is invalid"
    cat $TEMP_TASK_DEF
    rm $TEMP_TASK_DEF
    exit 1
  fi
  
  # Register new task definition
  echo "📝 Registering new task definition..."
  NEW_TASK_DEF_ARN=$(aws ecs register-task-definition --cli-input-json file://$TEMP_TASK_DEF --query 'taskDefinition.taskDefinitionArn' --output text)
  
  # Clean up temp file
  rm $TEMP_TASK_DEF
  
  # Update service
  aws ecs update-service --cluster $CLUSTER_NAME --service $SERVICE_NAME --task-definition $NEW_TASK_DEF_ARN
  
  echo "⏳ Waiting for deployment to complete..."
  aws ecs wait services-stable --cluster $CLUSTER_NAME --services $SERVICE_NAME
  
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