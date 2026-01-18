#!/bin/bash

# Update Bedrock Marketplace permissions for Noah backend service
# This script adds the required AWS Marketplace permissions to the ECS task role

set -e

echo "🔧 Updating Bedrock Marketplace permissions for Noah backend service..."

# Get the stack name
STACK_NAME="NoahInfrastructureStack"

# Get the ECS task role ARN from CloudFormation
echo "📋 Getting ECS task role ARN..."
TASK_ROLE_ARN=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --query 'Stacks[0].Outputs[?OutputKey==`NoahBackendServiceTaskRoleArn`].OutputValue' \
  --output text 2>/dev/null || echo "")

if [ -z "$TASK_ROLE_ARN" ]; then
  echo "⚠️  Task role ARN not found in outputs, trying to find it via ECS..."
  
  # Get cluster name
  CLUSTER_NAME=$(aws cloudformation describe-stack-resources \
    --stack-name $STACK_NAME \
    --query 'StackResources[?ResourceType==`AWS::ECS::Cluster`].PhysicalResourceId' \
    --output text)
  
  # Get service name
  SERVICE_NAME=$(aws cloudformation describe-stack-resources \
    --stack-name $STACK_NAME \
    --query 'StackResources[?ResourceType==`AWS::ECS::Service`].PhysicalResourceId' \
    --output text)
  
  # Get task definition ARN
  TASK_DEF_ARN=$(aws ecs describe-services \
    --cluster $CLUSTER_NAME \
    --services $SERVICE_NAME \
    --query 'services[0].taskDefinition' \
    --output text)
  
  # Get task role ARN from task definition
  TASK_ROLE_ARN=$(aws ecs describe-task-definition \
    --task-definition $TASK_DEF_ARN \
    --query 'taskDefinition.taskRoleArn' \
    --output text)
fi

if [ -z "$TASK_ROLE_ARN" ] || [ "$TASK_ROLE_ARN" = "None" ]; then
  echo "❌ Could not find ECS task role ARN"
  exit 1
fi

echo "✅ Found task role: $TASK_ROLE_ARN"

# Extract role name from ARN
ROLE_NAME=$(echo $TASK_ROLE_ARN | cut -d'/' -f2)
echo "📝 Role name: $ROLE_NAME"

# Create the marketplace policy document
MARKETPLACE_POLICY='{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "aws-marketplace:ViewSubscriptions",
        "aws-marketplace:Subscribe"
      ],
      "Resource": "*"
    }
  ]
}'

# Policy name
POLICY_NAME="NoahBedrockMarketplacePolicy"

echo "🔐 Creating/updating marketplace policy..."

# Try to create the policy (will fail if it already exists)
POLICY_ARN=$(aws iam create-policy \
  --policy-name $POLICY_NAME \
  --policy-document "$MARKETPLACE_POLICY" \
  --description "AWS Marketplace permissions for Noah Bedrock model access" \
  --query 'Policy.Arn' \
  --output text 2>/dev/null || echo "")

if [ -z "$POLICY_ARN" ]; then
  echo "📋 Policy already exists, getting ARN..."
  ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
  POLICY_ARN="arn:aws:iam::${ACCOUNT_ID}:policy/${POLICY_NAME}"
  
  echo "🔄 Updating existing policy..."
  aws iam create-policy-version \
    --policy-arn $POLICY_ARN \
    --policy-document "$MARKETPLACE_POLICY" \
    --set-as-default
fi

echo "✅ Policy ARN: $POLICY_ARN"

# Attach the policy to the role
echo "🔗 Attaching marketplace policy to task role..."
aws iam attach-role-policy \
  --role-name $ROLE_NAME \
  --policy-arn $POLICY_ARN

echo "✅ Marketplace policy attached successfully!"

# Verify the policy is attached
echo "🔍 Verifying policy attachment..."
ATTACHED_POLICIES=$(aws iam list-attached-role-policies \
  --role-name $ROLE_NAME \
  --query 'AttachedPolicies[?PolicyName==`'$POLICY_NAME'`].PolicyName' \
  --output text)

if [ "$ATTACHED_POLICIES" = "$POLICY_NAME" ]; then
  echo "✅ Policy attachment verified!"
else
  echo "❌ Policy attachment verification failed"
  exit 1
fi

echo ""
echo "🎉 Bedrock Marketplace permissions updated successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Wait 2-3 minutes for permissions to propagate"
echo "2. Restart the ECS service to pick up new permissions:"
echo "   aws ecs update-service --cluster $CLUSTER_NAME --service $SERVICE_NAME --force-new-deployment"
echo "3. Monitor logs to verify the Bedrock access issue is resolved"
echo ""
echo "🔍 To check if the issue is resolved:"
echo "   ./scripts/test-bedrock-permissions.sh"