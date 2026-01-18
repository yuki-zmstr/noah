#!/bin/bash

# Connect to database using AWS Systems Manager Session Manager (no SSH required)
# Usage: ./scripts/connect-via-ssm.sh [action]
# Actions: setup, tunnel, connect

set -e

STACK_NAME="NoahInfrastructureStack"
REGION=${AWS_REGION:-"ap-northeast-1"}
ACTION=${1:-"connect"}

case "$ACTION" in
    "setup")
        echo "🔧 Setting up Systems Manager Session Manager..."
        
        # Check if session manager plugin is installed
        if ! command -v session-manager-plugin &> /dev/null; then
            echo "❌ AWS Session Manager plugin not found"
            echo "📥 Install it from: https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html"
            echo ""
            echo "🍺 On macOS with Homebrew:"
            echo "   brew install --cask session-manager-plugin"
            echo ""
            echo "📦 Or download directly:"
            echo "   curl 'https://s3.amazonaws.com/session-manager-downloads/plugin/latest/mac/sessionmanager-bundle.zip' -o 'sessionmanager-bundle.zip'"
            echo "   unzip sessionmanager-bundle.zip"
            echo "   sudo ./sessionmanager-bundle/install -i /usr/local/sessionmanagerplugin -b /usr/local/bin/session-manager-plugin"
            exit 1
        fi
        
        echo "✅ Session Manager plugin is installed"
        
        # Get instance ID
        OUTPUTS=$(aws cloudformation describe-stacks \
            --stack-name "$STACK_NAME" \
            --region "$REGION" \
            --query 'Stacks[0].Outputs' \
            --output json)
        
        BASTION_INSTANCE_ID=$(echo "$OUTPUTS" | jq -r '.[] | select(.OutputKey=="BastionHostInstanceId") | .OutputValue')
        
        if [ -z "$BASTION_INSTANCE_ID" ]; then
            echo "❌ Bastion instance not found"
            exit 1
        fi
        
        echo "✅ Bastion Instance ID: $BASTION_INSTANCE_ID"
        
        # Test SSM connectivity
        echo "🧪 Testing Systems Manager connectivity..."
        if aws ssm describe-instance-information \
            --filters "Key=InstanceIds,Values=$BASTION_INSTANCE_ID" \
            --region "$REGION" \
            --query 'InstanceInformationList[0].PingStatus' \
            --output text | grep -q "Online"; then
            echo "✅ Instance is online and accessible via Systems Manager"
        else
            echo "❌ Instance is not accessible via Systems Manager"
            echo "💡 The instance may need the SSM agent or proper IAM role"
        fi
        ;;
    
    "tunnel")
        echo "🔗 Creating database tunnel via Systems Manager..."
        
        # Get connection details
        OUTPUTS=$(aws cloudformation describe-stacks \
            --stack-name "$STACK_NAME" \
            --region "$REGION" \
            --query 'Stacks[0].Outputs' \
            --output json)
        
        BASTION_INSTANCE_ID=$(echo "$OUTPUTS" | jq -r '.[] | select(.OutputKey=="BastionHostInstanceId") | .OutputValue')
        DB_ENDPOINT=$(echo "$OUTPUTS" | jq -r '.[] | select(.OutputKey=="DatabaseEndpoint") | .OutputValue')
        
        if [ -z "$BASTION_INSTANCE_ID" ] || [ -z "$DB_ENDPOINT" ]; then
            echo "❌ Could not get connection details"
            exit 1
        fi
        
        echo "🔗 Creating tunnel: localhost:5432 -> $DB_ENDPOINT:5432"
        echo "💡 Keep this terminal open while using DBeaver"
        echo "🛑 Press Ctrl+C to close tunnel"
        echo ""
        
        # Create port forwarding session
        aws ssm start-session \
            --target "$BASTION_INSTANCE_ID" \
            --region "$REGION" \
            --document-name AWS-StartPortForwardingSessionToRemoteHost \
            --parameters "{\"host\":[\"$DB_ENDPOINT\"],\"portNumber\":[\"5432\"],\"localPortNumber\":[\"5432\"]}"
        ;;
    
    "connect")
        echo "🖥️  Connecting to bastion host via Systems Manager..."
        
        # Get instance ID
        OUTPUTS=$(aws cloudformation describe-stacks \
            --stack-name "$STACK_NAME" \
            --region "$REGION" \
            --query 'Stacks[0].Outputs' \
            --output json)
        
        BASTION_INSTANCE_ID=$(echo "$OUTPUTS" | jq -r '.[] | select(.OutputKey=="BastionHostInstanceId") | .OutputValue')
        
        if [ -z "$BASTION_INSTANCE_ID" ]; then
            echo "❌ Bastion instance not found"
            exit 1
        fi
        
        echo "🔗 Connecting to instance: $BASTION_INSTANCE_ID"
        echo "💡 You'll get a shell on the bastion host"
        echo "🐘 From there, you can connect to PostgreSQL directly"
        echo ""
        
        aws ssm start-session \
            --target "$BASTION_INSTANCE_ID" \
            --region "$REGION"
        ;;
    
    *)
        echo "AWS Systems Manager Database Connection"
        echo "======================================"
        echo ""
        echo "This method doesn't require SSH keys or security group modifications!"
        echo ""
        echo "Usage: $0 [action]"
        echo ""
        echo "Actions:"
        echo "  setup   - Install and test Session Manager plugin"
        echo "  tunnel  - Create port forwarding tunnel for DBeaver"
        echo "  connect - Connect to bastion host shell"
        echo ""
        echo "Workflow:"
        echo "1. $0 setup    (one time setup)"
        echo "2. $0 tunnel   (in one terminal, keep running)"
        echo "3. Use DBeaver with localhost:5432"
        echo ""
        echo "Requirements:"
        echo "- AWS CLI configured"
        echo "- Session Manager plugin installed"
        echo "- Bastion host with SSM agent (should be automatic)"
        ;;
esac