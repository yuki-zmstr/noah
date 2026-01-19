# Noah Reading Agent - AWS Architecture

## Overview

Noah Reading Agent is a cloud-native, personalized reading assistant built on AWS. The system uses a microservices architecture with containerized backend services, managed databases, and a globally distributed frontend. The architecture is designed for scalability, reliability, and cost-effectiveness.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                 Internet                                        │
└─────────────────────────────────┬───────────────────────────────────────────────┘
                                  │
┌─────────────────────────────────┴───────────────────────────────────────────────┐
│                            CloudFront CDN                                      │
│  ┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐ │
│  │   Static Assets     │    │    API Routes       │    │   WebSocket/SSE     │ │
│  │   (S3 Origin)       │    │   (ALB Origin)      │    │   (ALB Origin)      │ │
│  └─────────────────────┘    └─────────────────────┘    └─────────────────────┘ │
└─────────────────────────────┬───────────────────────────────────────────────────┘
                              │
┌─────────────────────────────┴───────────────────────────────────────────────────┐
│                              AWS Amplify                                       │
│                         (Frontend Deployment)                                  │
└─────────────────────────────┬───────────────────────────────────────────────────┘
                              │
┌─────────────────────────────┴───────────────────────────────────────────────────┐
│                              VPC (Multi-AZ)                                    │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                        Public Subnets                                  │   │
│  │  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐     │   │
│  │  │  Application    │    │   Bastion Host  │    │   NAT Gateway   │     │   │
│  │  │ Load Balancer   │    │   (Database     │    │                 │     │   │
│  │  │                 │    │    Access)      │    │                 │     │   │
│  │  └─────────────────┘    └─────────────────┘    └─────────────────┘     │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                       Private Subnets                                  │   │
│  │  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐     │   │
│  │  │   ECS Fargate   │    │   RDS PostgreSQL│    │   Future:       │     │   │
│  │  │   (Backend)     │    │   (User Data)   │    │   OpenSearch    │     │   │
│  │  │                 │    │                 │    │   (Vector DB)   │     │   │
│  │  └─────────────────┘    └─────────────────┘    └─────────────────┘     │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                           External Services                                     │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐             │
│  │  Amazon Bedrock │    │  Amazon Cognito │    │   Pinecone      │             │
│  │  (AI Models)    │    │  (Authentication│    │  (Vector DB)    │             │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘             │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Frontend Layer

#### AWS Amplify

- **Purpose**: Hosts the Vue.js frontend application
- **Features**:
  - Automatic builds from Git repository
  - Global CDN distribution
  - Custom domain support
  - Environment-specific deployments
- **Configuration**: Defined in `amplify.yml`

#### CloudFront Distribution

- **Purpose**: Global content delivery and API routing
- **Origins**:
  - S3 bucket for static assets (HTML, CSS, JS)
  - Application Load Balancer for API routes
- **Behaviors**:
  - `/api/*` → Backend ALB
  - `/health` → Backend ALB
  - `/ws/*` → Backend ALB (WebSocket/SSE)
  - Static files → S3 with aggressive caching
- **Security**: Custom security headers, CORS configuration

### 2. Application Layer

#### Amazon ECS with Fargate

- **Service**: `NoahBackendService`
- **Configuration**:
  - CPU: 512 units (0.5 vCPU)
  - Memory: 1024 MiB (1 GB)
  - Desired count: 1 (can be scaled)
- **Container**: Python FastAPI application
- **Health Checks**: `/health` endpoint with 30s intervals
- **Logging**: CloudWatch Logs with 7-day retention

#### Application Load Balancer (ALB)

- **Purpose**: Routes traffic to ECS tasks
- **Health Checks**: Monitors backend service health
- **Integration**: CloudFront origin for API traffic

### 3. Data Layer

#### Amazon RDS PostgreSQL

- **Engine**: PostgreSQL 15
- **Instance**: t3.micro (development) - scalable for production
- **Storage**: 20GB encrypted EBS
- **Networking**: Private subnets only
- **Access**: Via bastion host or ECS tasks
- **Backups**: Automated with point-in-time recovery

#### Vector Database (Pinecone)

- **Purpose**: Stores content embeddings for semantic search
- **Integration**: External service accessed via API
- **Use Cases**: Book recommendations, content similarity

#### Future: Amazon OpenSearch

- **Status**: Commented out in infrastructure code
- **Purpose**: Full-text search and analytics
- **Planned Features**: Content indexing, search analytics

### 4. Authentication & Authorization

#### Amazon Cognito

- **User Pool**: Manages user registration and authentication
- **Identity Pool**: Provides AWS resource access
- **Features**:
  - Email-based sign-up
  - Password policies
  - OAuth 2.0 flows
  - JWT token management
- **Integration**: Frontend uses AWS Amplify Auth

### 5. AI/ML Services

#### Amazon Bedrock

- **Models**: Anthropic Claude 3.5 Sonnet
- **Features**:
  - Streaming responses
  - Conversation memory
  - Content generation
- **Configuration**: Strands agent integration
- **Permissions**: ECS task role has Bedrock access

### 6. Monitoring & Observability

#### CloudWatch

- **Metrics**: ECS service metrics, RDS metrics
- **Alarms**: CPU, memory, database connections
- **Logs**: Application logs with structured logging
- **Dashboards**: Custom monitoring dashboards

#### Application Monitoring

- **Health Checks**: Multi-level health monitoring
- **Performance Metrics**: Request latency, error rates
- **Custom Metrics**: Business logic metrics

### 7. Security

#### Network Security

- **VPC**: Isolated network environment
- **Subnets**: Public/private subnet separation
- **Security Groups**: Restrictive ingress/egress rules
- **NAT Gateway**: Outbound internet access for private resources

#### Access Control

- **IAM Roles**: Least privilege access
- **Secrets Manager**: Database credentials, API keys
- **Bastion Host**: Secure database access for administration

#### Data Security

- **Encryption**: At-rest and in-transit encryption
- **HTTPS**: End-to-end encrypted communication
- **CORS**: Configured for secure cross-origin requests

## Deployment Architecture

### Infrastructure as Code

- **Tool**: AWS CDK (TypeScript)
- **Stack**: `NoahInfrastructureStack`
- **Resources**: ~20 AWS resources defined in code
- **Environments**: Development and production configurations

### CI/CD Pipeline

- **Platform**: GitHub Actions
- **Triggers**: Push to main branch, manual dispatch
- **Stages**:
  1. Infrastructure deployment (CDK)
  2. Backend container build and push (ECR)
  3. Database migrations (ECS task)
  4. Service updates (ECS)
  5. Verification and rollback capabilities

### Container Registry

- **Service**: Amazon ECR
- **Repository**: `noah-backend`
- **Features**: Image scanning, tag mutability
- **Integration**: Automated builds in CI/CD

## Data Flow

### User Authentication Flow

1. User accesses frontend via CloudFront
2. Amplify serves static assets
3. User authenticates via Cognito
4. JWT tokens stored in browser
5. API requests include authentication headers

### API Request Flow

1. Frontend makes API request
2. CloudFront routes to ALB
3. ALB forwards to ECS task
4. FastAPI processes request
5. Database queries via RDS
6. AI processing via Bedrock
7. Response returned through reverse path

### Real-time Communication

1. Frontend establishes SSE connection
2. CloudFront maintains persistent connection
3. Backend streams responses
4. Real-time updates delivered to client

## Scalability Considerations

### Horizontal Scaling

- **ECS Service**: Auto-scaling based on CPU/memory
- **RDS**: Read replicas for read-heavy workloads
- **CloudFront**: Global edge locations

### Vertical Scaling

- **ECS Tasks**: Configurable CPU/memory allocation
- **RDS Instance**: Upgradeable instance types
- **Load Balancer**: Automatic capacity management

### Cost Optimization

- **Fargate**: Pay-per-use compute
- **RDS**: Right-sized instances
- **CloudFront**: Optimized caching strategies
- **S3**: Intelligent tiering for static assets

## Disaster Recovery

### Backup Strategy

- **RDS**: Automated backups with 7-day retention
- **Code**: Git repository with multiple branches
- **Infrastructure**: CDK templates in version control

### High Availability

- **Multi-AZ**: RDS deployment across availability zones
- **ECS**: Tasks distributed across AZs
- **CloudFront**: Global distribution with failover

### Recovery Procedures

- **Database**: Point-in-time recovery
- **Application**: Blue-green deployments
- **Infrastructure**: CDK stack recreation

## Environment Configuration

### Development

- **Database**: Docker Compose PostgreSQL
- **Backend**: Local Python server
- **Frontend**: Vite development server
- **AI Services**: AWS Bedrock (shared)

### Production

- **All services**: AWS managed services
- **Domain**: Custom domain via Route 53
- **SSL**: AWS Certificate Manager
- **Monitoring**: Full CloudWatch integration

## Security Best Practices

### Network Security

- Private subnets for sensitive resources
- Security groups with minimal required access
- VPC Flow Logs for network monitoring

### Application Security

- JWT token validation
- Input sanitization and validation
- Rate limiting and DDoS protection

### Data Protection

- Encryption at rest and in transit
- Secrets management via AWS Secrets Manager
- Regular security updates and patches

## Future Enhancements

### Planned Additions

- **OpenSearch**: Full-text search capabilities
- **ElastiCache**: Redis caching layer
- **Lambda**: Serverless background processing
- **EventBridge**: Event-driven architecture

### Scalability Improvements

- **Auto Scaling**: Dynamic capacity management
- **CDN Optimization**: Advanced caching strategies
- **Database Optimization**: Query performance tuning
- **Microservices**: Service decomposition

This architecture provides a robust, scalable foundation for the Noah Reading Agent while maintaining cost-effectiveness and operational simplicity.
