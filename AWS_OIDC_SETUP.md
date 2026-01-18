# AWS OIDC Setup for GitHub Actions

## Overview

This guide explains how to set up OpenID Connect (OIDC) authentication between GitHub Actions and AWS, which is more secure than using long-lived access keys.

## Benefits of OIDC over Access Keys

1. **No long-lived credentials** - No need to store AWS access keys in GitHub secrets
2. **Automatic credential rotation** - Temporary credentials are issued for each workflow run
3. **Fine-grained permissions** - Role-based access control with specific permissions
4. **Audit trail** - Better tracking of which workflows accessed which AWS resources
5. **Reduced security risk** - No risk of leaked access keys

## Step 1: Create IAM OIDC Identity Provider

### 1.1 Create the Identity Provider

```bash
# Using AWS CLI
aws iam create-open-id-connect-provider \
    --url https://token.actions.githubusercontent.com \
    --client-id-list sts.amazonaws.com \
    --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1 \
    --tags Key=Purpose,Value=GitHubActions Key=Project,Value=NoahReadingAgent
```

### 1.2 Note the ARN

The command will return an ARN like:

```
arn:aws:iam::123456789012:oidc-provider/token.actions.githubusercontent.com
```

Save this ARN - you'll need it for the IAM role.

## Step 2: Create IAM Roles

### 2.1 Production Deployment Role

Create a file `github-actions-production-role-trust-policy.json`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::YOUR_ACCOUNT_ID:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRole",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:YOUR_GITHUB_USERNAME/YOUR_REPO_NAME:ref:refs/heads/main"
        }
      }
    }
  ]
}
```

Create the role:

```bash
aws iam create-role \
    --role-name GitHubActions-NoahProduction \
    --assume-role-policy-document file://github-actions-production-role-trust-policy.json \
    --description "Role for GitHub Actions to deploy Noah Reading Agent to production"
```

### 2.2 Staging Deployment Role

Create a file `github-actions-staging-role-trust-policy.json`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::YOUR_ACCOUNT_ID:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRole",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": [
            "repo:YOUR_GITHUB_USERNAME/YOUR_REPO_NAME:ref:refs/heads/develop",
            "repo:YOUR_GITHUB_USERNAME/YOUR_REPO_NAME:pull_request"
          ]
        }
      }
    }
  ]
}
```

Create the role:

```bash
aws iam create-role \
    --role-name GitHubActions-NoahStaging \
    --assume-role-policy-document file://github-actions-staging-role-trust-policy.json \
    --description "Role for GitHub Actions to deploy Noah Reading Agent to staging"
```

## Step 3: Attach Policies to Roles

### 3.1 Production Role Policies

```bash
# ECS and ECR permissions
aws iam attach-role-policy \
    --role-name GitHubActions-NoahProduction \
    --policy-arn arn:aws:iam::aws:policy/AmazonECS_FullAccess

aws iam attach-role-policy \
    --role-name GitHubActions-NoahProduction \
    --policy-arn arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryFullAccess

# CloudWatch permissions
aws iam attach-role-policy \
    --role-name GitHubActions-NoahProduction \
    --policy-arn arn:aws:iam::aws:policy/CloudWatchFullAccess

# Amplify permissions
aws iam attach-role-policy \
    --role-name GitHubActions-NoahProduction \
    --policy-arn arn:aws:iam::aws:policy/AmplifyFullAccess

# Load Balancer permissions
aws iam attach-role-policy \
    --role-name GitHubActions-NoahProduction \
    --policy-arn arn:aws:iam::aws:policy/ElasticLoadBalancingFullAccess
```

### 3.2 Create Custom Policy for Additional Permissions

