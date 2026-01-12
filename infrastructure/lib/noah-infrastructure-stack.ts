import * as cdk from 'aws-cdk-lib'
import * as ec2 from 'aws-cdk-lib/aws-ec2'
import * as rds from 'aws-cdk-lib/aws-rds'
import * as ecs from 'aws-cdk-lib/aws-ecs'
import * as ecsPatterns from 'aws-cdk-lib/aws-ecs-patterns'
import * as opensearch from 'aws-cdk-lib/aws-opensearchservice'
import * as s3 from 'aws-cdk-lib/aws-s3'
import * as cloudfront from 'aws-cdk-lib/aws-cloudfront'
import * as origins from 'aws-cdk-lib/aws-cloudfront-origins'
import * as bedrock from 'aws-cdk-lib/aws-bedrock'
import { Construct } from 'constructs'

export class NoahInfrastructureStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props)

    // VPC for all resources
    const vpc = new ec2.Vpc(this, 'NoahVpc', {
      maxAzs: 2,
      natGateways: 1,
    })

    // PostgreSQL Database for user profiles
    const database = new rds.DatabaseInstance(this, 'NoahDatabase', {
      engine: rds.DatabaseInstanceEngine.postgres({
        version: rds.PostgresEngineVersion.VER_15_4,
      }),
      instanceType: ec2.InstanceType.of(ec2.InstanceClass.T3, ec2.InstanceSize.MICRO),
      vpc,
      credentials: rds.Credentials.fromGeneratedSecret('noah-db-admin'),
      multiAz: false,
      allocatedStorage: 20,
      storageEncrypted: true,
      deletionProtection: false,
      databaseName: 'noah',
    })

    // OpenSearch for vector similarity search
    const searchDomain = new opensearch.Domain(this, 'NoahSearchDomain', {
      version: opensearch.EngineVersion.OPENSEARCH_2_9,
      capacity: {
        dataNodes: 1,
        dataNodeInstanceType: 't3.small.search',
      },
      ebs: {
        volumeSize: 20,
        volumeType: ec2.EbsDeviceVolumeType.GP3,
      },
      vpc,
      zoneAwareness: {
        enabled: false,
      },
      logging: {
        slowSearchLogEnabled: true,
        appLogEnabled: true,
        slowIndexLogEnabled: true,
      },
    })

    // ECS Cluster for backend services
    const cluster = new ecs.Cluster(this, 'NoahCluster', {
      vpc,
      containerInsights: true,
    })

    // Backend service with Fargate
    const backendService = new ecsPatterns.ApplicationLoadBalancedFargateService(this, 'NoahBackendService', {
      cluster,
      cpu: 512,
      memoryLimitMiB: 1024,
      desiredCount: 1,
      taskImageOptions: {
        image: ecs.ContainerImage.fromRegistry('nginx'), // Placeholder - will be replaced with actual backend image
        containerPort: 8000,
        environment: {
          NODE_ENV: 'production',
          DATABASE_URL: `postgresql://noah-db-admin:${database.secret?.secretValueFromJson('password')}@${database.instanceEndpoint.hostname}:5432/noah`,
          OPENSEARCH_ENDPOINT: searchDomain.domainEndpoint,
        },
      },
      publicLoadBalancer: true,
    })

    // Allow backend to access database
    database.connections.allowFrom(backendService.service, ec2.Port.tcp(5432))

    // Allow backend to access OpenSearch
    searchDomain.connections.allowFrom(backendService.service, ec2.Port.tcp(443))

    // S3 bucket for static assets and content storage
    const contentBucket = new s3.Bucket(this, 'NoahContentBucket', {
      bucketName: `noah-content-${this.account}-${this.region}`,
      versioned: true,
      encryption: s3.BucketEncryption.S3_MANAGED,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
    })

    // S3 bucket for frontend static files
    const frontendBucket = new s3.Bucket(this, 'NoahFrontendBucket', {
      bucketName: `noah-frontend-${this.account}-${this.region}`,
      websiteIndexDocument: 'index.html',
      websiteErrorDocument: 'index.html',
      publicReadAccess: true,
      blockPublicAccess: new s3.BlockPublicAccess({
        blockPublicAcls: false,
        blockPublicPolicy: false,
        ignorePublicAcls: false,
        restrictPublicBuckets: false,
      }),
    })

    // CloudFront distribution for frontend
    const distribution = new cloudfront.Distribution(this, 'NoahDistribution', {
      defaultBehavior: {
        origin: new origins.S3Origin(frontendBucket),
        viewerProtocolPolicy: cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
      },
      additionalBehaviors: {
        '/api/*': {
          origin: new origins.LoadBalancerV2Origin(backendService.loadBalancer, {
            protocolPolicy: cloudfront.OriginProtocolPolicy.HTTP_ONLY,
          }),
          allowedMethods: cloudfront.AllowedMethods.ALLOW_ALL,
          cachePolicy: cloudfront.CachePolicy.CACHING_DISABLED,
        },
      },
      defaultRootObject: 'index.html',
      errorResponses: [
        {
          httpStatus: 404,
          responseHttpStatus: 200,
          responsePagePath: '/index.html',
        },
      ],
    })

    // Outputs
    new cdk.CfnOutput(this, 'DatabaseEndpoint', {
      value: database.instanceEndpoint.hostname,
      description: 'PostgreSQL database endpoint',
    })

    new cdk.CfnOutput(this, 'OpenSearchEndpoint', {
      value: searchDomain.domainEndpoint,
      description: 'OpenSearch domain endpoint',
    })

    new cdk.CfnOutput(this, 'BackendUrl', {
      value: backendService.loadBalancer.loadBalancerDnsName,
      description: 'Backend service URL',
    })

    new cdk.CfnOutput(this, 'FrontendUrl', {
      value: distribution.distributionDomainName,
      description: 'Frontend CloudFront URL',
    })

    new cdk.CfnOutput(this, 'ContentBucketName', {
      value: contentBucket.bucketName,
      description: 'S3 bucket for content storage',
    })
  }
}