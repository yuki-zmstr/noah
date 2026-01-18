#!/bin/bash

# Update CloudWatch and Bedrock permissions for Noah Reading Agent
# This script deploys the updated infrastructure with CloudWatch and Bedrock permissions

set -e

echo "🚀 Updating Noah Infrastructure with CloudWatch and Bedrock permissions..."

# Change to infrastructure directory
cd infrastructure

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing CDK dependencies..."
    npm install
fi

# Bootstrap CDK if needed (only run once per account/region)
echo "🔧 Checking CDK bootstrap status..."
npx cdk bootstrap --require-approval never || echo "CDK already bootstrapped"

# Deploy the infrastructure
echo "🏗️  Deploying infrastructure updates..."
npx cdk deploy --require-approval never

echo "✅ Infrastructure update completed!"
echo ""
echo "📋 Next steps:"
echo "1. The ECS service will automatically restart with new permissions"
echo "2. CloudWatch metrics should start working within a few minutes"
echo "3. Strands agents will be able to access Bedrock models"
echo "4. Check the logs to verify both errors are resolved"
echo ""
echo "🔍 To check deployment status:"
echo "aws ecs describe-services --cluster NoahInfrastructureStack-NoahCluster* --services NoahInfrastructureStack-NoahBackendService*"
echo ""
echo "🧪 To test permissions:"
echo "./scripts/test-cloudwatch-permissions.sh"