Create `noah-deployment-policy.json`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::amplify-deployments/*",
        "arn:aws:s3:::amplify-staging-deployments/*",
        "arn:aws:s3:::amplify-deployments",
        "arn:aws:s3:::amplify-staging-deployments"
      ]
    },
    {
      "Effect": "Allow",
      "Action": ["iam:PassRole"],
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "iam:PassedToService": [
            "ecs-tasks.amazonaws.com",
            "amplify.amazonaws.com"
          ]
        }
      }
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents",
        "logs:DescribeLogGroups",
        "logs:DescribeLogStreams",
        "logs:FilterLogEvents"
      ],
      "Resource": "*"
    }
  ]
}
```

Create and attach the policy:

```bash
aws iam create-policy \
    --policy-name NoahDeploymentPolicy \
    --policy-document file://noah-deployment-policy.json

aws iam attach-role-policy \
    --role-name GitHubActions-NoahProduction \
    --policy-arn arn:aws:iam::YOUR_ACCOUNT_ID:policy/NoahDeploymentPolicy

aws iam attach-role-policy \
    --role-name GitHubActions-NoahStaging \
    --policy-arn arn:aws:iam::YOUR_ACCOUNT_ID:policy/NoahDeploymentPolicy
```

## Step 4: Update GitHub Secrets

Instead of AWS access keys, you now need these secrets:

### Required Secrets

1. **AWS_ROLE_ARN_PRODUCTION** - `arn:aws:iam::YOUR_ACCOUNT_ID:role/GitHubActions-NoahProduction`
2. **AWS_ROLE_ARN_STAGING** - `arn:aws:iam::YOUR_ACCOUNT_ID:role/GitHubActions-NoahStaging`
3. **AWS_REGION** - `ap-northeast-1` (or your preferred region)

### Optional Secrets (keep existing ones)

- `COGNITO_USER_POOL_ID`
- `COGNITO_CLIENT_ID`
- `COGNITO_IDENTITY_POOL_ID`
- `OPENAI_API_KEY_TEST`
- etc.

## Step 5: Test the Setup

### 5.1 Test Production Role

```bash
# Test assuming the production role
aws sts assume-role-with-web-identity \
    --role-arn arn:aws:iam::YOUR_ACCOUNT_ID:role/GitHubActions-NoahProduction \
    --role-session-name test-session \
    --web-identity-token "$(curl -H "Authorization: bearer $ACTIONS_ID_TOKEN_REQUEST_TOKEN" "$ACTIONS_ID_TOKEN_REQUEST_URL&audience=sts.amazonaws.com" | jq -r '.value')"
```

### 5.2 Test Staging Role

```bash
# Test assuming the staging role
aws sts assume-role-with-web-identity \
    --role-arn arn:aws:iam::YOUR_ACCOUNT_ID:role/GitHubActions-NoahStaging \
    --role-session-name test-session \
    --web-identity-token "$(curl -H "Authorization: bearer $ACTIONS_ID_TOKEN_REQUEST_TOKEN" "$ACTIONS_ID_TOKEN_REQUEST_URL&audience=sts.amazonaws.com" | jq -r '.value')"
```

## Troubleshooting

### Common Issues

1. **"No OpenIDConnect provider found"**
   - Verify the OIDC provider was created correctly
   - Check the thumbprint is correct

2. **"Not authorized to perform sts:AssumeRole"**
   - Check the trust policy conditions
   - Verify the repository name and branch in the condition

3. **"Access denied" during deployment**
   - Check that all necessary policies are attached to the role
   - Verify the role has permissions for the specific AWS services

### Debugging Steps

1. **Check OIDC Provider:**

   ```bash
   aws iam list-open-id-connect-providers
   ```

2. **Check Role Trust Policy:**

   ```bash
   aws iam get-role --role-name GitHubActions-NoahProduction
   ```

3. **Check Attached Policies:**
   ```bash
   aws iam list-attached-role-policies --role-name GitHubActions-NoahProduction
   ```

## Security Best Practices

1. **Principle of Least Privilege** - Only grant the minimum permissions needed
2. **Branch Restrictions** - Limit production role to main branch only
3. **Regular Audits** - Review role permissions periodically
4. **Monitoring** - Set up CloudTrail to monitor role usage
5. **Rotation** - OIDC tokens are automatically rotated, no manual action needed

## Next Steps

After setting up OIDC:

1. Update your GitHub Actions workflows to use the new authentication method
2. Remove the old AWS access key secrets from GitHub
3. Test deployments to ensure everything works
4. Set up monitoring for the new authentication method
5. Document the new process for your team

This OIDC setup provides a more secure and maintainable way to authenticate GitHub Actions with AWS services.
