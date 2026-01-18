#!/bin/bash

# Deploy Noah Reading Agent Infrastructure
# This script deploys the CDK infrastructure with proper dependency management

set -e

echo "🏗️  Deploying Noah Reading Agent Infrastructure..."

# Configuration
AWS_REGION="ap-northeast-1"
STACK_NAME="NoahInfrastructureStack"

# Check AWS CLI and credentials
echo "🔐 Checking AWS credentials..."
if ! command -v aws &> /dev/null; then
  echo "❌ AWS CLI not found. Please install AWS CLI first."
  exit 1
fi

if ! aws sts get-caller-identity &> /dev/null; then
  echo "❌ AWS credentials not configured or invalid"
  echo "Please run: aws configure"
  exit 1
fi

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo "✅ AWS credentials valid (Account: $ACCOUNT_ID, Region: $AWS_REGION)"

# Navigate to infrastructure directory
cd infrastructure

echo "📦 Installing dependencies..."
npm ci

echo "🔧 Building TypeScript..."
npm run build

echo "🚀 Bootstrapping CDK (if needed)..."
npx cdk bootstrap aws://$ACCOUNT_ID/$AWS_REGION

echo "📋 Checking what will be deployed..."
npx cdk diff

echo "🚀 Deploying infrastructure..."
npx cdk deploy --require-approval never

echo "✅ Infrastructure deployment completed!"

# Get outputs
echo ""
echo "📊 Deployment Outputs:"
aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --query 'Stacks[0].Outputs[*].[OutputKey,OutputValue]' \
  --output table

echo ""
echo "🎉 Infrastructure is ready!"
echo "Next steps:"
echo "1. Build and push your backend Docker image"
echo "2. Configure your frontend environment variables"
echo "3. Test the deployment with: ./scripts/health-monitoring-dashboard.sh"