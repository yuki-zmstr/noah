# Database Migrations Guide

This document explains how database migrations work in the Noah Reading Agent project and how they're handled during deployment.

## Overview

The project uses Alembic for database schema migrations. **Migrations are run in GitHub Actions before deploying the application**, ensuring the database is updated before the new code is deployed.

## Migration Strategy

### ✅ **GitHub Actions Migration Approach**

**Why this approach:**

- ✅ **Separation of Concerns**: Migrations run separately from app deployment
- ✅ **Better Control**: Explicit migration step with proper error handling
- ✅ **Cleaner Containers**: App containers only contain app code
- ✅ **Easier Debugging**: Migration logs are clearly visible in GitHub Actions
- ✅ **Rollback Safety**: Can rollback migrations independently of app deployment

**How it works:**

1. **Migration Step**: GitHub Actions connects to RDS and runs `alembic upgrade head`
2. **Build Step**: Docker image is built (without migration code)
3. **Deploy Step**: New image is deployed to ECS
4. **Verify Step**: Health checks confirm everything is working

## Migration Files

Migration files are located in `python-backend/alembic/versions/` and include:

1. **70e2f3202201_initial_migration.py** - Creates all initial tables
2. **a8abefa4ec5f_remove_purchase_links_table.py** - Removes purchase_links table
3. **6a1b012c8e7c_remove_purchase_links_from_messages.py** - Removes purchase_links column from messages
4. **7d8e9f1a2b3c_align_local_schema_with_models.py** - Aligns local schema with current models

## Database Schema

The current database schema includes these tables:

- `user_profiles` - User preferences and reading levels
- `content_items` - Books and articles content
- `conversation_sessions` - Chat sessions
- `conversation_messages` - Individual messages
- `conversation_histories` - Conversation summaries
- `reading_behaviors` - Reading tracking data
- `preference_snapshots` - Preference evolution tracking
- `discovery_recommendations` - Discovery mode recommendations

## Local Development

### Running Migrations Locally

```bash
cd python-backend

# Check current migration status
uv run alembic current

# View migration history
uv run alembic history

# Run all pending migrations
uv run alembic upgrade head

# Rollback one migration
uv run alembic downgrade -1
```

### Creating New Migrations

```bash
cd python-backend

# Auto-generate migration from model changes
uv run alembic revision --autogenerate -m "description_of_changes"

# Create empty migration file
uv run alembic revision -m "description_of_changes"
```

### Database Reset (Development Only)

If you need to reset your local database:

```bash
# Stop containers
docker-compose down

# Remove database volume
docker volume rm noah_postgres_data

# Start containers (will create fresh database)
docker-compose up -d

# Run migrations
cd python-backend
uv run alembic upgrade head
```

## Production Deployment

### Automatic Migration in GitHub Actions

Migrations are automatically run in GitHub Actions **before** deploying the application:

**Deployment Flow:**

1. **Migration Phase**: GitHub Actions connects to RDS and runs migrations
2. **Build Phase**: Docker image is built (clean, no migration code)
3. **Deploy Phase**: New image is deployed to ECS
4. **Verify Phase**: Health checks confirm deployment success

**Migration Process:**

- GitHub Actions runner connects directly to RDS using AWS credentials
- Database credentials are retrieved from AWS Secrets Manager
- `alembic upgrade head` is executed to apply all pending migrations
- Only if migrations succeed, the deployment continues
- If migrations fail, the entire deployment is aborted

### Deployment Scripts

#### Deploy with GitHub Actions

```bash
git push origin main  # Triggers automatic deployment with migrations
```

The GitHub Actions workflow will:

- Run database migrations first
- Build and push Docker image
- Deploy to ECS
- Verify deployment success

#### Manual Migration Check

```bash
./scripts/check-migration-status.sh
```

This script connects to the RDS database and shows:

- Current migration version
- Available tables
- Migration history

### Manual Migration Check

To manually check migration status on production:

1. **Connect via Bastion Host**:

   ```bash
   # Get bastion instance ID from CloudFormation outputs
   aws ssm start-session --target i-1234567890abcdef0
   ```

2. **Install PostgreSQL Client**:

   ```bash
   sudo yum install -y postgresql
   ```

3. **Connect to Database**:

   ```bash
   # Get credentials from AWS Secrets Manager
   PGPASSWORD='your_password' psql -h your-db-endpoint -U noah_db_admin -d noah
   ```

4. **Check Migration Status**:

   ```sql
   -- Current migration version
   SELECT * FROM alembic_version;

   -- Available tables
   \dt

   -- Table structure
   \d+ table_name
   ```

## Migration Best Practices

### Development

- Always create migrations for schema changes
- Test migrations on a copy of production data
- Review auto-generated migrations before committing
- Use descriptive migration messages

### Production

