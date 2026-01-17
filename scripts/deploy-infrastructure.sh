#!/bin/bash

# Complete deployment script for Noah Reading Agent infrastructure
# This script deploys the entire AWS infrastructure including Cognito, Amplify, ECS, and RDS

set -e

echo "🚀 Deploying Noah Reading Agent infrastructure..."

# Check prerequisites
echo "🔍 Checking prerequisites..."

if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI is not installed. Please install it first."
    exit 1
fi

if ! command -v cdk &> /dev/null; then
    echo "❌ AWS CDK is not installed. Please install it first."
    echo "Run: npm install -g aws-cdk"
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install it first."
    exit 1
fi

# Get configuration
STACK_NAME=${1:-NoahInfrastructureStack}
AWS_REGION=$(aws configure get region)

if [ -z "$AWS_REGION" ]; then
    AWS_REGION="us-east-1"
    echo "⚠️  No AWS region configured, defaulting to us-east-1"
fi

echo "📋 Deployment configuration:"
echo "   Stack Name: $STACK_NAME"
echo "   AWS Region: $AWS_REGION"

# Step 1: Install CDK dependencies
echo "📦 Installing CDK dependencies..."
cd infrastructure
npm install

# Step 2: Bootstrap CDK (if not already done)
echo "🏗️  Bootstrapping CDK..."
cdk bootstrap --region $AWS_REGION || echo "CDK already bootstrapped"

# Step 3: Deploy infrastructure
echo "🚀 Deploying infrastructure stack..."
cdk deploy --require-approval never

# Step 4: Build and push Docker image
echo "🐳 Building and pushing backend Docker image..."
cd ..
./scripts/build-and-push.sh

# Step 5: Update ECS service with new image
echo "🔄 Updating ECS service..."
CLUSTER_NAME=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --query "Stacks[0].Outputs[?contains(OutputKey, 'Cluster')].OutputValue" --output text 2>/dev/null || echo "")
SERVICE_NAME=$(aws ecs list-services --cluster $CLUSTER_NAME --query "serviceArns[0]" --output text 2>/dev/null | cut -d'/' -f3 || echo "")

if [ -n "$CLUSTER_NAME" ] && [ -n "$SERVICE_NAME" ]; then
    echo "   Forcing new deployment for ECS service..."
    aws ecs update-service --cluster $CLUSTER_NAME --service $SERVICE_NAME --force-new-deployment
else
    echo "⚠️  Could not find ECS cluster/service. Manual deployment may be required."
fi

# Step 6: Configure Cognito and environment variables
echo "🔧 Setting up Cognito configuration..."
./scripts/setup-cognito.sh $STACK_NAME

# Step 7: Set up Amplify
echo "📱 Setting up Amplify configuration..."
./scripts/setup-amplify.sh $STACK_NAME

# Get deployment URLs
echo "✅ Deployment completed successfully!"
echo ""
echo "📋 Deployment Summary:"

USER_POOL_ID=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --query "Stacks[0].Outputs[?OutputKey=='UserPoolId'].OutputValue" --output text 2>/dev/null || echo "Not found")
BACKEND_URL=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --query "Stacks[0].Outputs[?OutputKey=='BackendUrl'].OutputValue" --output text 2>/dev/null || echo "Not found")
AMPLIFY_URL=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --query "Stacks[0].Outputs[?OutputKey=='AmplifyAppUrl'].OutputValue" --output text 2>/dev/null || echo "Not found")
ECR_URI=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --query "Stacks[0].Outputs[?OutputKey=='EcrRepositoryUri'].OutputValue" --output text 2>/dev/null || echo "Not found")

echo "   🔐 Cognito User Pool ID: $USER_POOL_ID"
echo "   🖥️  Backend API URL: https://$BACKEND_URL"
echo "   🌐 Frontend URL: $AMPLIFY_URL"
echo "   🐳 ECR Repository: $ECR_URI"

echo ""
echo "📋 Next steps:"
echo "1. Connect your GitHub repository to Amplify (if not already done)"
echo "2. Push your code to trigger Amplify build"
echo "3. Test the authentication flow"
echo "4. Monitor CloudWatch logs for any issues"
echo ""
echo "🔗 Useful links:"
echo "   AWS Console: https://console.aws.amazon.com/"
echo "   Amplify Console: https://console.aws.amazon.com/amplify/home"
echo "   ECS Console: https://console.aws.amazon.com/ecs/home"
echo "   CloudWatch Logs: https://console.aws.amazon.com/cloudwatch/home#logsV2:log-groups"