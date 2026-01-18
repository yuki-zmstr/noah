#!/bin/bash

# Deploy backend with database migrations
# This script builds and deploys the backend, ensuring migrations are run

set -e

echo "🚀 Starting Noah Reading Agent Backend Deployment with Migrations"

# Configuration
AWS_REGION=${AWS_REGION:-"ap-northeast-1"}
ECR_REPOSITORY_NAME="noah-backend"
ECS_CLUSTER_NAME="NoahInfrastructureStack-NoahCluster"
ECS_SERVICE_NAME="NoahInfrastructureStack-NoahBackendService"

# Get AWS account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_REPOSITORY_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY_NAME}"

echo "📋 Configuration:"
echo "  AWS Region: $AWS_REGION"
echo "  AWS Account: $AWS_ACCOUNT_ID"
echo "  ECR Repository: $ECR_REPOSITORY_URI"
echo "  ECS Cluster: $ECS_CLUSTER_NAME"
echo "  ECS Service: $ECS_SERVICE_NAME"

# Step 1: Build and push Docker image
echo "🔨 Building Docker image..."
cd python-backend

# Login to ECR
echo "🔐 Logging in to ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_REPOSITORY_URI

# Build image with timestamp tag
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
IMAGE_TAG="deploy-${TIMESTAMP}"

echo "🏗️  Building image with tag: $IMAGE_TAG"
docker build --platform linux/amd64 -t $ECR_REPOSITORY_NAME:$IMAGE_TAG .
docker tag $ECR_REPOSITORY_NAME:$IMAGE_TAG $ECR_REPOSITORY_URI:$IMAGE_TAG
docker tag $ECR_REPOSITORY_NAME:$IMAGE_TAG $ECR_REPOSITORY_URI:latest

# Push image
echo "📤 Pushing image to ECR..."
docker push $ECR_REPOSITORY_URI:$IMAGE_TAG
docker push $ECR_REPOSITORY_URI:latest

echo "✅ Image pushed successfully: $ECR_REPOSITORY_URI:$IMAGE_TAG"

# Step 2: Update ECS service
echo "🔄 Updating ECS service..."

# Force new deployment to pick up the new image
aws ecs update-service \
    --cluster $ECS_CLUSTER_NAME \
    --service $ECS_SERVICE_NAME \
    --force-new-deployment \
    --region $AWS_REGION

echo "⏳ Waiting for deployment to complete..."

# Wait for service to stabilize
aws ecs wait services-stable \
    --cluster $ECS_CLUSTER_NAME \
    --services $ECS_SERVICE_NAME \
    --region $AWS_REGION

echo "✅ ECS service updated successfully!"

# Step 3: Verify deployment
echo "🔍 Verifying deployment..."

# Get the load balancer URL
LB_DNS=$(aws elbv2 describe-load-balancers \
    --query "LoadBalancers[?contains(LoadBalancerName, 'NoahInfrastructureStack')].DNSName" \
    --output text \
    --region $AWS_REGION)

if [ -n "$LB_DNS" ]; then
    echo "🌐 Load Balancer URL: http://$LB_DNS"
    
    # Test health endpoint
    echo "🏥 Testing health endpoint..."
    for i in {1..10}; do
        if curl -f -s "http://$LB_DNS/health" > /dev/null; then
            echo "✅ Health check passed!"
            break
        else
            echo "⏳ Waiting for service to be healthy... (attempt $i/10)"
            sleep 30
        fi
    done
else
    echo "⚠️  Could not find load balancer DNS name"
fi

echo "🎉 Deployment completed successfully!"
echo ""
echo "📝 Next steps:"
echo "  1. The new image includes automatic database migrations"
echo "  2. Migrations will run automatically when the container starts"
echo "  3. Monitor the ECS service logs to ensure migrations complete successfully"
echo "  4. Test your API endpoints to verify everything is working"
echo ""
echo "🔗 Useful commands:"
echo "  View ECS service logs:"
echo "    aws logs tail /ecs/noah-backend --follow --region $AWS_REGION"
echo ""
echo "  Check ECS service status:"
echo "    aws ecs describe-services --cluster $ECS_CLUSTER_NAME --services $ECS_SERVICE_NAME --region $AWS_REGION"

cd ..