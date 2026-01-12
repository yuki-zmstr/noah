# Environment Variables Setup Guide

This guide explains all the environment variables needed for the Noah Reading Agent and how to obtain them.

## Quick Start for Development

For local development, you can start with minimal configuration:

1. Copy the example file:

   ```bash
   cp .env.example .env
   cp frontend/.env.example frontend/.env
   ```

2. **Required for basic functionality:**

   - Generate JWT secrets (see Security section below)
   - The database URLs are pre-configured for Docker development setup

3. **Optional for enhanced features:**
   - AWS credentials for Bedrock Agent
   - Amazon Product API for purchase links
   - Google Search API for web search links

## Environment Variables Breakdown

### 🔧 Application Configuration

```bash
NODE_ENV=development          # Environment: development, staging, production
PORT=8000                    # Backend server port
FRONTEND_URL=http://localhost:3000  # Frontend URL for CORS
```

**How to set:**

- `NODE_ENV`: Set to `development` for local, `production` for deployment
- `PORT`: Use `8000` for development, or any available port
- `FRONTEND_URL`: Your frontend URL (localhost:3000 for development)

### 🗄️ Database Configuration

```bash
DATABASE_URL=postgresql://noah_user:noah_password@localhost:5432/noah_dev
REDIS_URL=redis://localhost:6379
```

**For Development (using Docker):**

- These are pre-configured for the Docker Compose setup
- No changes needed if using the provided `docker-compose.yml`

**For Production:**

- `DATABASE_URL`: Get from your PostgreSQL provider (AWS RDS, Heroku Postgres, etc.)
- `REDIS_URL`: Get from your Redis provider (AWS ElastiCache, Redis Cloud, etc.)

### 🔍 OpenSearch Configuration

```bash
OPENSEARCH_ENDPOINT=http://localhost:9200
OPENSEARCH_USERNAME=          # Optional for development
OPENSEARCH_PASSWORD=          # Optional for development
```

**For Development:**

- Pre-configured for Docker setup with security disabled
- Leave username/password empty

**For Production:**

- Get from AWS OpenSearch Service or self-hosted OpenSearch
- Enable authentication and set credentials

### ☁️ AWS Configuration

```bash
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
```

**How to get AWS credentials:**

