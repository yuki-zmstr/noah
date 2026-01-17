#!/bin/bash

# Test production deployment of Noah Reading Agent
# This script validates that all components are working correctly in production

set -e

echo "🧪 Testing Noah Reading Agent production deployment..."

# Get configuration
STACK_NAME=${1:-NoahInfrastructureStack}
BACKEND_URL=""
FRONTEND_URL=""
AMPLIFY_URL=""

# Get URLs from CDK outputs
echo "📋 Getting deployment URLs..."
BACKEND_URL=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --query "Stacks[0].Outputs[?OutputKey=='BackendUrl'].OutputValue" --output text 2>/dev/null || echo "")
FRONTEND_URL=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --query "Stacks[0].Outputs[?OutputKey=='FrontendUrl'].OutputValue" --output text 2>/dev/null || echo "")
AMPLIFY_URL=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --query "Stacks[0].Outputs[?OutputKey=='AmplifyAppUrl'].OutputValue" --output text 2>/dev/null || echo "")

if [ -z "$BACKEND_URL" ]; then
    echo "❌ Could not find backend URL. Please ensure infrastructure is deployed."
    exit 1
fi

echo "🌐 Testing URLs:"
echo "   Backend: https://$BACKEND_URL"
if [ -n "$FRONTEND_URL" ]; then
    echo "   CloudFront: https://$FRONTEND_URL"
fi
if [ -n "$AMPLIFY_URL" ]; then
    echo "   Amplify: $AMPLIFY_URL"
fi

# Test 1: Backend Health Check
echo ""
echo "🔍 Test 1: Backend Health Check"
HEALTH_RESPONSE=$(curl -s -w "%{http_code}" -o /tmp/health_response.json "https://$BACKEND_URL/health" || echo "000")
HEALTH_CODE="${HEALTH_RESPONSE: -3}"

if [ "$HEALTH_CODE" = "200" ]; then
    echo "✅ Backend health check passed"
    cat /tmp/health_response.json | jq '.' 2>/dev/null || cat /tmp/health_response.json
else
    echo "❌ Backend health check failed (HTTP $HEALTH_CODE)"
    cat /tmp/health_response.json 2>/dev/null || echo "No response body"
fi

# Test 2: API Configuration
echo ""
echo "🔍 Test 2: API Configuration"
CONFIG_RESPONSE=$(curl -s -w "%{http_code}" -o /tmp/config_response.json "https://$BACKEND_URL/api/config" || echo "000")
CONFIG_CODE="${CONFIG_RESPONSE: -3}"

if [ "$CONFIG_CODE" = "200" ]; then
    echo "✅ API configuration endpoint passed"
    cat /tmp/config_response.json | jq '.' 2>/dev/null || cat /tmp/config_response.json
else
    echo "❌ API configuration endpoint failed (HTTP $CONFIG_CODE)"
    cat /tmp/config_response.json 2>/dev/null || echo "No response body"
fi

# Test 3: Conversation Health Check
echo ""
echo "🔍 Test 3: Conversation Service Health Check"
CONV_HEALTH_RESPONSE=$(curl -s -w "%{http_code}" -o /tmp/conv_health_response.json "https://$BACKEND_URL/api/v1/conversations/health" || echo "000")
CONV_HEALTH_CODE="${CONV_HEALTH_RESPONSE: -3}"

if [ "$CONV_HEALTH_CODE" = "200" ]; then
    echo "✅ Conversation service health check passed"
    cat /tmp/conv_health_response.json | jq '.' 2>/dev/null || cat /tmp/conv_health_response.json
else
    echo "❌ Conversation service health check failed (HTTP $CONV_HEALTH_CODE)"
    cat /tmp/conv_health_response.json 2>/dev/null || echo "No response body"
fi

# Test 4: Test Message Functionality
echo ""
echo "🔍 Test 4: Test Message Functionality"
TEST_MESSAGE='{"content": "Hello Noah, this is a test message", "user_id": "test-user-production"}'
MESSAGE_RESPONSE=$(curl -s -w "%{http_code}" -o /tmp/message_response.json \
    -H "Content-Type: application/json" \
    -d "$TEST_MESSAGE" \
    "https://$BACKEND_URL/api/v1/conversations/test-message" || echo "000")
MESSAGE_CODE="${MESSAGE_RESPONSE: -3}"

if [ "$MESSAGE_CODE" = "200" ]; then
    echo "✅ Test message functionality passed"
    cat /tmp/message_response.json | jq '.' 2>/dev/null || cat /tmp/message_response.json
