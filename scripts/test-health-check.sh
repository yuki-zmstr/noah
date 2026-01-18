#!/bin/bash

# Test health check for Noah Reading Agent
# This script tests the current deployment health check

set -e

echo "🔍 Testing Noah Reading Agent Health Check..."

# Configuration
STACK_NAME="NoahInfrastructureStack"
AWS_REGION="ap-northeast-1"

echo "📋 Getting ECS resources from CloudFormation..."

# Get cluster name from CloudFormation stack
ECS_CLUSTER=$(aws cloudformation describe-stack-resources \
  --stack-name $STACK_NAME \
  --query 'StackResources[?ResourceType==`AWS::ECS::Cluster`].PhysicalResourceId' \
  --output text 2>/dev/null || echo "")

if [[ -z "$ECS_CLUSTER" || "$ECS_CLUSTER" == "None" ]]; then
  echo "❌ ECS cluster not found in CloudFormation stack"
  exit 1
fi

echo "✅ Found ECS cluster: $ECS_CLUSTER"

# Get service name from CloudFormation stack
ECS_SERVICE=$(aws cloudformation describe-stack-resources \
  --stack-name $STACK_NAME \
  --query 'StackResources[?ResourceType==`AWS::ECS::Service`].PhysicalResourceId' \
  --output text 2>/dev/null || echo "")

if [[ -z "$ECS_SERVICE" || "$ECS_SERVICE" == "None" ]]; then
  echo "❌ ECS service not found in CloudFormation stack"
  exit 1
fi

echo "✅ Found ECS service: $ECS_SERVICE"

# Check service status
echo "📊 Checking service status..."
SERVICE_STATUS=$(aws ecs describe-services --cluster $ECS_CLUSTER --services $ECS_SERVICE --query 'services[0].status' --output text 2>/dev/null || echo "")
RUNNING_COUNT=$(aws ecs describe-services --cluster $ECS_CLUSTER --services $ECS_SERVICE --query 'services[0].runningCount' --output text 2>/dev/null || echo "0")
DESIRED_COUNT=$(aws ecs describe-services --cluster $ECS_CLUSTER --services $ECS_SERVICE --query 'services[0].desiredCount' --output text 2>/dev/null || echo "0")

echo "Service Status: $SERVICE_STATUS"
echo "Running Tasks: $RUNNING_COUNT"
echo "Desired Tasks: $DESIRED_COUNT"

if [[ "$SERVICE_STATUS" != "ACTIVE" ]]; then
  echo "⚠️ Service is not active: $SERVICE_STATUS"
fi

if [[ "$RUNNING_COUNT" != "$DESIRED_COUNT" ]]; then
  echo "⚠️ Running count ($RUNNING_COUNT) doesn't match desired count ($DESIRED_COUNT)"
fi

# Get load balancer DNS
echo "🌐 Getting load balancer information..."
TG_ARN=$(aws ecs describe-services --cluster $ECS_CLUSTER --services $ECS_SERVICE --query 'services[0].loadBalancers[0].targetGroupArn' --output text 2>/dev/null || echo "")

if [[ -z "$TG_ARN" || "$TG_ARN" == "None" ]]; then
  echo "❌ Load balancer target group not found"
  exit 1
fi

echo "✅ Found target group: $TG_ARN"

LB_ARN=$(aws elbv2 describe-target-groups --target-group-arns $TG_ARN --query 'TargetGroups[0].LoadBalancerArns[0]' --output text 2>/dev/null || echo "")

if [[ -z "$LB_ARN" || "$LB_ARN" == "None" ]]; then
  echo "❌ Load balancer not found"
  exit 1
fi

echo "✅ Found load balancer: $LB_ARN"

LB_DNS=$(aws elbv2 describe-load-balancers --load-balancer-arns $LB_ARN --query 'LoadBalancers[0].DNSName' --output text 2>/dev/null || echo "")

if [[ -z "$LB_DNS" || "$LB_DNS" == "None" ]]; then
  echo "❌ Load balancer DNS not available"
  exit 1
fi

echo "✅ Found load balancer DNS: $LB_DNS"

# Test health endpoint
echo "🏥 Testing health endpoint..."
HEALTH_URL="http://$LB_DNS/health"
echo "Health URL: $HEALTH_URL"

if curl -f -m 10 "$HEALTH_URL"; then
  echo ""
  echo "✅ Health check passed!"
else
  echo ""
  echo "❌ Health check failed!"
  
  # Try to get more information
  echo "🔍 Debugging information:"
  echo "Trying to get basic response..."
  curl -v "$HEALTH_URL" || echo "No response"
  
  # Check target health
  echo "🎯 Checking target group health..."
  aws elbv2 describe-target-health --target-group-arn $TG_ARN
  
  exit 1
fi

echo ""
echo "🎉 All health checks passed!"
echo "Your Noah Reading Agent is healthy and accessible at: $HEALTH_URL"