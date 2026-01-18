#!/bin/bash

# Script to get RDS connection details for DBeaver
# Usage: ./scripts/get-db-connection.sh [stack-name]

set -e

STACK_NAME=${1:-"NoahInfrastructureStack"}
REGION=${AWS_REGION:-"ap-northeast-1"}

echo "🔍 Getting RDS connection details for stack: $STACK_NAME"
echo "📍 Region: $REGION"
echo ""

# Get stack outputs
echo "📋 Fetching CloudFormation outputs..."
OUTPUTS=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$REGION" \
    --query 'Stacks[0].Outputs' \
    --output json 2>/dev/null || echo "[]")

if [ "$OUTPUTS" = "[]" ]; then
    echo "❌ Stack not found or no outputs available"
    echo "💡 Make sure the stack is deployed and you have the correct stack name"
    exit 1
fi

# Extract database endpoint
DB_ENDPOINT=$(echo "$OUTPUTS" | jq -r '.[] | select(.OutputKey=="DatabaseEndpoint") | .OutputValue' 2>/dev/null || echo "")
BASTION_IP=$(echo "$OUTPUTS" | jq -r '.[] | select(.OutputKey=="BastionHostPublicIP") | .OutputValue' 2>/dev/null || echo "")

if [ -z "$DB_ENDPOINT" ]; then
    echo "❌ Database endpoint not found in stack outputs"
    exit 1
fi

echo "✅ Database endpoint: $DB_ENDPOINT"

# Get database credentials from Secrets Manager
echo "🔐 Fetching database credentials..."
SECRET_ARN=$(aws rds describe-db-instances \
    --region "$REGION" \
    --query 'DBInstances[?DBName==`noah`].MasterUserSecret.SecretArn' \
    --output text 2>/dev/null || echo "")

if [ -z "$SECRET_ARN" ]; then
    echo "⚠️  Could not find secret ARN, trying alternative method..."
    # Try to find secret by name pattern
    SECRET_ARN=$(aws secretsmanager list-secrets \
        --region "$REGION" \
        --query 'SecretList[?contains(Name, `noah`) && contains(Name, `rds`)].ARN' \
        --output text | head -1)
fi

if [ -n "$SECRET_ARN" ]; then
    echo "🔑 Found secret: $SECRET_ARN"
    
    SECRET_VALUE=$(aws secretsmanager get-secret-value \
        --secret-id "$SECRET_ARN" \
        --region "$REGION" \
        --query 'SecretString' \
        --output text)
    
    DB_USERNAME=$(echo "$SECRET_VALUE" | jq -r '.username')
    DB_PASSWORD=$(echo "$SECRET_VALUE" | jq -r '.password')
    
    echo "✅ Retrieved credentials for user: $DB_USERNAME"
else
    echo "⚠️  Could not retrieve database credentials automatically"
    DB_USERNAME="noah_db_admin"
    DB_PASSWORD="<check AWS Secrets Manager>"
fi

# Display connection information
echo ""
echo "🎯 DBeaver Connection Details:"
echo "================================"
echo "Connection Type: PostgreSQL"
echo "Host: $DB_ENDPOINT"
echo "Port: 5432"
echo "Database: noah"
echo "Username: $DB_USERNAME"
echo "Password: $DB_PASSWORD"
echo ""

if [ -n "$BASTION_IP" ]; then
    echo "🖥️  Bastion Host Details:"
    echo "========================="
    echo "Public IP: $BASTION_IP"
    echo "SSH Command: ssh -i ~/.ssh/noah-bastion-key.pem ec2-user@$BASTION_IP"
    echo ""
    echo "🔗 SSH Tunnel for DBeaver:"
    echo "=========================="
    echo "1. Create SSH tunnel:"
    echo "   ssh -i ~/.ssh/noah-bastion-key.pem -L 5432:$DB_ENDPOINT:5432 ec2-user@$BASTION_IP"
    echo ""
    echo "2. In DBeaver, use these settings:"
    echo "   Host: localhost"
    echo "   Port: 5432"
    echo "   Database: noah"
    echo "   Username: $DB_USERNAME"
    echo "   Password: $DB_PASSWORD"
else
    echo "⚠️  Bastion host not found. You'll need to:"
    echo "1. Deploy the updated infrastructure with bastion host"
    echo "2. Or configure VPN access to your VPC"
    echo "3. Or temporarily modify RDS security group (not recommended)"
fi

echo ""
echo "📝 Next Steps:"
echo "=============="
echo "1. If bastion host exists, create SSH tunnel (command above)"
echo "2. Open DBeaver and create new PostgreSQL connection"
echo "3. Use localhost:5432 if using SSH tunnel, or direct endpoint if VPN connected"
echo "4. Test connection"