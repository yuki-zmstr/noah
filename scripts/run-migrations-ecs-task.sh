#!/bin/bash

# Run Database Migrations as ECS Task
# This script runs migrations as an ECS task within the VPC where it can access the database

set -e

echo "🗄️ Running Database Migrations via ECS Task..."

# Configuration
AWS_REGION=${AWS_REGION:-"ap-northeast-1"}
STACK_NAME="NoahInfrastructureStack"
ECR_REPOSITORY="noah-backend"

# Get ECS cluster from CloudFormation
ECS_CLUSTER=$(aws cloudformation describe-stack-resources \
  --stack-name $STACK_NAME \
  --query 'StackResources[?ResourceType==`AWS::ECS::Cluster`].PhysicalResourceId' \
  --output text)

echo "Using ECS cluster: $ECS_CLUSTER"

# Get VPC and subnet information
VPC_ID=$(aws ec2 describe-vpcs \
  --filters "Name=tag:aws:cloudformation:stack-name,Values=$STACK_NAME" \
  --query 'Vpcs[0].VpcId' \
  --output text)

PRIVATE_SUBNETS=$(aws ec2 describe-subnets \
  --filters "Name=vpc-id,Values=$VPC_ID" "Name=tag:aws-cdk:subnet-type,Values=Private" \
  --query 'Subnets[].SubnetId' \
  --output text | tr '\t' ',')

echo "VPC ID: $VPC_ID"
echo "Private subnets: $PRIVATE_SUBNETS"

# Get security group that allows database access
BACKEND_SECURITY_GROUP=$(aws ec2 describe-security-groups \
  --filters "Name=vpc-id,Values=$VPC_ID" "Name=group-name,Values=*BackendService*" \
  --query 'SecurityGroups[0].GroupId' \
  --output text)

echo "Backend security group: $BACKEND_SECURITY_GROUP"

# Get database connection details
DB_ENDPOINT=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --query 'Stacks[0].Outputs[?OutputKey==`DatabaseEndpoint`].OutputValue' \
  --output text)

# Get database secret ARN
DB_SECRET_ARN=$(aws secretsmanager list-secrets \
  --query 'SecretList[?contains(Name, `NoahInfrastructureStack`)].ARN' \
  --output text | head -1)

echo "Database endpoint: $DB_ENDPOINT"
echo "Database secret: $DB_SECRET_ARN"

# Get ECR repository URI
ECR_URI=$(aws ecr describe-repositories --repository-names $ECR_REPOSITORY --query 'repositories[0].repositoryUri' --output text)
MIGRATION_IMAGE="$ECR_URI:latest"

echo "Using image: $MIGRATION_IMAGE"

# Create task definition for migrations
TASK_DEFINITION_JSON=$(cat <<EOF
{
  "family": "noah-migrations",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "executionRoleArn": "arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "migration-container",
      "image": "$MIGRATION_IMAGE",
      "essential": true,
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/noah-migrations",
          "awslogs-region": "$AWS_REGION",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "environment": [
        {
          "name": "DATABASE_HOST",
          "value": "$DB_ENDPOINT"
        },
        {
          "name": "DATABASE_PORT",
          "value": "5432"
        },
        {
          "name": "DATABASE_NAME",
          "value": "noah"
        },
        {
          "name": "DATABASE_USER",
          "value": "noah_db_admin"
        }
      ],
      "secrets": [
        {
          "name": "DATABASE_PASSWORD",
          "valueFrom": "$DB_SECRET_ARN:password::"
        }
      ],
      "command": ["uv", "run", "alembic", "upgrade", "head"]
    }
  ]
}
EOF
)

# Create CloudWatch log group if it doesn't exist
aws logs create-log-group --log-group-name "/ecs/noah-migrations" --region $AWS_REGION || echo "Log group already exists"

# Register task definition
echo "📝 Registering migration task definition..."
TASK_DEF_ARN=$(echo "$TASK_DEFINITION_JSON" | aws ecs register-task-definition --cli-input-json file:///dev/stdin --query 'taskDefinition.taskDefinitionArn' --output text)

echo "Task definition registered: $TASK_DEF_ARN"

# Run the migration task
echo "🚀 Running migration task..."
TASK_ARN=$(aws ecs run-task \
  --cluster $ECS_CLUSTER \
  --task-definition $TASK_DEF_ARN \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[$PRIVATE_SUBNETS],securityGroups=[$BACKEND_SECURITY_GROUP],assignPublicIp=DISABLED}" \
  --query 'tasks[0].taskArn' \
  --output text)

echo "Migration task started: $TASK_ARN"

# Wait for task to complete
echo "⏳ Waiting for migration task to complete..."
aws ecs wait tasks-stopped --cluster $ECS_CLUSTER --tasks $TASK_ARN

# Check task exit code
TASK_STATUS=$(aws ecs describe-tasks \
  --cluster $ECS_CLUSTER \
  --tasks $TASK_ARN \
  --query 'tasks[0].containers[0].exitCode' \
  --output text)

if [ "$TASK_STATUS" = "0" ]; then
  echo "✅ Migration task completed successfully!"
else
  echo "❌ Migration task failed with exit code: $TASK_STATUS"
  
  # Get logs for debugging
  echo "📋 Migration task logs:"
  aws logs get-log-events \
    --log-group-name "/ecs/noah-migrations" \
    --log-stream-name "ecs/migration-container/$(echo $TASK_ARN | cut -d'/' -f3)" \
    --query 'events[].message' \
    --output text || echo "Could not retrieve logs"
  
  exit 1
fi

echo "✅ Database migrations completed successfully!"