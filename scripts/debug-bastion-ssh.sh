#!/bin/bash

# Debug script for bastion host SSH connectivity issues
# Usage: ./scripts/debug-bastion-ssh.sh [stack-name]

set -e

STACK_NAME=${1:-"NoahInfrastructureStack"}
REGION=${AWS_REGION:-"ap-northeast-1"}
KEY_NAME="noah-bastion-key"
KEY_PATH="$HOME/.ssh/${KEY_NAME}.pem"

echo "🔍 Debugging bastion host SSH connectivity"
echo "=========================================="
echo ""

# Check if stack exists and get outputs
echo "1️⃣ Checking CloudFormation stack..."
OUTPUTS=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$REGION" \
    --query 'Stacks[0].Outputs' \
    --output json 2>/dev/null || echo "[]")

if [ "$OUTPUTS" = "[]" ]; then
    echo "❌ Stack '$STACK_NAME' not found or no outputs"
    echo "💡 Available stacks:"
    aws cloudformation list-stacks --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE --query 'StackSummaries[].StackName' --output table
    exit 1
fi

BASTION_IP=$(echo "$OUTPUTS" | jq -r '.[] | select(.OutputKey=="BastionHostPublicIP") | .OutputValue' 2>/dev/null || echo "")
BASTION_INSTANCE_ID=$(echo "$OUTPUTS" | jq -r '.[] | select(.OutputKey=="BastionHostInstanceId") | .OutputValue' 2>/dev/null || echo "")

if [ -z "$BASTION_IP" ] || [ -z "$BASTION_INSTANCE_ID" ]; then
    echo "❌ Bastion host outputs not found in stack"
    echo "📋 Available outputs:"
    echo "$OUTPUTS" | jq -r '.[] | "\(.OutputKey): \(.OutputValue)"'
    echo ""
    echo "💡 The bastion host may not be deployed yet. Redeploy with:"
    echo "   cd infrastructure && npm run deploy"
    exit 1
fi

echo "✅ Bastion IP: $BASTION_IP"
echo "✅ Instance ID: $BASTION_INSTANCE_ID"
echo ""

# Check instance status
echo "2️⃣ Checking instance status..."
INSTANCE_STATE=$(aws ec2 describe-instances \
    --instance-ids "$BASTION_INSTANCE_ID" \
    --region "$REGION" \
    --query 'Reservations[0].Instances[0].State.Name' \
    --output text 2>/dev/null || echo "unknown")

echo "Instance state: $INSTANCE_STATE"

if [ "$INSTANCE_STATE" != "running" ]; then
    echo "❌ Instance is not running"
    if [ "$INSTANCE_STATE" = "stopped" ]; then
        echo "🔄 Starting instance..."
        aws ec2 start-instances --instance-ids "$BASTION_INSTANCE_ID" --region "$REGION"
        echo "⏳ Waiting for instance to start..."
        aws ec2 wait instance-running --instance-ids "$BASTION_INSTANCE_ID" --region "$REGION"
        echo "✅ Instance started"
    else
        echo "💡 Wait for instance to reach 'running' state"
        exit 1
    fi
fi

# Check key pair
echo ""
echo "3️⃣ Checking SSH key pair..."
if [ ! -f "$KEY_PATH" ]; then
    echo "❌ SSH key not found at: $KEY_PATH"
    echo "🔑 Creating new key pair..."
    
    # Delete existing key pair if it exists
    aws ec2 delete-key-pair --key-name "$KEY_NAME" --region "$REGION" 2>/dev/null || true
    
    # Create new key pair
    aws ec2 create-key-pair \
        --key-name "$KEY_NAME" \
        --region "$REGION" \
        --query 'KeyMaterial' \
        --output text > "$KEY_PATH"
    
    chmod 600 "$KEY_PATH"
    echo "✅ New key created at: $KEY_PATH"
else
    echo "✅ SSH key found at: $KEY_PATH"
    
    # Check permissions
    PERMS=$(stat -f "%A" "$KEY_PATH" 2>/dev/null || stat -c "%a" "$KEY_PATH" 2>/dev/null || echo "unknown")
    if [ "$PERMS" != "600" ]; then
        echo "⚠️  Fixing key permissions (was $PERMS, setting to 600)"
        chmod 600 "$KEY_PATH"
    fi
