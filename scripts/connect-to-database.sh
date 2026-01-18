#!/bin/bash

# One-stop script for connecting to the Noah database via bastion host
# Usage: ./scripts/connect-to-database.sh [action]
# Actions: setup, tunnel, info, psql

set -e

STACK_NAME="NoahInfrastructureStack"
REGION=${AWS_REGION:-"ap-northeast-1"}
KEY_PATH="$HOME/.ssh/noah-bastion-key.pem"
ACTION=${1:-"info"}

case "$ACTION" in
    "setup")
        echo "🚀 Setting up bastion host access..."
        ./scripts/setup-bastion-access.sh "$STACK_NAME"
        ;;
    
    "tunnel")
        echo "🔗 Creating SSH tunnel to database..."
        
        # Get connection details
        OUTPUTS=$(aws cloudformation describe-stacks \
            --stack-name "$STACK_NAME" \
            --region "$REGION" \
            --query 'Stacks[0].Outputs' \
            --output json)
        
        BASTION_IP=$(echo "$OUTPUTS" | jq -r '.[] | select(.OutputKey=="BastionHostPublicIP") | .OutputValue')
        DB_ENDPOINT=$(echo "$OUTPUTS" | jq -r '.[] | select(.OutputKey=="DatabaseEndpoint") | .OutputValue')
        
        if [ -z "$BASTION_IP" ] || [ -z "$DB_ENDPOINT" ]; then
            echo "❌ Could not get connection details. Run setup first:"
            echo "   ./scripts/connect-to-database.sh setup"
            exit 1
        fi
        
        echo "🔗 Creating tunnel: localhost:5432 -> $DB_ENDPOINT:5432"
        echo "💡 Keep this terminal open while using DBeaver"
        echo "🛑 Press Ctrl+C to close tunnel"
        echo ""
        
        ssh -i "$KEY_PATH" -L 5432:"$DB_ENDPOINT":5432 ec2-user@"$BASTION_IP"
        ;;
    
    "info")
        echo "📋 Getting database connection information..."
        ./scripts/get-db-connection.sh "$STACK_NAME"
        ;;
    
    "psql")
        echo "🐘 Connecting with psql via tunnel..."
        
        # Check if tunnel is running
        if ! nc -z localhost 5432 2>/dev/null; then
            echo "❌ No tunnel detected on localhost:5432"
            echo "💡 Start tunnel first: ./scripts/connect-to-database.sh tunnel"
            exit 1
        fi
        
        # Get credentials
        OUTPUTS=$(aws cloudformation describe-stacks \
            --stack-name "$STACK_NAME" \
            --region "$REGION" \
            --query 'Stacks[0].Outputs' \
            --output json)
        
        # Get secret
        SECRET_ARN=$(aws rds describe-db-instances \
            --region "$REGION" \
            --query 'DBInstances[?DBName==`noah`].MasterUserSecret.SecretArn' \
            --output text 2>/dev/null || echo "")
        
        if [ -n "$SECRET_ARN" ]; then
            SECRET_VALUE=$(aws secretsmanager get-secret-value \
                --secret-id "$SECRET_ARN" \
                --region "$REGION" \
                --query 'SecretString' \
                --output text)
            
            DB_USERNAME=$(echo "$SECRET_VALUE" | jq -r '.username')
            DB_PASSWORD=$(echo "$SECRET_VALUE" | jq -r '.password')
            
            echo "🔐 Connecting as $DB_USERNAME..."
            PGPASSWORD="$DB_PASSWORD" psql -h localhost -p 5432 -U "$DB_USERNAME" -d noah
        else
            echo "❌ Could not retrieve database credentials"
            echo "💡 Connect manually: psql -h localhost -p 5432 -U noah_db_admin -d noah"
        fi
        ;;
    
    *)
        echo "Noah Database Connection Helper"
        echo "=============================="
        echo ""
        echo "Usage: $0 [action]"
        echo ""
        echo "Actions:"
        echo "  setup   - Set up bastion host and SSH keys"
        echo "  tunnel  - Create SSH tunnel (keep running for DBeaver)"
        echo "  info    - Show connection details for DBeaver"
        echo "  psql    - Connect with psql via tunnel"
        echo ""
        echo "Typical workflow:"
        echo "1. $0 setup    (one time)"
        echo "2. $0 tunnel   (in one terminal, keep running)"
        echo "3. $0 info     (in another terminal, for DBeaver setup)"
        echo ""
        ;;
esac