#!/bin/bash

# Test CloudWatch permissions for Noah Reading Agent
# This script verifies that the ECS task can send metrics to CloudWatch

set -e

echo "🔍 Testing CloudWatch permissions..."

# Get the ECS cluster and service names
CLUSTER_NAME=$(aws ecs list-clusters --query 'clusterArns[?contains(@, `NoahCluster`)]' --output text | head -1 | cut -d'/' -f2)
SERVICE_NAME=$(aws ecs list-services --cluster "$CLUSTER_NAME" --query 'serviceArns[?contains(@, `NoahBackendService`)]' --output text | head -1 | cut -d'/' -f3)

if [ -z "$CLUSTER_NAME" ] || [ -z "$SERVICE_NAME" ]; then
    echo "❌ Could not find Noah ECS cluster or service"
    echo "Make sure the infrastructure is deployed"
    exit 1
fi

echo "📋 Found cluster: $CLUSTER_NAME"
echo "📋 Found service: $SERVICE_NAME"

# Get the task definition ARN
TASK_DEF_ARN=$(aws ecs describe-services --cluster "$CLUSTER_NAME" --services "$SERVICE_NAME" --query 'services[0].taskDefinition' --output text)
echo "📋 Task definition: $TASK_DEF_ARN"

# Get the task role ARN
TASK_ROLE_ARN=$(aws ecs describe-task-definition --task-definition "$TASK_DEF_ARN" --query 'taskDefinition.taskRoleArn' --output text)
echo "📋 Task role: $TASK_ROLE_ARN"

# Check if the role has CloudWatch permissions
echo ""
echo "🔐 Checking CloudWatch permissions..."

# Get attached policies
ATTACHED_POLICIES=$(aws iam list-attached-role-policies --role-name $(echo $TASK_ROLE_ARN | cut -d'/' -f2) --query 'AttachedPolicies[].PolicyArn' --output text)
echo "📋 Attached policies:"
for policy in $ATTACHED_POLICIES; do
    echo "  - $policy"
done

# Check inline policies
INLINE_POLICIES=$(aws iam list-role-policies --role-name $(echo $TASK_ROLE_ARN | cut -d'/' -f2) --query 'PolicyNames' --output text)
if [ ! -z "$INLINE_POLICIES" ]; then
    echo "📋 Inline policies:"
    for policy in $INLINE_POLICIES; do
        echo "  - $policy"
    done
fi

# Test CloudWatch access by checking if we can list metrics
echo ""
echo "🧪 Testing CloudWatch access..."
if aws cloudwatch list-metrics --namespace "Noah/ReadingAgent" --max-records 1 >/dev/null 2>&1; then
    echo "✅ CloudWatch access test passed"
else
    echo "❌ CloudWatch access test failed"
    echo "This might be expected if no metrics have been sent yet"
fi

# Check recent logs for CloudWatch errors
echo ""
echo "📊 Checking recent logs for CloudWatch errors..."
LOG_GROUP="/aws/ecs/noah-backend"
if aws logs describe-log-groups --log-group-name-prefix "$LOG_GROUP" >/dev/null 2>&1; then
    echo "📋 Found log group: $LOG_GROUP"
    
    # Get the most recent log stream
    RECENT_STREAM=$(aws logs describe-log-streams --log-group-name "$LOG_GROUP" --order-by LastEventTime --descending --max-items 1 --query 'logStreams[0].logStreamName' --output text)
    
    if [ "$RECENT_STREAM" != "None" ] && [ ! -z "$RECENT_STREAM" ]; then
        echo "📋 Checking recent log stream: $RECENT_STREAM"
        
        # Check for CloudWatch errors in the last 10 minutes
        START_TIME=$(date -d '10 minutes ago' +%s)000
        
        if aws logs filter-log-events --log-group-name "$LOG_GROUP" --log-stream-names "$RECENT_STREAM" --start-time "$START_TIME" --filter-pattern "CloudWatch" --query 'events[].message' --output text | grep -i error; then
            echo "❌ Found CloudWatch errors in recent logs"
        else
            echo "✅ No CloudWatch errors found in recent logs"
        fi
    else
        echo "📋 No recent log streams found"
    fi
else
    echo "📋 Log group not found: $LOG_GROUP"
fi

echo ""
echo "🏁 CloudWatch permissions test completed"
echo ""
echo "💡 If you see permission errors:"
echo "1. Run: ./scripts/update-cloudwatch-permissions.sh"
echo "2. Wait for the ECS service to restart (2-3 minutes)"
echo "3. Run this test again"