fi

# Check which key pair the instance is using
echo ""
echo "4️⃣ Checking instance key pair..."
INSTANCE_KEY=$(aws ec2 describe-instances \
    --instance-ids "$BASTION_INSTANCE_ID" \
    --region "$REGION" \
    --query 'Reservations[0].Instances[0].KeyName' \
    --output text 2>/dev/null || echo "None")

echo "Instance key pair: $INSTANCE_KEY"
echo "Expected key pair: $KEY_NAME"

if [ "$INSTANCE_KEY" != "$KEY_NAME" ]; then
    echo "❌ Key pair mismatch!"
    echo "💡 The instance was created with a different key pair"
    echo "🔧 Options:"
    echo "   1. Use the original key pair: $INSTANCE_KEY"
    echo "   2. Recreate the bastion host with correct key"
    echo "   3. Use AWS Systems Manager Session Manager instead"
fi

# Check security groups
echo ""
echo "5️⃣ Checking security groups..."
SECURITY_GROUPS=$(aws ec2 describe-instances \
    --instance-ids "$BASTION_INSTANCE_ID" \
    --region "$REGION" \
    --query 'Reservations[0].Instances[0].SecurityGroups[].GroupId' \
    --output text)

echo "Security groups: $SECURITY_GROUPS"

for SG in $SECURITY_GROUPS; do
    echo "📋 Rules for $SG:"
    aws ec2 describe-security-groups \
        --group-ids "$SG" \
        --region "$REGION" \
        --query 'SecurityGroups[0].IpPermissions[?FromPort==`22`]' \
        --output table 2>/dev/null || echo "  No SSH rules found"
done

# Check your public IP
echo ""
echo "6️⃣ Checking your public IP..."
YOUR_IP=$(curl -s https://checkip.amazonaws.com/ || echo "unknown")
echo "Your public IP: $YOUR_IP"

# Test network connectivity
echo ""
echo "7️⃣ Testing network connectivity..."
if nc -z -w5 "$BASTION_IP" 22 2>/dev/null; then
    echo "✅ Port 22 is reachable on $BASTION_IP"
else
    echo "❌ Port 22 is NOT reachable on $BASTION_IP"
    echo "💡 This could be due to:"
    echo "   - Security group not allowing SSH from your IP"
    echo "   - Network ACLs blocking traffic"
    echo "   - Instance not fully started"
fi

# Test SSH with verbose output
echo ""
echo "8️⃣ Testing SSH connection..."
echo "🧪 Running SSH test with verbose output..."
echo "   (This will show detailed connection information)"
echo ""

if [ -f "$KEY_PATH" ]; then
    timeout 10 ssh -v -i "$KEY_PATH" -o ConnectTimeout=10 -o StrictHostKeyChecking=no ec2-user@"$BASTION_IP" "echo 'SSH SUCCESS'" 2>&1 || true
else
    echo "❌ Cannot test SSH - key file not found"
fi

echo ""
echo "🔧 Troubleshooting Summary:"
echo "=========================="
echo "If SSH still fails, try these solutions:"
echo ""
echo "1. 🔑 Use AWS Systems Manager Session Manager (no SSH needed):"
echo "   aws ssm start-session --target $BASTION_INSTANCE_ID --region $REGION"
echo ""
echo "2. 🛡️  Add your IP to security group:"
echo "   aws ec2 authorize-security-group-ingress \\"
echo "     --group-id <security-group-id> \\"
echo "     --protocol tcp --port 22 \\"
echo "     --cidr $YOUR_IP/32 \\"
echo "     --region $REGION"
echo ""
echo "3. 🔄 Recreate bastion with correct key:"
echo "   cd infrastructure && npm run deploy"
echo ""
echo "4. 📞 Use EC2 Instance Connect (if supported):"
echo "   aws ec2-instance-connect send-ssh-public-key \\"
echo "     --instance-id $BASTION_INSTANCE_ID \\"
echo "     --availability-zone <az> \\"
echo "     --instance-os-user ec2-user \\"
echo "     --ssh-public-key file://~/.ssh/id_rsa.pub"