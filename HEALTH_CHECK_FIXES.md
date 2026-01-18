# Health Check Deployment Fixes

## Problem

The ALB health checks were failing with 400 Bad Request errors, causing the ECS service deployment to fail and triggering stack rollback.

## Root Causes Identified

1. **Incorrect Health Check Path**: The ALB target group was using the default health check path (`/`) instead of the application's health endpoint (`/health`)

2. **Environment Variable Mismatch**: The infrastructure was setting environment variables that didn't match what the Python application expected

3. **Health Check Complexity**: The health check endpoint was too complex and might have been affected by middleware

## Fixes Applied

### 1. Infrastructure Changes (`infrastructure/lib/noah-infrastructure-stack.ts`)

- **Added explicit health check configuration**:

  ```typescript
  backendService.targetGroup.configureHealthCheck({
    path: "/health",
    healthyHttpCodes: "200",
    interval: cdk.Duration.seconds(30),
    timeout: cdk.Duration.seconds(5),
    healthyThresholdCount: 2,
    unhealthyThresholdCount: 5,
  });
  ```

- **Fixed environment variables** to match Python application expectations:
  ```typescript
  environment: {
    APP_NAME: 'Noah Reading Agent',
    APP_VERSION: '0.1.0',
    DEBUG: 'false',
    DATABASE_HOST: database.instanceEndpoint.hostname,
    DATABASE_PORT: '5432',
    DATABASE_NAME: 'noah',
    DATABASE_USER: 'noah_db_admin',
    AWS_REGION: this.region,
    ALLOWED_ORIGINS: 'http://localhost:5173,https://localhost:5173',
    // ... other vars
  }
  ```

### 2. Backend Application Changes (`python-backend/src/main.py`)

- **Simplified health check endpoint**:

  ```python
  @app.get("/health")
  async def health_check():
      """Health check endpoint for load balancer."""
      return {"status": "healthy"}
  ```

- **Improved request logging** to help debug future issues
- **Ensured health check is defined before middleware** to avoid interference

### 3. Added Testing Script

Created `python-backend/test_health.py` to test the health endpoint locally before deployment.

## Next Steps

1. **Clean up the failed stack**:

   ```bash
   # Delete ECR images first
   aws ecr batch-delete-image --repository-name noah-backend --region ap-northeast-1 --image-ids imageDigest=sha256:...

   # Delete the failed stack
   aws cloudformation delete-stack --stack-name NoahInfrastructureStack --region ap-northeast-1
   ```

2. **Redeploy with fixes**:

   ```bash
   cd infrastructure
   cdk deploy
   ```

3. **Build and push new backend image**:

   ```bash
   ./scripts/build-and-push.sh
   ```

4. **Monitor health checks**:
   - Check ECS service health in AWS Console
   - Monitor CloudWatch logs for health check requests
   - Verify target group shows healthy targets

## Expected Behavior After Fixes

- ALB health checks should hit `/health` endpoint
- Health checks should return 200 OK with `{"status": "healthy"}`
- ECS service should show healthy targets
- Deployment should complete successfully without rollback

## Monitoring Commands

```bash
# Check target group health
aws elbv2 describe-target-health --target-group-arn <target-group-arn>

# Check ECS service status
aws ecs describe-services --cluster <cluster-name> --services <service-name>

# Check CloudWatch logs
aws logs tail /aws/ecs/noah-backend --follow
```