- Migrations run automatically during deployment
- Monitor ECS logs during deployment to ensure migrations succeed
- Have a rollback plan for complex migrations
- Test migrations in staging environment first

### Schema Changes

- **Adding Columns**: Safe, can be done online
- **Removing Columns**: Requires careful planning, may need multiple deployments
- **Renaming Tables/Columns**: Use multiple migrations for zero-downtime
- **Data Migrations**: Consider performance impact on large tables

## Troubleshooting

### Migration Fails During Deployment

1. **Check ECS Logs**:

   ```bash
   aws logs tail /ecs/noah-backend --follow --region ap-northeast-1
   ```

2. **Connect to Database Manually**:

   ```bash
   ./scripts/check-migration-status.sh
   ```

3. **Rollback if Necessary**:
   ```bash
   # Connect to bastion host and run:
   PGPASSWORD='password' psql -h endpoint -U user -d noah
   # Then manually fix or rollback
   ```

### Local Database Out of Sync

1. **Check Current Status**:

   ```bash
   cd python-backend
   uv run alembic current
   uv run alembic history
   ```

2. **Reset Database** (if safe):

   ```bash
   docker-compose down
   docker volume rm noah_postgres_data
   docker-compose up -d
   cd python-backend
   uv run alembic upgrade head
   ```

3. **Manual Sync** (if data must be preserved):

   ```bash
   # Stamp database with current version
   uv run alembic stamp head

   # Then run any new migrations
   uv run alembic upgrade head
   ```

## Monitoring

### ECS Service Logs

Monitor the ECS service logs to see migration execution:

```bash
aws logs tail /ecs/noah-backend --follow --region ap-northeast-1
```

### CloudWatch Metrics

- Monitor ECS service health
- Check database connection metrics
- Set up alarms for deployment failures

### Health Checks

The application includes a health endpoint that verifies:

- Database connectivity
- Migration status
- Service readiness

Access at: `https://your-domain/health`

## Files and Configuration

### Key Files

- `python-backend/migrate_and_start.py` - Migration and startup script
- `python-backend/alembic.ini` - Alembic configuration
- `python-backend/alembic/env.py` - Alembic environment setup
- `python-backend/alembic/versions/` - Migration files
- `python-backend/src/models/` - SQLAlchemy models

### Environment Variables

- `DATABASE_URL` - Complete database connection string
- `DATABASE_HOST`, `DATABASE_PORT`, `DATABASE_NAME`, `DATABASE_USER`, `DATABASE_PASSWORD` - Individual components
- `DEBUG` - Enables verbose logging for migrations

### Docker Configuration

The Dockerfile includes:

- Migration script execution on startup
- Proper error handling
- Logging configuration

This ensures that every deployment automatically applies the latest database schema changes.

## GitHub Actions Integration

### ✅ **Migration Integration Complete**

Your GitHub Actions `deploy.yml` now runs database migrations **before** deploying the application. Here's the improved workflow:

### 🔄 **New Deployment Flow**

1. **Migration Phase**: GitHub Actions connects to RDS and runs `alembic upgrade head`
2. **Build Phase**: Docker image is built (clean, no migration code)
3. **Deploy Phase**: ECS service updated with new image
4. **Verification Phase**: Health checks confirm deployment success

### 📋 **What's Included in deploy.yml**

- ✅ **Dedicated Migration Step**: Runs before building Docker image
- ✅ **AWS Secrets Integration**: Automatically retrieves RDS credentials
- ✅ **Migration Verification**: Confirms migrations completed successfully
- ✅ **Failure Handling**: Deployment aborts if migrations fail
- ✅ **Clean Separation**: App containers only contain app code

### 🛠️ **Key Advantages**

**Better Architecture:**

- Migrations run separately from app deployment
- Cleaner Docker containers (no migration code)
- Easier debugging and monitoring
- Independent rollback capabilities

**Enhanced Safety:**

- Migrations must succeed before deployment continues
- Clear failure points and error messages
- No risk of multiple containers running migrations
- Proper credential management through AWS Secrets

**Improved Monitoring:**

- Migration logs clearly visible in GitHub Actions
- Separate migration and deployment status
- Better error reporting and troubleshooting

### 🚀 **Usage**

**Deploy with Migrations:**

```bash
git push origin main  # Triggers automatic deployment with migrations
```

**What You'll See in GitHub Actions:**

- 🗄️ "Running database migrations..."
- 📋 "Checking current migration status..."
- 🚀 "Running migrations..."
- ✅ "Database migrations completed successfully!"
- 🔨 "Building Docker image..."
- 📝 "Updating ECS service..."
- ✅ "Deployment successful!"

The deployment will automatically fail if migrations don't complete successfully, ensuring your database is always in a consistent state.

## Summary

The migration system now runs in GitHub Actions **before** deployment, providing better separation of concerns, cleaner containers, and more reliable deployments. Your RDS database will stay in sync with your models during every deployment.
