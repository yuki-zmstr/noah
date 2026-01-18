#!/bin/bash

# Test Bedrock permissions for Noah Reading Agent
# This script verifies that the ECS task can access Bedrock models

set -e

echo "🔍 Testing Bedrock permissions..."

# Test if we can list foundation models
echo ""
echo "🧪 Testing Bedrock access..."
if aws bedrock list-foundation-models --by-provider anthropic --query 'modelSummaries[*].modelId' --output table 2>/dev/null; then
    echo "✅ Bedrock access test passed - Anthropic models available"
else
    echo "❌ Bedrock access test failed"
    echo "This could mean:"
    echo "  1. Bedrock permissions are not configured"
    echo "  2. Anthropic models are not enabled in this region"
    echo "  3. You need to request access to Anthropic models in Bedrock console"
fi

# Check if the specific model we're using is available
echo ""
echo "🔍 Checking for Claude 3.5 Sonnet model..."
MODEL_ID="anthropic.claude-3-5-sonnet-20240620-v1:0"
if aws bedrock get-foundation-model --model-identifier "$MODEL_ID" >/dev/null 2>&1; then
    echo "✅ Claude 3.5 Sonnet v1 model is available"
else
    echo "❌ Claude 3.5 Sonnet v1 model is not available"
    echo "Available Anthropic models:"
    aws bedrock list-foundation-models --by-provider anthropic --query 'modelSummaries[*].{ModelId:modelId,Name:modelName}' --output table 2>/dev/null || echo "No Anthropic models found"
fi

# Check recent logs for Bedrock errors
echo ""
echo "📊 Checking recent logs for Bedrock/Strands errors..."
LOG_GROUP="/aws/ecs/noah-backend"
if aws logs describe-log-groups --log-group-name-prefix "$LOG_GROUP" >/dev/null 2>&1; then
    echo "📋 Found log group: $LOG_GROUP"
    
    # Get the most recent log stream
    RECENT_STREAM=$(aws logs describe-log-streams --log-group-name "$LOG_GROUP" --order-by LastEventTime --descending --max-items 1 --query 'logStreams[0].logStreamName' --output text)
    
    if [ "$RECENT_STREAM" != "None" ] && [ ! -z "$RECENT_STREAM" ]; then
        echo "📋 Checking recent log stream: $RECENT_STREAM"
        
        # Check for Bedrock/Strands errors in the last 10 minutes
        START_TIME=$(date -d '10 minutes ago' +%s)000
        
        echo "🔍 Checking for Bedrock ValidationException errors..."
        if aws logs filter-log-events --log-group-name "$LOG_GROUP" --log-stream-names "$RECENT_STREAM" --start-time "$START_TIME" --filter-pattern "ValidationException" --query 'events[].message' --output text | grep -i "model identifier"; then
            echo "❌ Found Bedrock model identifier errors in recent logs"
        else
            echo "✅ No Bedrock model identifier errors found in recent logs"
        fi
        
        echo "🔍 Checking for AWS Marketplace permission errors..."
        if aws logs filter-log-events --log-group-name "$LOG_GROUP" --log-stream-names "$RECENT_STREAM" --start-time "$START_TIME" --filter-pattern "AccessDeniedException" --query 'events[].message' --output text | grep -i "marketplace"; then
            echo "❌ Found AWS Marketplace permission errors in recent logs"
            echo "💡 Run: ./scripts/update-bedrock-marketplace-permissions.sh"
        else
            echo "✅ No AWS Marketplace permission errors found in recent logs"
        fi
        
        echo "🔍 Checking for Strands agent errors..."
        if aws logs filter-log-events --log-group-name "$LOG_GROUP" --log-stream-names "$RECENT_STREAM" --start-time "$START_TIME" --filter-pattern "strands_agent_service" --query 'events[].message' --output text | grep -i error; then
            echo "❌ Found Strands agent errors in recent logs"
        else
            echo "✅ No Strands agent errors found in recent logs"
        fi
    else
        echo "📋 No recent log streams found"
    fi
else
    echo "📋 Log group not found: $LOG_GROUP"
fi

echo ""
echo "🏁 Bedrock permissions test completed"
echo ""
echo "💡 If you see permission or model access errors:"
echo "1. For marketplace permissions: ./scripts/update-bedrock-marketplace-permissions.sh"
echo "2. For general Bedrock permissions: ./scripts/update-cloudwatch-permissions.sh"
echo "3. Enable Anthropic models in AWS Console > Bedrock > Model Access"
echo "4. Wait for the ECS service to restart (2-3 minutes)"
echo "5. Run this test again"
echo ""
echo "🌐 To enable Anthropic models:"
echo "https://console.aws.amazon.com/bedrock/home#/modelaccess"