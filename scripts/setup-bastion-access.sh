#!/bin/bash

# Script to set up bastion host access for database connections
# Usage: ./scripts/setup-bastion-access.sh [stack-name]

set -e

STACK_NAME=${1:-"NoahInfrastructureStack"}
REGION=${AWS_REGION:-"ap-northeast-1"}
KEY_NAME="noah-bastion-key"
KEY_PATH="$HOME/.ssh/${KEY_NAME}.pem"

echo "🔧 Setting up bastion host access for stack: $STACK_NAME"
echo "📍 Region: $REGION"
echo ""

# Check if key pair already exists
if aws ec2 describe-key-pairs --key-names "$KEY_NAME" --region "$REGION" >/dev/null 2>&1; then
    echo "✅ Key pair '$KEY_NAME' already exists"
else
    echo "🔑 Creating new key pair: $KEY_NAME"
    aws ec2 create-key-pair \
        --key-name "$KEY_NAME" \
        --region "$REGION" \
        --query 'KeyMaterial' \
        --output text > "$KEY_PATH"
    
    chmod 600 "$KEY_PATH"
    echo "✅ Key saved to: $KEY_PATH"
fi

# Get bastion host details
echo "📋 Getting bastion host information..."
OUTPUTS=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$REGION" \
    --query 'Stacks[0].Outputs' \
    --output json 2>/dev/null || echo "[]")

if [ "$OUTPUTS" = "[]" ]; then
    echo "❌ Stack not found. Make sure to deploy the infrastructure first:"
    echo "   cd infrastructure && npm run deploy"
    exit 1
fi

BASTION_IP=$(echo "$OUTPUTS" | jq -r '.[] | select(.OutputKey=="BastionHostPublicIP") | .OutputValue' 2>/dev/null || echo "")
BASTION_INSTANCE_ID=$(echo "$OUTPUTS" | jq -r '.[] | select(.OutputKey=="BastionHostInstanceId") | .OutputValue' 2>/dev/null || echo "")
DB_ENDPOINT=$(echo "$OUTPUTS" | jq -r '.[] | select(.OutputKey=="DatabaseEndpoint") | .OutputValue' 2>/dev/null || echo "")

if [ -z "$BASTION_IP" ]; then
    echo "❌ Bastion host not found. Deploy the updated infrastructure first:"
    echo "   cd infrastructure && npm run deploy"
    exit 1
fi

echo "✅ Bastion Host IP: $BASTION_IP"
echo "✅ Instance ID: $BASTION_INSTANCE_ID"
echo "✅ Database Endpoint: $DB_ENDPOINT"

# Update bastion host to use our key pair
echo "🔧 Updating bastion host key pair..."
aws ec2 modify-instance-attribute \
    --instance-id "$BASTION_INSTANCE_ID" \
    --attribute keyName \
    --value "$KEY_NAME" \
    --region "$REGION" 2>/dev/null || echo "⚠️  Could not update key pair (instance may need restart)"

# Test SSH connection
echo "🧪 Testing SSH connection..."
if ssh -i "$KEY_PATH" -o ConnectTimeout=10 -o StrictHostKeyChecking=no ec2-user@"$BASTION_IP" "echo 'SSH connection successful'" 2>/dev/null; then
    echo "✅ SSH connection test passed"
else
    echo "⚠️  SSH connection test failed. The instance may still be starting up."
    echo "   Try again in a few minutes."
fi

echo ""
echo "🎯 Connection Commands:"
echo "======================"
echo ""
echo "1. Create SSH tunnel for database access:"
echo "   ssh -i $KEY_PATH -L 5432:$DB_ENDPOINT:5432 ec2-user@$BASTION_IP"
echo ""
echo "2. In another terminal, get database credentials:"
echo "   ./scripts/get-db-connection.sh"
echo ""
echo "3. In DBeaver, create connection with:"
echo "   Host: localhost"
echo "   Port: 5432"
echo "   Database: noah"
echo "   (Use credentials from step 2)"
echo ""
echo "4. Keep the SSH tunnel running while using DBeaver"
echo ""
echo "💡 Pro tip: Add this alias to your ~/.bashrc or ~/.zshrc:"
echo "   alias noah-tunnel='ssh -i $KEY_PATH -L 5432:$DB_ENDPOINT:5432 ec2-user@$BASTION_IP'"