1. **Create AWS Account:** [aws.amazon.com](https://aws.amazon.com)

2. **Create IAM User:**

   - Go to AWS Console → IAM → Users → Create User
   - Attach policies: `AmazonBedrockFullAccess`, `AmazonS3FullAccess`
   - Create access key in Security Credentials tab

3. **Or use AWS CLI:**
   ```bash
   aws configure
   # Enter your access key, secret key, and region
   ```

### 🤖 AWS Bedrock Agent Configuration

```bash
BEDROCK_AGENT_ID=your-agent-id
BEDROCK_AGENT_ALIAS_ID=your-alias-id
BEDROCK_KNOWLEDGE_BASE_ID=your-kb-id
```

**How to get Bedrock Agent credentials:**

1. **Enable Bedrock in AWS Console:**

   - Go to AWS Bedrock service
   - Request access to Claude/other models if needed

2. **Create Bedrock Agent:**

   - Go to Bedrock → Agents → Create Agent
   - Configure with your instructions and knowledge base
   - Note the Agent ID and Alias ID

3. **Create Knowledge Base (optional):**
   - Go to Bedrock → Knowledge Bases → Create
   - Upload your content documents
   - Note the Knowledge Base ID

**For Development:**

- You can leave these empty initially
- The system will work without Bedrock (with limited AI features)

### 🛒 Amazon Product API (for Purchase Links)

```bash
AMAZON_PRODUCT_API_KEY=your-api-key
AMAZON_ASSOCIATE_TAG=your-associate-tag
```

**How to get Amazon Product API access:**

1. **Join Amazon Associates Program:**

   - Go to [associates.amazon.com](https://associates.amazon.com)
   - Create account and get approved
   - Note your Associate Tag (e.g., `yoursite-20`)

2. **Get Product Advertising API Access:**
   - Go to [webservices.amazon.com](https://webservices.amazon.com/paapi5/documentation/)
   - Request API access (requires active Associate account)
   - Get your Access Key and Secret Key

**For Development:**

- You can leave these empty
- Purchase links will fall back to web search

### 🔍 Google Search API (for Web Search Links)

```bash
GOOGLE_SEARCH_API_KEY=your-api-key
GOOGLE_SEARCH_ENGINE_ID=your-engine-id
```

**How to get Google Search API access:**

1. **Create Google Cloud Project:**

   - Go to [console.cloud.google.com](https://console.cloud.google.com)
   - Create new project or select existing

2. **Enable Custom Search API:**

   - Go to APIs & Services → Library
   - Search for "Custom Search API" and enable it

3. **Create API Key:**

   - Go to APIs & Services → Credentials
   - Create API Key and restrict it to Custom Search API

4. **Create Custom Search Engine:**
   - Go to [cse.google.com](https://cse.google.com)
   - Create new search engine
   - Set to search the entire web
   - Note the Search Engine ID

**For Development:**

- You can leave these empty
- Web search features will be disabled

### 🔐 Security Configuration

```bash
JWT_SECRET=your-jwt-secret-here
SESSION_SECRET=your-session-secret-here
```

**How to generate secure secrets:**

```bash
# Generate random secrets (run these commands)
node -e "console.log(require('crypto').randomBytes(64).toString('hex'))"
node -e "console.log(require('crypto').randomBytes(64).toString('hex'))"
```

Or use online generators:

- [randomkeygen.com](https://randomkeygen.com)
- Generate 64-character random strings

**⚠️ Important:** Use different secrets for each environment!

### 📝 Logging Configuration

```bash
LOG_LEVEL=info    # Options: error, warn, info, debug
```

**Recommended levels:**

- Development: `debug` or `info`
- Production: `warn` or `error`

### ⚙️ Content Processing Configuration

```bash
MAX_CONTENT_SIZE=10485760        # 10MB in bytes
SUPPORTED_LANGUAGES=english,japanese
```

**How to configure:**

- `MAX_CONTENT_SIZE`: Maximum file size for content uploads
- `SUPPORTED_LANGUAGES`: Comma-separated list of supported languages

### 🚦 Rate Limiting Configuration

```bash
RATE_LIMIT_WINDOW_MS=900000      # 15 minutes in milliseconds
RATE_LIMIT_MAX_REQUESTS=100      # Max requests per window
```

**Recommended settings:**

- Development: Higher limits for testing
- Production: Conservative limits to prevent abuse

## Frontend Environment Variables

In `frontend/.env`:

```bash
VITE_API_BASE_URL=http://localhost:8000/api
VITE_SOCKET_URL=http://localhost:8000
VITE_ENABLE_DISCOVERY_MODE=true
VITE_ENABLE_MULTILINGUAL=true
VITE_ENABLE_PURCHASE_LINKS=true
VITE_DEFAULT_LANGUAGE=english
VITE_MAX_MESSAGE_LENGTH=2000
VITE_TYPING_INDICATOR_DELAY=1000
```

**Configuration:**

- Update URLs to match your backend deployment
- Enable/disable features based on your API availability
- Adjust UI settings as needed

## Environment-Specific Configurations

### Development Environment

```bash
NODE_ENV=development
DATABASE_URL=postgresql://noah_user:noah_password@localhost:5432/noah_dev
REDIS_URL=redis://localhost:6379
OPENSEARCH_ENDPOINT=http://localhost:9200
LOG_LEVEL=debug
```

### Production Environment

```bash
NODE_ENV=production
DATABASE_URL=postgresql://user:pass@prod-db-host:5432/noah_prod
REDIS_URL=redis://prod-redis-host:6379
OPENSEARCH_ENDPOINT=https://prod-opensearch-host:443
OPENSEARCH_USERNAME=admin
OPENSEARCH_PASSWORD=secure-password
LOG_LEVEL=warn
```

## Security Best Practices

1. **Never commit .env files to version control**
2. **Use different secrets for each environment**
3. **Rotate secrets regularly in production**
4. **Use AWS IAM roles instead of access keys when possible**
5. **Restrict API keys to minimum required permissions**
6. **Use environment-specific configurations**

## Troubleshooting

### Common Issues

1. **Database connection errors:**

   - Ensure Docker containers are running: `docker compose ps`
   - Check DATABASE_URL format and credentials

2. **AWS Bedrock access denied:**

   - Verify IAM permissions include Bedrock access
   - Check if model access is requested and approved

3. **Amazon API errors:**

   - Verify Associate account is active
   - Check API key permissions and rate limits

4. **Google Search API errors:**
   - Verify API is enabled in Google Cloud Console
   - Check API key restrictions and quotas

### Testing Configuration

Test your configuration with these commands:

```bash
# Test database connection
docker compose exec postgres psql -U noah_user -d noah_dev -c "SELECT 1;"

# Test Redis connection
docker compose exec redis redis-cli ping

# Test OpenSearch connection
curl http://localhost:9200/_cluster/health

# Test backend startup
cd backend && npm run dev
```

## Getting Help

If you need help with any of these services:

- **AWS Support:** [aws.amazon.com/support](https://aws.amazon.com/support)
- **Amazon Associates:** [affiliate-program.amazon.com/help](https://affiliate-program.amazon.com/help)
- **Google Cloud Support:** [cloud.google.com/support](https://cloud.google.com/support)
- **Project Issues:** Create an issue in the project repository

## Minimal Setup for Testing

If you just want to test the basic functionality without external APIs:

```bash
# Required (generate these)
JWT_SECRET=your-generated-secret-here
SESSION_SECRET=your-other-generated-secret-here

# Pre-configured for Docker
NODE_ENV=development
PORT=8000
FRONTEND_URL=http://localhost:3000
DATABASE_URL=postgresql://noah_user:noah_password@localhost:5432/noah_dev
REDIS_URL=redis://localhost:6379
OPENSEARCH_ENDPOINT=http://localhost:9200

# Optional (leave empty for basic testing)
BEDROCK_AGENT_ID=
AMAZON_PRODUCT_API_KEY=
GOOGLE_SEARCH_API_KEY=
```

This minimal setup will allow you to:

- ✅ Run the chat interface
- ✅ Store user conversations
- ✅ Basic content processing
- ❌ AI-powered responses (needs Bedrock)
- ❌ Purchase links (needs Amazon API)
- ❌ Web search (needs Google API)