else
    echo "❌ Test message functionality failed (HTTP $MESSAGE_CODE)"
    cat /tmp/message_response.json 2>/dev/null || echo "No response body"
fi

# Test 5: Database Connection (via message storage)
echo ""
echo "🔍 Test 5: Database Connection Test"
DB_TEST_MESSAGE='{"content": "test database connection", "user_id": "db-test-user"}'
DB_RESPONSE=$(curl -s -w "%{http_code}" -o /tmp/db_response.json \
    -H "Content-Type: application/json" \
    -d "$DB_TEST_MESSAGE" \
    "https://$BACKEND_URL/api/v1/conversations/test-message" || echo "000")
DB_CODE="${DB_RESPONSE: -3}"

if [ "$DB_CODE" = "200" ]; then
    echo "✅ Database connection test passed"
    cat /tmp/db_response.json | jq '.session_id' 2>/dev/null || echo "Session created successfully"
else
    echo "❌ Database connection test failed (HTTP $DB_CODE)"
    cat /tmp/db_response.json 2>/dev/null || echo "No response body"
fi

# Test 6: Frontend Accessibility (if URLs available)
if [ -n "$FRONTEND_URL" ]; then
    echo ""
    echo "🔍 Test 6: Frontend Accessibility (CloudFront)"
    FRONTEND_RESPONSE=$(curl -s -w "%{http_code}" -o /tmp/frontend_response.html "https://$FRONTEND_URL" || echo "000")
    FRONTEND_CODE="${FRONTEND_RESPONSE: -3}"
    
    if [ "$FRONTEND_CODE" = "200" ]; then
        echo "✅ Frontend (CloudFront) accessibility passed"
        if grep -q "Noah" /tmp/frontend_response.html; then
            echo "   Frontend contains expected content"
        fi
    else
        echo "❌ Frontend (CloudFront) accessibility failed (HTTP $FRONTEND_CODE)"
    fi
fi

if [ -n "$AMPLIFY_URL" ]; then
    echo ""
    echo "🔍 Test 7: Frontend Accessibility (Amplify)"
    AMPLIFY_RESPONSE=$(curl -s -w "%{http_code}" -o /tmp/amplify_response.html "$AMPLIFY_URL" || echo "000")
    AMPLIFY_CODE="${AMPLIFY_RESPONSE: -3}"
    
    if [ "$AMPLIFY_CODE" = "200" ]; then
        echo "✅ Frontend (Amplify) accessibility passed"
        if grep -q "Noah" /tmp/amplify_response.html; then
            echo "   Frontend contains expected content"
        fi
    else
        echo "❌ Frontend (Amplify) accessibility failed (HTTP $AMPLIFY_CODE)"
    fi
fi

# Cleanup temporary files
rm -f /tmp/health_response.json /tmp/config_response.json /tmp/conv_health_response.json
rm -f /tmp/message_response.json /tmp/db_response.json /tmp/frontend_response.html /tmp/amplify_response.html

echo ""
echo "🎯 Production Test Summary:"
echo "   Backend Health: $([ "$HEALTH_CODE" = "200" ] && echo "✅ PASS" || echo "❌ FAIL")"
echo "   API Config: $([ "$CONFIG_CODE" = "200" ] && echo "✅ PASS" || echo "❌ FAIL")"
echo "   Conversation Service: $([ "$CONV_HEALTH_CODE" = "200" ] && echo "✅ PASS" || echo "❌ FAIL")"
echo "   Message Functionality: $([ "$MESSAGE_CODE" = "200" ] && echo "✅ PASS" || echo "❌ FAIL")"
echo "   Database Connection: $([ "$DB_CODE" = "200" ] && echo "✅ PASS" || echo "❌ FAIL")"

if [ -n "$FRONTEND_URL" ]; then
    echo "   Frontend (CloudFront): $([ "$FRONTEND_CODE" = "200" ] && echo "✅ PASS" || echo "❌ FAIL")"
fi

if [ -n "$AMPLIFY_URL" ]; then
    echo "   Frontend (Amplify): $([ "$AMPLIFY_CODE" = "200" ] && echo "✅ PASS" || echo "❌ FAIL")"
fi

echo ""
if [ "$HEALTH_CODE" = "200" ] && [ "$MESSAGE_CODE" = "200" ] && [ "$DB_CODE" = "200" ]; then
    echo "🎉 Production deployment test completed successfully!"
    echo "Your Noah Reading Agent is ready for use."
else
    echo "⚠️  Some tests failed. Please check the logs and fix any issues."
    exit 1
fi