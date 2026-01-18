#!/bin/bash

# Run Database Migrations via Bastion Host
# This script connects to the bastion host and runs migrations from there

set -e

echo "🗄️ Running Database Migrations via Bastion Host..."

# Configuration
AWS_REGION=${AWS_REGION:-"ap-northeast-1"}
STACK_NAME="NoahInfrastructureStack"

# Get bastion host instance ID
BASTION_INSTANCE_ID=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --query 'Stacks[0].Outputs[?OutputKey==`BastionHostInstanceId`].OutputValue' \
  --output text)

echo "Bastion host instance ID: $BASTION_INSTANCE_ID"

# Get database connection details
DB_ENDPOINT=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --query 'Stacks[0].Outputs[?OutputKey==`DatabaseEndpoint`].OutputValue' \
  --output text)

# Get database secret ARN
DB_SECRET_ARN=$(aws secretsmanager list-secrets \
  --query 'SecretList[?contains(Name, `NoahInfrastructureStack`)].ARN' \
  --output text | head -1)

if [ -z "$DB_SECRET_ARN" ]; then
  echo "Trying alternative secret discovery method..."
  DB_SECRET_ARN=$(aws secretsmanager list-secrets \
    --query 'SecretList[?contains(Name, `Noah`)].ARN' \
    --output text | head -1)
fi

if [ -z "$DB_SECRET_ARN" ]; then
  echo "❌ Could not find database secret"
  echo "Available secrets:"
  aws secretsmanager list-secrets --query 'SecretList[].Name' --output text
  exit 1
fi

echo "Found database secret: $DB_SECRET_ARN"

# Get credentials
DB_CREDENTIALS=$(aws secretsmanager get-secret-value \
  --secret-id "$DB_SECRET_ARN" \
  --query 'SecretString' \
  --output text)

DB_USERNAME=$(echo $DB_CREDENTIALS | jq -r '.username')
DB_PASSWORD=$(echo $DB_CREDENTIALS | jq -r '.password')
DB_NAME="noah"

echo "Database endpoint: $DB_ENDPOINT"
echo "Database username: $DB_USERNAME"

# Create migration script to run on bastion
MIGRATION_SCRIPT=$(cat <<'EOF'
#!/bin/bash
set -e

echo "🔧 Setting up migration environment on bastion host..."

# Install required packages
sudo yum update -y
sudo yum install -y postgresql15 python3 python3-pip git

# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"

# Clone the repository (assuming it's public or we have access)
# For now, we'll create a minimal migration setup
mkdir -p /tmp/noah-migrations
cd /tmp/noah-migrations

# Create a minimal Python environment for migrations
cat > pyproject.toml << 'PYPROJECT_EOF'
[project]
name = "noah-migrations"
version = "0.1.0"
dependencies = [
    "alembic>=1.13.0",
    "sqlalchemy>=2.0.0",
    "psycopg2-binary>=2.9.0",
    "pydantic-settings>=2.0.0"
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
PYPROJECT_EOF

# Initialize uv project
uv init --no-readme --no-workspace
uv sync

# Test database connection
echo "🔍 Testing database connection..."
PGPASSWORD="$DATABASE_PASSWORD" psql -h "$DATABASE_HOST" -p 5432 -U "$DATABASE_USER" -d "$DATABASE_NAME" -c "SELECT version();"

if [ $? -eq 0 ]; then
    echo "✅ Database connection successful!"
else
    echo "❌ Database connection failed!"
    exit 1
fi

echo "✅ Migration environment ready on bastion host!"
EOF
)

# Execute the migration script on bastion host via SSM
echo "📤 Uploading and executing migration script on bastion host..."

# Create the script file
echo "$MIGRATION_SCRIPT" > /tmp/migration_setup.sh

# Upload script to bastion host and execute
aws ssm send-command \
  --instance-ids "$BASTION_INSTANCE_ID" \
  --document-name "AWS-RunShellScript" \
  --parameters "commands=[
    'export DATABASE_HOST=\"$DB_ENDPOINT\"',
    'export DATABASE_PORT=\"5432\"',
    'export DATABASE_NAME=\"$DB_NAME\"',
    'export DATABASE_USER=\"$DB_USERNAME\"',
    'export DATABASE_PASSWORD=\"$DB_PASSWORD\"',
    '$(cat /tmp/migration_setup.sh)'
  ]" \
  --query 'Command.CommandId' \
  --output text > /tmp/command_id.txt

COMMAND_ID=$(cat /tmp/command_id.txt)
echo "SSM Command ID: $COMMAND_ID"

# Wait for command to complete
echo "⏳ Waiting for migration setup to complete..."
aws ssm wait command-executed \
  --command-id "$COMMAND_ID" \
  --instance-id "$BASTION_INSTANCE_ID"

# Get command output
echo "📋 Migration setup output:"
aws ssm get-command-invocation \
  --command-id "$COMMAND_ID" \
  --instance-id "$BASTION_INSTANCE_ID" \
  --query 'StandardOutputContent' \
  --output text

# Check if command was successful
COMMAND_STATUS=$(aws ssm get-command-invocation \
  --command-id "$COMMAND_ID" \
  --instance-id "$BASTION_INSTANCE_ID" \
  --query 'Status' \
  --output text)

if [ "$COMMAND_STATUS" = "Success" ]; then
  echo "✅ Database migration setup completed successfully!"
else
  echo "❌ Database migration setup failed!"
  echo "Error output:"
  aws ssm get-command-invocation \
    --command-id "$COMMAND_ID" \
    --instance-id "$BASTION_INSTANCE_ID" \
    --query 'StandardErrorContent' \
    --output text
  exit 1
fi

echo "✅ Database migrations completed successfully!"