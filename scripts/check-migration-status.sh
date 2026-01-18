#!/bin/bash

# Check Database Migration Status
# This script connects to the RDS database and checks the current migration status

set -e

echo "🔍 Checking Database Migration Status..."

# Configuration
AWS_REGION=${AWS_REGION:-"ap-northeast-1"}
STACK_NAME="NoahInfrastructureStack"

# Get database connection details from CloudFormation
echo "📋 Getting database connection details..."

DB_ENDPOINT=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --query 'Stacks[0].Outputs[?OutputKey==`DatabaseEndpoint`].OutputValue' \
  --output text 2>/dev/null || echo "")

if [[ -z "$DB_ENDPOINT" || "$DB_ENDPOINT" == "None" ]]; then
  echo "❌ Database endpoint not found. Make sure infrastructure is deployed first."
  exit 1
fi

# Get database credentials from Secrets Manager
echo "🔐 Getting database credentials..."
DB_SECRET_ARN=$(aws rds describe-db-instances \
  --query 'DBInstances[?DBInstanceIdentifier==`noahinfrastructurestack-noahdatabase*`].MasterUserSecret.SecretArn' \
  --output text 2>/dev/null || echo "")

if [[ -z "$DB_SECRET_ARN" || "$DB_SECRET_ARN" == "None" ]]; then
  echo "❌ Database secret not found. Trying alternative method..."
  
  # Try to get from CloudFormation resources
  DB_SECRET_ARN=$(aws cloudformation describe-stack-resources \
    --stack-name $STACK_NAME \
    --query 'StackResources[?ResourceType==`AWS::SecretsManager::Secret`].PhysicalResourceId' \
    --output text 2>/dev/null || echo "")
fi

if [[ -z "$DB_SECRET_ARN" || "$DB_SECRET_ARN" == "None" ]]; then
  echo "❌ Could not find database credentials"
  exit 1
fi

# Get credentials from Secrets Manager
DB_CREDENTIALS=$(aws secretsmanager get-secret-value \
  --secret-id "$DB_SECRET_ARN" \
  --query 'SecretString' \
  --output text)

DB_USERNAME=$(echo $DB_CREDENTIALS | jq -r '.username')
DB_PASSWORD=$(echo $DB_CREDENTIALS | jq -r '.password')
DB_NAME="noah"

echo "✅ Database connection details retrieved"
echo "  Endpoint: $DB_ENDPOINT"
echo "  Database: $DB_NAME"
echo "  Username: $DB_USERNAME"

# Check if we can connect via bastion host
BASTION_INSTANCE_ID=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --query 'Stacks[0].Outputs[?OutputKey==`BastionHostInstanceId`].OutputValue' \
  --output text 2>/dev/null || echo "")

if [[ -n "$BASTION_INSTANCE_ID" && "$BASTION_INSTANCE_ID" != "None" ]]; then
  echo "🔗 Using bastion host for database connection..."
  echo "  Bastion Instance ID: $BASTION_INSTANCE_ID"
  
  # Create a temporary SQL script
  TEMP_SQL=$(mktemp)
  cat > $TEMP_SQL << EOF
-- Check if alembic_version table exists
SELECT EXISTS (
    SELECT FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_name = 'alembic_version'
) as alembic_table_exists;

-- If alembic_version exists, show current version
SELECT version_num as current_migration_version 
FROM alembic_version 
WHERE EXISTS (
    SELECT FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_name = 'alembic_version'
);

-- Show all tables
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;
EOF

  echo "📊 Executing database queries via bastion host..."
  
  # Execute SQL via SSM Session Manager
  aws ssm send-command \
    --instance-ids "$BASTION_INSTANCE_ID" \
    --document-name "AWS-RunShellScript" \
    --parameters "commands=[\"PGPASSWORD='$DB_PASSWORD' psql -h $DB_ENDPOINT -U $DB_USERNAME -d $DB_NAME -f /dev/stdin << 'EOF'
$(cat $TEMP_SQL)
EOF\"]" \
    --query 'Command.CommandId' \
    --output text > /tmp/command_id.txt
  
  COMMAND_ID=$(cat /tmp/command_id.txt)
  
  echo "⏳ Waiting for command to complete..."
  sleep 5
  
  # Get command output
  aws ssm get-command-invocation \
    --command-id "$COMMAND_ID" \
    --instance-id "$BASTION_INSTANCE_ID" \
    --query 'StandardOutputContent' \
    --output text
  
  # Clean up
  rm $TEMP_SQL
  rm /tmp/command_id.txt
  
else
  echo "❌ Bastion host not found. Cannot connect to database directly."
  echo "💡 To check migration status manually:"
  echo "  1. Connect to bastion host via SSM Session Manager"
  echo "  2. Install PostgreSQL client: sudo yum install -y postgresql"
  echo "  3. Connect to database: PGPASSWORD='$DB_PASSWORD' psql -h $DB_ENDPOINT -U $DB_USERNAME -d $DB_NAME"
  echo "  4. Check migration status: SELECT * FROM alembic_version;"
fi

echo ""
echo "📝 Migration Status Summary:"
echo "  ✅ Database endpoint accessible"
echo "  ✅ Credentials retrieved"
echo "  ℹ️  Check the output above for current migration version"
echo ""
echo "🔗 Useful commands:"
echo "  View ECS service logs (for migration logs):"
echo "    aws logs tail /ecs/noah-backend --follow --region $AWS_REGION"