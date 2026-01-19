# Noah Reading Agent - Deployment Guide

This guide covers the complete deployment process for the Noah Reading Agent to AWS, including infrastructure setup, application deployment, and production testing.

## Prerequisites

Before starting the deployment, ensure you have:

- AWS CLI installed and configured with appropriate permissions
- AWS CDK CLI installed (`npm install -g aws-cdk`)
- Docker installed and running
- Node.js and npm installed
- Git repository set up (for Amplify deployment)

## Quick Commands Summary

Here are the essential commands to run:

```bash
# 1. Deploy infrastructure
cd infrastructure
npm install
cdk bootstrap
cdk deploy

# 2. Build and push backend
cd ..
./scripts/build-and-push.sh

# 3. Set up Amplify manually (see detailed steps below)

# 4. Test deployment
./scripts/test-production.sh
```

## Deployment Overview

The Noah Reading Agent uses the following AWS services:

- **Amazon Cognito**: User authentication and authorization
- **AWS Amplify**: Frontend hosting with automatic builds (configured manually)
- **Amazon ECS Fargate**: Backend API hosting
- **Amazon RDS PostgreSQL**: User data and conversation storage
- **Amazon OpenSearch**: Vector similarity search for content
- **Amazon CloudFront**: Global content delivery
- **Amazon ECR**: Docker image registry
- **Amazon S3**: Static asset and content storage

## Step-by-Step Deployment

### 1. Deploy Core Infrastructure

```bash
cd infrastructure
npm install
npm run build
cdk bootstrap
cdk deploy
```

### 2. Build and Push Backend Image

```bash
cd ..
./scripts/build-and-push.sh
```

### 3. Set Up Amplify Manually

Since Amplify CDK constructs have compatibility issues, we'll set up Amplify through the console:

1. Go to [AWS Amplify Console](https://console.aws.amazon.com/amplify/home)
2. Click "New app" > "Host web app"
3. Choose "GitHub" as your source
4. Connect your repository and select the branch (main)
5. Configure build settings:
   - Build command: `cd frontend && npm ci && npm run build`
   - Base directory: `frontend`
   - Artifact base directory: `frontend/dist`
6. Add environment variables (get values from CDK outputs):
   ```
   VITE_AWS_REGION=us-east-1
   VITE_COGNITO_USER_POOL_ID=<from CDK output>
   VITE_COGNITO_CLIENT_ID=<from CDK output>
   VITE_COGNITO_IDENTITY_POOL_ID=<from CDK output>
   VITE_API_ENDPOINT=https://<backend-url-from-cdk>
   VITE_API_BASE_URL=https://<backend-url-from-cdk>/api
   VITE_ENABLE_DISCOVERY_MODE=true
   VITE_ENABLE_MULTILINGUAL=true
   VITE_DEFAULT_LANGUAGE=english
   VITE_MAX_MESSAGE_LENGTH=2000
   VITE_TYPING_INDICATOR_DELAY=1000
   ```
7. Deploy the app

### 4. Update Cognito Callback URLs

After Amplify deployment, update Cognito with the Amplify URL:

```bash
# Get your Amplify URL from the console, then run:
aws cognito-idp update-user-pool-client \
  --user-pool-id <USER_POOL_ID> \
  --client-id <CLIENT_ID> \
  --callback-urls https://your-amplify-url.amplifyapp.com,http://localhost:5173 \
  --logout-urls https://your-amplify-url.amplifyapp.com,http://localhost:5173
```

### 5. Test the Deployment

```bash
./scripts/test-production.sh
```

## Configuration Values

### Get CDK Outputs

After infrastructure deployment, get the configuration values:

```bash
# Get all stack outputs
aws cloudformation describe-stacks --stack-name NoahInfrastructureStack --query "Stacks[0].Outputs"
```

Key outputs you'll need for Amplify:

- `UserPoolId`: Cognito User Pool ID
- `UserPoolClientId`: Cognito Client ID
- `IdentityPoolId`: Cognito Identity Pool ID
- `BackendUrl`: Backend API URL

### Environment Variables for Amplify

Use these in your Amplify app configuration:

```
VITE_AWS_REGION=us-east-1
VITE_COGNITO_USER_POOL_ID=<UserPoolId from CDK>
VITE_COGNITO_CLIENT_ID=<UserPoolClientId from CDK>
VITE_COGNITO_IDENTITY_POOL_ID=<IdentityPoolId from CDK>
VITE_API_ENDPOINT=https://<BackendUrl from CDK>
VITE_API_BASE_URL=https://<BackendUrl from CDK>/api
VITE_ENABLE_DISCOVERY_MODE=true
VITE_ENABLE_MULTILINGUAL=true
VITE_DEFAULT_LANGUAGE=english
VITE_MAX_MESSAGE_LENGTH=2000
VITE_TYPING_INDICATOR_DELAY=1000
```

## Access Your Application

After successful deployment:

- **Frontend**: Your Amplify app URL (from Amplify console)
- **Backend API**: Check CDK outputs for backend URL
- **Production Test Page**: `https://your-amplify-url/test`

## Troubleshooting

### Common Issues

1. **CDK Bootstrap Error**:

   ```bash
   cdk bootstrap --region us-east-1
   ```

2. **Docker Build Fails**:
   - Ensure Docker is running
   - Check Docker permissions
   - Verify ECR repository exists

3. **Amplify Build Fails**:
   - Check build logs in Amplify console
   - Verify environment variables are set correctly
   - Ensure repository access permissions

4. **Database Connection Issues**:
   - Verify VPC security groups
   - Check RDS instance status
   - Validate connection strings

### Getting Help

1. **ECS Task Logs**:

   ```bash
   aws logs describe-log-groups --log-group-name-prefix "/aws/ecs/noah"
   ```

2. **CloudFormation Events**:
   ```bash
   aws cloudformation describe-stack-events --stack-name NoahInfrastructureStack
   ```

The deployment creates a production-ready infrastructure with monitoring, security, and scalability built in.
