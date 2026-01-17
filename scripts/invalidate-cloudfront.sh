#!/bin/bash

# Invalidate CloudFront cache for Noah Reading Agent
# This script invalidates the CloudFront distribution cache to ensure users get the latest content

set -e

echo "🔄 Invalidating CloudFront cache..."

# Get the stack name (default to NoahInfrastructureStack)
STACK_NAME=${1:-NoahInfrastructureStack}

# Get CloudFront distribution ID from CDK outputs
DISTRIBUTION_ID=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --query "Stacks[0].Outputs[?contains(OutputKey, 'Distribution')].OutputValue" --output text 2>/dev/null || echo "")

if [ -z "$DISTRIBUTION_ID" ]; then
    echo "❌ Could not find CloudFront distribution ID in stack outputs."
    echo "Please check your stack name or ensure the infrastructure is deployed."
    exit 1
fi

echo "📋 Configuration:"
echo "   Stack Name: $STACK_NAME"
echo "   Distribution ID: $DISTRIBUTION_ID"

# Create invalidation
echo "🚀 Creating invalidation..."
INVALIDATION_ID=$(aws cloudfront create-invalidation \
    --distribution-id $DISTRIBUTION_ID \
    --paths "/*" \
    --query 'Invalidation.Id' \
    --output text)

echo "✅ Invalidation created with ID: $INVALIDATION_ID"

# Wait for invalidation to complete (optional)
read -p "Do you want to wait for invalidation to complete? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "⏳ Waiting for invalidation to complete..."
    aws cloudfront wait invalidation-completed \
        --distribution-id $DISTRIBUTION_ID \
        --id $INVALIDATION_ID
    echo "✅ Invalidation completed!"
else
    echo "📋 You can check the invalidation status with:"
    echo "aws cloudfront get-invalidation --distribution-id $DISTRIBUTION_ID --id $INVALIDATION_ID"
fi

echo ""
echo "🌐 Your CloudFront distribution cache has been invalidated."
echo "Changes should be visible globally within 5-15 minutes."