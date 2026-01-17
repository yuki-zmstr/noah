#!/bin/bash

# Build and push Docker image to Amazon ECR
# This script builds the backend Docker image and pushes it to ECR for deployment

set -e

echo "🐳 Building and pushing Noah backend Docker image..."

# Get AWS account ID and region
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=$(aws configure get region)

if [ -z "$AWS_REGION" ]; then
    AWS_REGION="us-east-1"
    echo "⚠️  No AWS region configured, defaulting to us-east-1"
fi

# ECR repository name
ECR_REPO_NAME="noah-backend"
ECR_URI="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO_NAME"

echo "📋 Configuration:"
echo "   AWS Account: $AWS_ACCOUNT_ID"
echo "   AWS Region: $AWS_REGION"
echo "   ECR Repository: $ECR_URI"

# Create ECR repository if it doesn't exist
echo "🏗️  Creating ECR repository if it doesn't exist..."
aws ecr describe-repositories --repository-names $ECR_REPO_NAME --region $AWS_REGION 2>/dev/null || \
aws ecr create-repository --repository-name $ECR_REPO_NAME --region $AWS_REGION

# Get ECR login token
echo "🔐 Logging in to ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_URI

# Build Docker image
echo "🔨 Building Docker image..."
cd python-backend
docker build -t $ECR_REPO_NAME:latest .

# Tag image for ECR
echo "🏷️  Tagging image for ECR..."
docker tag $ECR_REPO_NAME:latest $ECR_URI:latest
docker tag $ECR_REPO_NAME:latest $ECR_URI:$(date +%Y%m%d-%H%M%S)

# Push image to ECR
echo "📤 Pushing image to ECR..."
docker push $ECR_URI:latest
docker push $ECR_URI:$(date +%Y%m%d-%H%M%S)

echo "✅ Docker image pushed successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Update your ECS service to use the new image:"
echo "   Image URI: $ECR_URI:latest"
echo ""
echo "2. Or update your CDK stack to use the ECR image:"
echo "   image: ecs.ContainerImage.fromEcrRepository(ecrRepository, 'latest')"
echo ""
echo "3. Deploy your infrastructure:"
echo "   cd ../infrastructure && cdk deploy"