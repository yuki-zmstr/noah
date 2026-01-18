#!/bin/bash

# Health Monitoring Dashboard for Noah Reading Agent
# This script provides a comprehensive view of system health

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
STACK_NAME="NoahInfrastructureStack"
AWS_REGION="ap-northeast-1"

echo -e "${BLUE}🔍 Noah Reading Agent Health Monitoring Dashboard${NC}"
echo "=================================================="

# Function to print status with color
print_status() {
  local status=$1
  local message=$2
  case $status in
    "OK")
      echo -e "${GREEN}✅ $message${NC}"
      ;;
    "WARNING")
      echo -e "${YELLOW}⚠️  $message${NC}"
      ;;
    "ERROR")
      echo -e "${RED}❌ $message${NC}"
      ;;
    "INFO")
      echo -e "${BLUE}ℹ️  $message${NC}"
      ;;
  esac
}

# Check AWS CLI and credentials
echo ""
echo "🔐 AWS Configuration Check"
echo "-------------------------"

if ! command -v aws &> /dev/null; then
  print_status "ERROR" "AWS CLI not found"
  exit 1
fi

if ! aws sts get-caller-identity &> /dev/null; then
  print_status "ERROR" "AWS credentials not configured or invalid"
  exit 1
fi

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
print_status "OK" "AWS credentials valid (Account: $ACCOUNT_ID)"

# Check CloudFormation stack
echo ""
echo "🏗️  Infrastructure Check"
echo "------------------------"

STACK_STATUS=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --query 'Stacks[0].StackStatus' --output text 2>/dev/null || echo "NOT_FOUND")

case $STACK_STATUS in
  "CREATE_COMPLETE"|"UPDATE_COMPLETE")
    print_status "OK" "CloudFormation stack is healthy ($STACK_STATUS)"
    ;;
  "CREATE_IN_PROGRESS"|"UPDATE_IN_PROGRESS")
    print_status "WARNING" "CloudFormation stack is updating ($STACK_STATUS)"
    ;;
  "NOT_FOUND")
    print_status "ERROR" "CloudFormation stack not found"
    exit 1
    ;;
  *)
    print_status "ERROR" "CloudFormation stack in bad state ($STACK_STATUS)"
    exit 1
    ;;
esac

# Get ECS resources
echo ""
echo "🐳 ECS Service Check"
echo "-------------------"

ECS_CLUSTER=$(aws cloudformation describe-stack-resources \
  --stack-name $STACK_NAME \
  --query 'StackResources[?ResourceType==`AWS::ECS::Cluster`].PhysicalResourceId' \
  --output text 2>/dev/null || echo "")

if [[ -z "$ECS_CLUSTER" || "$ECS_CLUSTER" == "None" ]]; then
  print_status "ERROR" "ECS cluster not found"
  exit 1
fi

print_status "OK" "ECS cluster found: $ECS_CLUSTER"

ECS_SERVICE=$(aws cloudformation describe-stack-resources \
  --stack-name $STACK_NAME \
  --query 'StackResources[?ResourceType==`AWS::ECS::Service`].PhysicalResourceId' \
  --output text 2>/dev/null || echo "")

if [[ -z "$ECS_SERVICE" || "$ECS_SERVICE" == "None" ]]; then
  print_status "ERROR" "ECS service not found"
  exit 1
fi

print_status "OK" "ECS service found: $ECS_SERVICE"

# Check service health
SERVICE_STATUS=$(aws ecs describe-services --cluster $ECS_CLUSTER --services $ECS_SERVICE --query 'services[0].status' --output text 2>/dev/null || echo "")
RUNNING_COUNT=$(aws ecs describe-services --cluster $ECS_CLUSTER --services $ECS_SERVICE --query 'services[0].runningCount' --output text 2>/dev/null || echo "0")
DESIRED_COUNT=$(aws ecs describe-services --cluster $ECS_CLUSTER --services $ECS_SERVICE --query 'services[0].desiredCount' --output text 2>/dev/null || echo "0")

