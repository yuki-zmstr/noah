# Database Connection Guide

This guide explains how to connect to the Noah Reading Agent PostgreSQL database using DBeaver through AWS Systems Manager Session Manager or SSH tunneling.

## Overview

The Noah application uses an Amazon RDS PostgreSQL database that resides in a private subnet for security. To connect from your local machine, you need to create a secure tunnel through a bastion host.

## Prerequisites

- AWS CLI configured with appropriate permissions
- DBeaver or another PostgreSQL client installed
- Access to the deployed Noah infrastructure

## Method 1: AWS Systems Manager Session Manager (Recommended)

This method is more secure as it doesn't require SSH keys or opening ports.

### Step 1: Install Session Manager Plugin

**On macOS with Homebrew:**

```bash
brew install --cask session-manager-plugin
```

**Manual Installation:**

```bash
curl 'https://s3.amazonaws.com/session-manager-downloads/plugin/latest/mac/sessionmanager-bundle.zip' -o 'sessionmanager-bundle.zip'
unzip sessionmanager-bundle.zip
sudo ./sessionmanager-bundle/install -i /usr/local/sessionmanagerplugin -b /usr/local/bin/session-manager-plugin
```

### Step 2: Verify Setup

```bash
./scripts/connect-via-ssm.sh setup
```

Expected output:

```
✅ Session Manager plugin is installed
✅ Bastion Instance ID: i-xxxxxxxxx
✅ Instance is online and accessible via Systems Manager
```

### Step 3: Create Database Tunnel

In a terminal window that you'll keep open:

```bash
./scripts/connect-via-ssm.sh tunnel
```

You should see:

```
🔗 Creating tunnel: localhost:5432 -> [rds-endpoint]:5432
💡 Keep this terminal open while using DBeaver
🛑 Press Ctrl+C to close tunnel

Starting session with SessionId: root-xxxxx
Port 5432 opened for sessionId root-xxxxx
Waiting for connections...
```

**Important:** Keep this terminal window open while using DBeaver.

### Step 4: Get Database Credentials

In another terminal:

```bash
./scripts/get-db-connection.sh
```

This will output the connection details including the database password.

### Step 5: Configure DBeaver

1. Open DBeaver
2. Create a new connection (Database → New Database Connection)
3. Select PostgreSQL
4. Use these settings:

| Setting      | Value                   |
| ------------ | ----------------------- |
| **Host**     | `localhost`             |
| **Port**     | `5432`                  |
| **Database** | `noah`                  |
| **Username** | `noah_db_admin`         |
| **Password** | [Retrieved from step 4] |

5. Test the connection
6. Save and connect

## Method 2: SSH Tunneling (Alternative)

If you prefer SSH tunneling or Systems Manager is not available.

### Step 1: Deploy Updated Infrastructure

Ensure your infrastructure includes the bastion host with proper SSH configuration:

```bash
cd infrastructure
npm run deploy
```

### Step 2: Set Up SSH Access

```bash
./scripts/setup-bastion-access.sh
```

This will:

- Create an SSH key pair
- Configure the bastion host
- Test connectivity

### Step 3: Create SSH Tunnel

```bash
./scripts/connect-to-database.sh tunnel
```

Or manually:

```bash
ssh -i ~/.ssh/noah-bastion-key.pem -L 5432:[rds-endpoint]:5432 ec2-user@[bastion-ip]
```

### Step 4: Configure DBeaver

Use the same DBeaver settings as Method 1, connecting to `localhost:5432`.

## Helper Scripts Reference

### `connect-via-ssm.sh`

Main script for Systems Manager connections:

```bash
./scripts/connect-via-ssm.sh [action]
```

**Actions:**

- `setup` - Install and test Session Manager plugin
- `tunnel` - Create port forwarding tunnel for DBeaver
- `connect` - Connect to bastion host shell

### `connect-to-database.sh`

Unified script for database connections:

```bash
./scripts/connect-to-database.sh [action]
```

**Actions:**

- `setup` - Set up bastion host and SSH keys
- `tunnel` - Create SSH tunnel (keep running)
- `info` - Show connection details for DBeaver
- `psql` - Connect with psql via tunnel

### `get-db-connection.sh`

Retrieves database connection details:

```bash
./scripts/get-db-connection.sh [stack-name]
```

### `debug-bastion-ssh.sh`

Troubleshoots SSH connectivity issues:

```bash
./scripts/debug-bastion-ssh.sh [stack-name]
```

## Troubleshooting

### Connection Refused

**Problem:** DBeaver shows "Connection refused" to localhost:5432

**Solutions:**

1. Verify the tunnel is running (check terminal output)
2. Ensure no other service is using port 5432 locally:
   ```bash
   lsof -i :5432
   ```
3. Restart the tunnel

### Authentication Failed

**Problem:** Wrong username or password

**Solutions:**

1. Re-run `./scripts/get-db-connection.sh` to get fresh credentials
2. Check AWS Secrets Manager in the console
3. Verify the database user exists

### Tunnel Connection Issues

**Problem:** Cannot establish tunnel to bastion host

**Solutions:**

1. Check bastion host status:
   ```bash
   aws ec2 describe-instances --instance-ids [instance-id] --query 'Reservations[0].Instances[0].State.Name'
   ```
2. Verify Systems Manager connectivity:
   ```bash
   aws ssm describe-instance-information --filters "Key=InstanceIds,Values=[instance-id]"
   ```
3. Check security groups allow the required access

### Instance Not Found

**Problem:** Bastion host not found in CloudFormation outputs

**Solutions:**

1. Redeploy infrastructure:
   ```bash
   cd infrastructure && npm run deploy
   ```
2. Check stack status:
   ```bash
   aws cloudformation describe-stacks --stack-name NoahInfrastructureStack
   ```

## Security Considerations

### Systems Manager (Recommended)

- ✅ No SSH keys to manage
- ✅ No open ports required
- ✅ All traffic encrypted
- ✅ AWS IAM-based access control
- ✅ Session logging available

### SSH Tunneling

- ⚠️ Requires SSH key management
- ⚠️ Port 22 must be open on bastion host
- ✅ Traffic encrypted through SSH
- ⚠️ Key-based authentication

## Database Schema

Once connected, you can explore the Noah database schema:

### Main Tables

- `user_profiles` - User account information
- `conversations` - Chat conversation history
- `content` - Book and content metadata
- `reading_progress` - User reading tracking

### Useful Queries

**List all tables:**

```sql
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public';
```

**Check user profiles:**

```sql
SELECT * FROM user_profiles LIMIT 10;
```

**View recent conversations:**

```sql
SELECT * FROM conversations
ORDER BY created_at DESC
LIMIT 10;
```

## Connection Workflow Summary

### Quick Start (Systems Manager)

1. `./scripts/connect-via-ssm.sh setup` (one time)
2. `./scripts/connect-via-ssm.sh tunnel` (keep running)
3. `./scripts/get-db-connection.sh` (get credentials)
4. Configure DBeaver with localhost:5432
5. Connect and explore!

### Quick Start (SSH)

1. `./scripts/connect-to-database.sh setup` (one time)
2. `./scripts/connect-to-database.sh tunnel` (keep running)
3. `./scripts/connect-to-database.sh info` (get credentials)
4. Configure DBeaver with localhost:5432
5. Connect and explore!

## Additional Resources

- [AWS Systems Manager Session Manager](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager.html)
- [DBeaver Documentation](https://dbeaver.io/docs/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [AWS RDS PostgreSQL](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_PostgreSQL.html)
