#!/bin/bash

# Setup script for AWS Amplify deployment
# This script helps configure Amplify hosting for the Noah Reading Agent frontend

set -e

echo "🚀 Setting up AWS Amplify deployment..."

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI is not installed. Please install it first."
    exit 1
fi

# Get the stack name (default to NoahInfrastructureStack)
STACK_NAME=${1:-NoahInfrastructureStack}

echo "📋 Getting Amplify configuration from CDK stack: $STACK_NAME"

# Get CDK outputs
AMPLIFY_APP_ID=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --query "Stacks[0].Outputs[?OutputKey=='AmplifyAppId'].OutputValue" --output text 2>/dev/null || echo "")
AMPLIFY_APP_URL=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --query "Stacks[0].Outputs[?OutputKey=='AmplifyAppUrl'].OutputValue" --output text 2>/dev/null || echo "")
AMPLIFY_DEV_URL=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --query "Stacks[0].Outputs[?OutputKey=='AmplifyDevUrl'].OutputValue" --output text 2>/dev/null || echo "")

if [ -z "$AMPLIFY_APP_ID" ]; then
    echo "⚠️  Amplify App not found in CDK stack. Please deploy the infrastructure first."
    echo ""
    echo "To deploy the infrastructure:"
    echo "cd infrastructure"
    echo "npm install"
    echo "cdk deploy"
    exit 1
fi

echo "✅ Found Amplify configuration:"
echo "   App ID: $AMPLIFY_APP_ID"
echo "   Main URL: $AMPLIFY_APP_URL"
echo "   Dev URL: $AMPLIFY_DEV_URL"

# Update Cognito callback URLs to include Amplify URLs
echo "🔧 Updating Cognito callback URLs..."

USER_POOL_ID=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --query "Stacks[0].Outputs[?OutputKey=='UserPoolId'].OutputValue" --output text)
CLIENT_ID=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --query "Stacks[0].Outputs[?OutputKey=='UserPoolClientId'].OutputValue" --output text)

if [ -n "$USER_POOL_ID" ] && [ -n "$CLIENT_ID" ]; then
    # Extract domain from Amplify URLs
    MAIN_DOMAIN=$(echo $AMPLIFY_APP_URL | sed 's|https://||')
    DEV_DOMAIN=$(echo $AMPLIFY_DEV_URL | sed 's|https://||')
    
    aws cognito-idp update-user-pool-client \
        --user-pool-id $USER_POOL_ID \
        --client-id $CLIENT_ID \
        --callback-urls $AMPLIFY_APP_URL,$AMPLIFY_DEV_URL,http://localhost:5173,https://localhost:5173 \
        --logout-urls $AMPLIFY_APP_URL,$AMPLIFY_DEV_URL,http://localhost:5173,https://localhost:5173 \
        --supported-identity-providers COGNITO \
        --allowed-o-auth-flows authorization_code_grant \
        --allowed-o-auth-scopes email,openid,profile \
        --allowed-o-auth-flows-user-pool-client
    
    echo "✅ Updated Cognito callback URLs"
else
    echo "⚠️  Could not find Cognito configuration. Skipping callback URL update."
fi

echo ""
echo "📋 Next steps:"
echo "1. Connect your GitHub repository to Amplify:"
echo "   - Go to AWS Amplify Console: https://console.aws.amazon.com/amplify/home"
echo "   - Find your app: noah-reading-agent"
echo "   - Connect your GitHub repository"
echo "   - Configure build settings (amplify.yml is already created)"
echo ""
echo "2. Set up GitHub token in AWS Secrets Manager:"
echo "   - Create a GitHub personal access token with repo permissions"
echo "   - Store it in Secrets Manager with name 'github-token'"
echo ""
echo "3. Trigger a deployment:"
echo "   - Push to main or develop branch"
echo "   - Or manually trigger build in Amplify Console"
echo ""
echo "🌐 Your app will be available at:"
echo "   Production: $AMPLIFY_APP_URL"
echo "   Development: $AMPLIFY_DEV_URL"