if [[ "$SERVICE_STATUS" == "ACTIVE" ]]; then
  print_status "OK" "Service is active"
else
  print_status "ERROR" "Service is not active: $SERVICE_STATUS"
fi

if [[ "$RUNNING_COUNT" == "$DESIRED_COUNT" ]]; then
  print_status "OK" "All tasks running ($RUNNING_COUNT/$DESIRED_COUNT)"
else
  print_status "WARNING" "Task count mismatch ($RUNNING_COUNT/$DESIRED_COUNT)"
fi

# Check load balancer
echo ""
echo "⚖️  Load Balancer Check"
echo "----------------------"

TG_ARN=$(aws ecs describe-services --cluster $ECS_CLUSTER --services $ECS_SERVICE --query 'services[0].loadBalancers[0].targetGroupArn' --output text 2>/dev/null || echo "")

if [[ -z "$TG_ARN" || "$TG_ARN" == "None" ]]; then
  print_status "ERROR" "Target group not found"
  exit 1
fi

print_status "OK" "Target group found"

# Check target health
HEALTHY_TARGETS=$(aws elbv2 describe-target-health --target-group-arn $TG_ARN --query 'TargetHealthDescriptions[?TargetHealth.State==`healthy`] | length(@)' --output text 2>/dev/null || echo "0")
TOTAL_TARGETS=$(aws elbv2 describe-target-health --target-group-arn $TG_ARN --query 'TargetHealthDescriptions | length(@)' --output text 2>/dev/null || echo "0")

if [[ "$HEALTHY_TARGETS" == "$TOTAL_TARGETS" && "$HEALTHY_TARGETS" -gt 0 ]]; then
  print_status "OK" "All targets healthy ($HEALTHY_TARGETS/$TOTAL_TARGETS)"
else
  print_status "WARNING" "Some targets unhealthy ($HEALTHY_TARGETS/$TOTAL_TARGETS)"
fi

LB_ARN=$(aws elbv2 describe-target-groups --target-group-arns $TG_ARN --query 'TargetGroups[0].LoadBalancerArns[0]' --output text 2>/dev/null || echo "")
LB_DNS=$(aws elbv2 describe-load-balancers --load-balancer-arns $LB_ARN --query 'LoadBalancers[0].DNSName' --output text 2>/dev/null || echo "")

if [[ -n "$LB_DNS" && "$LB_DNS" != "None" ]]; then
  print_status "OK" "Load balancer DNS: $LB_DNS"
else
  print_status "ERROR" "Load balancer DNS not available"
  exit 1
fi

# Test application health
echo ""
echo "🏥 Application Health Check"
echo "--------------------------"

HEALTH_URL="http://$LB_DNS/health"
print_status "INFO" "Testing: $HEALTH_URL"

if HEALTH_RESPONSE=$(curl -s -f -m 10 "$HEALTH_URL" 2>/dev/null); then
  print_status "OK" "Health endpoint responding"
  
  # Parse health response if it's JSON
  if echo "$HEALTH_RESPONSE" | jq . &>/dev/null; then
    STATUS=$(echo "$HEALTH_RESPONSE" | jq -r '.status // "unknown"')
    UPTIME=$(echo "$HEALTH_RESPONSE" | jq -r '.uptime_seconds // "unknown"')
    
    if [[ "$STATUS" == "healthy" ]]; then
      print_status "OK" "Application status: $STATUS (uptime: ${UPTIME}s)"
    else
      print_status "WARNING" "Application status: $STATUS"
    fi
  else
    print_status "OK" "Health endpoint returned: $HEALTH_RESPONSE"
  fi
else
  print_status "ERROR" "Health endpoint not responding"
fi

# Test API endpoints
echo ""
echo "🔌 API Endpoints Check"
echo "---------------------"

