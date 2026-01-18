# Database Connection Scripts

Quick reference for connecting to the Noah PostgreSQL database.

## 🚀 Quick Start

### Systems Manager (Recommended)

```bash
# One-time setup
./scripts/connect-via-ssm.sh setup

# Create tunnel (keep running)
./scripts/connect-via-ssm.sh tunnel

# Get credentials (in another terminal)
./scripts/get-db-connection.sh
```

### SSH Method

```bash
# One-time setup
./scripts/connect-to-database.sh setup

# Create tunnel (keep running)
./scripts/connect-to-database.sh tunnel

# Get credentials (in another terminal)
./scripts/connect-to-database.sh info
```

## 📋 DBeaver Settings

Once tunnel is running, use these settings in DBeaver:

- **Host:** `localhost`
- **Port:** `5432`
- **Database:** `noah`
- **Username:** `noah_db_admin`
- **Password:** [from get-db-connection.sh output]

## 🔧 Available Scripts

| Script                    | Purpose                              |
| ------------------------- | ------------------------------------ |
| `connect-via-ssm.sh`      | Systems Manager connections (no SSH) |
| `connect-to-database.sh`  | Unified database connection helper   |
| `get-db-connection.sh`    | Retrieve connection details          |
| `setup-bastion-access.sh` | SSH key and bastion setup            |
| `debug-bastion-ssh.sh`    | Troubleshoot SSH issues              |

## 🆘 Troubleshooting

**Connection refused?**

```bash
# Check if tunnel is running
lsof -i :5432

# Restart tunnel
./scripts/connect-via-ssm.sh tunnel
```

**Can't find bastion host?**

```bash
# Redeploy infrastructure
cd infrastructure && npm run deploy
```

**SSH issues?**

```bash
# Debug SSH connectivity
./scripts/debug-bastion-ssh.sh
```

For detailed documentation, see [DATABASE_CONNECTION.md](../DATABASE_CONNECTION.md).