API_BASE="http://$LB_DNS/api"

# Test config endpoint
if curl -s -f -m 5 "$API_BASE/config" &>/dev/null; then
  print_status "OK" "Config endpoint responding"
else
  print_status "WARNING" "Config endpoint not responding"
fi

# Test conversation health
if curl -s -f -m 5 "$API_BASE/v1/conversations/health" &>/dev/null; then
  print_status "OK" "Conversation service responding"
else
  print_status "WARNING" "Conversation service not responding"
fi

# Check database connectivity (via health endpoint)
echo ""
echo "🗄️  Database Check"
echo "-----------------"

if HEALTH_RESPONSE=$(curl -s -f -m 10 "$HEALTH_URL" 2>/dev/null); then
  if echo "$HEALTH_RESPONSE" | jq . &>/dev/null; then
    DB_STATUS=$(echo "$HEALTH_RESPONSE" | jq -r '.services.database // "unknown"')
    
    if [[ "$DB_STATUS" == "healthy" ]]; then
      print_status "OK" "Database connectivity: $DB_STATUS"
    else
      print_status "ERROR" "Database connectivity: $DB_STATUS"
    fi
  fi
fi

# Check CloudWatch metrics (if available)
echo ""
echo "📊 CloudWatch Metrics"
echo "--------------------"

# Check if we have recent metrics
END_TIME=$(date -u +%Y-%m-%dT%H:%M:%S)
START_TIME=$(date -u -d '5 minutes ago' +%Y-%m-%dT%H:%M:%S)

CPU_METRICS=$(aws cloudwatch get-metric-statistics \
  --namespace AWS/ECS \
  --metric-name CPUUtilization \
  --dimensions Name=ServiceName,Value=$ECS_SERVICE Name=ClusterName,Value=$ECS_CLUSTER \
  --start-time $START_TIME \
  --end-time $END_TIME \
  --period 300 \
  --statistics Average \
  --query 'Datapoints | length(@)' --output text 2>/dev/null || echo "0")

if [[ "$CPU_METRICS" -gt 0 ]]; then
  print_status "OK" "CloudWatch metrics available"
else
  print_status "WARNING" "No recent CloudWatch metrics"
fi

# Summary
echo ""
echo "📋 Health Summary"
echo "=================="

# Get overall status from health endpoint
if HEALTH_RESPONSE=$(curl -s -f -m 10 "$HEALTH_URL" 2>/dev/null); then
  if echo "$HEALTH_RESPONSE" | jq . &>/dev/null; then
    OVERALL_STATUS=$(echo "$HEALTH_RESPONSE" | jq -r '.status // "unknown"')
    
    case $OVERALL_STATUS in
      "healthy")
        print_status "OK" "Overall system status: HEALTHY"
        echo ""
        echo -e "${GREEN}🎉 Noah Reading Agent is running smoothly!${NC}"
        echo "Access your application at: http://$LB_DNS"
        ;;
      "degraded")
        print_status "WARNING" "Overall system status: DEGRADED"
        echo ""
        echo -e "${YELLOW}⚠️  System is running but with some issues${NC}"
        ;;
      *)
        print_status "ERROR" "Overall system status: $OVERALL_STATUS"
        echo ""
        echo -e "${RED}❌ System requires attention${NC}"
        ;;
    esac
  fi
else
  print_status "ERROR" "Cannot determine overall system status"
  echo ""
  echo -e "${RED}❌ System health check failed${NC}"
fi

echo ""
echo "For detailed logs, check:"
echo "- CloudWatch Logs: /aws/ecs/noah-backend"
echo "- ECS Console: https://console.aws.amazon.com/ecs/home?region=$AWS_REGION#/clusters/$ECS_CLUSTER/services"
echo "- Load Balancer: https://console.aws.amazon.com/ec2/v2/home?region=$AWS_REGION#LoadBalancers:"