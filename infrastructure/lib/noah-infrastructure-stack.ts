import * as cdk from 'aws-cdk-lib'
import * as ec2 from 'aws-cdk-lib/aws-ec2'
import * as rds from 'aws-cdk-lib/aws-rds'
import * as ecs from 'aws-cdk-lib/aws-ecs'
import * as ecsPatterns from 'aws-cdk-lib/aws-ecs-patterns'
import * as opensearch from 'aws-cdk-lib/aws-opensearchservice'
import * as s3 from 'aws-cdk-lib/aws-s3'
import * as cloudfront from 'aws-cdk-lib/aws-cloudfront'
import * as origins from 'aws-cdk-lib/aws-cloudfront-origins'
import * as cognito from 'aws-cdk-lib/aws-cognito'
import * as iam from 'aws-cdk-lib/aws-iam'
import * as logs from 'aws-cdk-lib/aws-logs'
import * as cloudwatch from 'aws-cdk-lib/aws-cloudwatch'
import * as ecr from 'aws-cdk-lib/aws-ecr'
import * as bedrock from 'aws-cdk-lib/aws-bedrock'
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager'
import { Construct } from 'constructs'

export class NoahInfrastructureStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props)

    // VPC for all resources
    const vpc = new ec2.Vpc(this, 'NoahVpc', {
      maxAzs: 2,
      natGateways: 1,
    })

    // Amazon Cognito User Pool for authentication
    const userPool = new cognito.UserPool(this, 'NoahUserPool', {
      userPoolName: 'noah-user-pool',
      selfSignUpEnabled: true,
      signInAliases: {
        email: true,
      },
      autoVerify: {
        email: true,
      },
      standardAttributes: {
        email: {
          required: true,
          mutable: true,
        },
        givenName: {
          required: false,
          mutable: true,
        },
        familyName: {
          required: false,
          mutable: true,
        },
      },
      passwordPolicy: {
        minLength: 8,
        requireLowercase: true,
        requireUppercase: true,
        requireDigits: true,
        requireSymbols: true,
      },
      accountRecovery: cognito.AccountRecovery.EMAIL_ONLY,
      removalPolicy: cdk.RemovalPolicy.DESTROY, // For development - change to RETAIN for production
    })

    // Cognito User Pool Client
    const userPoolClient = new cognito.UserPoolClient(this, 'NoahUserPoolClient', {
      userPool,
      userPoolClientName: 'noah-web-client',
      generateSecret: false, // For web applications
      authFlows: {
        userPassword: true,
        userSrp: true,
      },
      oAuth: {
        flows: {
          authorizationCodeGrant: true,
        },
        scopes: [
          cognito.OAuthScope.EMAIL,
          cognito.OAuthScope.OPENID,
          cognito.OAuthScope.PROFILE,
        ],
        callbackUrls: [
          'http://localhost:5173', // Development
          'https://localhost:5173', // Development with HTTPS
        ],
        logoutUrls: [
          'http://localhost:5173', // Development
          'https://localhost:5173', // Development with HTTPS
        ],
      },
      preventUserExistenceErrors: true,
      refreshTokenValidity: cdk.Duration.days(30),
      accessTokenValidity: cdk.Duration.hours(1),
      idTokenValidity: cdk.Duration.hours(1),
    })

    // Cognito Identity Pool for AWS resource access
    const identityPool = new cognito.CfnIdentityPool(this, 'NoahIdentityPool', {
      identityPoolName: 'noah-identity-pool',
      allowUnauthenticatedIdentities: false,
      cognitoIdentityProviders: [
        {
          clientId: userPoolClient.userPoolClientId,
          providerName: userPool.userPoolProviderName,
        },
      ],
    })

    // Note: Amplify will be configured manually through the AWS Console
    // See DEPLOYMENT.md for instructions

    // ECR Repository for backend Docker images
    const ecrRepository = new ecr.Repository(this, 'NoahBackendRepository', {
      repositoryName: 'noah-backend',
      imageScanOnPush: true,
      imageTagMutability: ecr.TagMutability.MUTABLE,
      removalPolicy: cdk.RemovalPolicy.DESTROY, // For development - change to RETAIN for production
    })

    // PostgreSQL Database for user profiles
    const database = new rds.DatabaseInstance(this, 'NoahDatabase', {
      engine: rds.DatabaseInstanceEngine.postgres({
        version: rds.PostgresEngineVersion.VER_15,
      }),
      instanceType: ec2.InstanceType.of(ec2.InstanceClass.T3, ec2.InstanceSize.MICRO),
      vpc,
      credentials: rds.Credentials.fromGeneratedSecret('noah_db_admin'),
      multiAz: false,
      allocatedStorage: 20,
      storageEncrypted: true,
      deletionProtection: false,
      databaseName: 'noah',
    })

    // Note: OpenSearch will be added later - commenting out for initial deployment
    // const searchDomain = new opensearch.Domain(this, 'NoahSearchDomain', {
    //   version: opensearch.EngineVersion.OPENSEARCH_2_9,
    //   capacity: {
    //     dataNodes: 1,
    //     dataNodeInstanceType: 't3.small.search',
    //   },
    //   ebs: {
    //     volumeSize: 20,
    //     volumeType: ec2.EbsDeviceVolumeType.GP3,
    //   },
    //   vpc,
    //   vpcSubnets: [
    //     {
    //       subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS,
    //       availabilityZones: [vpc.availabilityZones[0]], // Use only first AZ
    //     }
    //   ],
    //   zoneAwareness: {
    //     enabled: false,
    //   },
    //   logging: {
    //     slowSearchLogEnabled: true,
    //     appLogEnabled: true,
    //     slowIndexLogEnabled: true,
    //   },
    // })

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
        image: ecs.ContainerImage.fromEcrRepository(ecrRepository, 'latest'),
        containerPort: 8000,
        environment: {
          NODE_ENV: 'production',
          DATABASE_HOST: database.instanceEndpoint.hostname,
          DATABASE_PORT: '5432',
          DATABASE_NAME: 'noah',
          DATABASE_USER: 'noah_db_admin',
          OPENSEARCH_ENDPOINT: 'disabled-for-initial-deployment',
          COGNITO_USER_POOL_ID: userPool.userPoolId,
          COGNITO_CLIENT_ID: userPoolClient.userPoolClientId,
          COGNITO_REGION: this.region,
          AWS_DEFAULT_REGION: this.region,
          CORS_ORIGINS: 'http://localhost:5173,https://localhost:5173',
        },
        secrets: {
          DATABASE_PASSWORD: ecs.Secret.fromSecretsManager(database.secret!, 'password'),
          PINECONE_API_KEY: ecs.Secret.fromSecretsManager(secretsmanager.Secret.fromSecretNameV2(this, 'PineconeSecret', 'pinecone/api-key')),
          OPENAI_API_KEY: ecs.Secret.fromSecretsManager(secretsmanager.Secret.fromSecretNameV2(this, 'OpenAISecret', 'openai/api-key')),
        },
        logDriver: ecs.LogDrivers.awsLogs({
          streamPrefix: 'noah-backend',
          logRetention: 7, // 7 days retention
        }),
      },
      publicLoadBalancer: true,
      listenerPort: 80,
      healthCheckGracePeriod: cdk.Duration.seconds(60),
    })

    // Allow backend to access database
    database.connections.allowFrom(backendService.service, ec2.Port.tcp(5432))

    // Allow backend to access OpenSearch (commented out for initial deployment)
    // searchDomain.connections.allowFrom(backendService.service, ec2.Port.tcp(443))

    // CloudWatch Log Group for application logs
    const appLogGroup = new logs.LogGroup(this, 'NoahAppLogGroup', {
      logGroupName: '/aws/ecs/noah-backend',
      retention: logs.RetentionDays.ONE_WEEK,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    })

    // CloudWatch Alarms for monitoring
    const cpuAlarm = new cloudwatch.Alarm(this, 'NoahBackendCpuAlarm', {
      metric: backendService.service.metricCpuUtilization(),
      threshold: 80,
      evaluationPeriods: 2,
      treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING,
    })

    const memoryAlarm = new cloudwatch.Alarm(this, 'NoahBackendMemoryAlarm', {
      metric: backendService.service.metricMemoryUtilization(),
      threshold: 80,
      evaluationPeriods: 2,
      treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING,
    })

    // Database monitoring
    const dbCpuAlarm = new cloudwatch.Alarm(this, 'NoahDatabaseCpuAlarm', {
      metric: database.metricCPUUtilization(),
      threshold: 80,
      evaluationPeriods: 2,
      treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING,
    })

    const dbConnectionsAlarm = new cloudwatch.Alarm(this, 'NoahDatabaseConnectionsAlarm', {
      metric: database.metricDatabaseConnections(),
      threshold: 80,
      evaluationPeriods: 2,
      treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING,
    })

    // Add branches will be configured manually in Amplify Console
    // Update Cognito callback URLs to include Amplify URLs manually after Amplify setup

    // S3 bucket for static assets and content storage
    const contentBucket = new s3.Bucket(this, 'NoahContentBucket', {
      versioned: true,
      encryption: s3.BucketEncryption.S3_MANAGED,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      removalPolicy: cdk.RemovalPolicy.DESTROY, // For development - change to RETAIN for production
    })

    // S3 bucket for frontend static files
    const frontendBucket = new s3.Bucket(this, 'NoahFrontendBucket', {
      websiteIndexDocument: 'index.html',
      websiteErrorDocument: 'index.html',
      publicReadAccess: true,
      blockPublicAccess: new s3.BlockPublicAccess({
        blockPublicAcls: false,
        blockPublicPolicy: false,
        ignorePublicAcls: false,
        restrictPublicBuckets: false,
      }),
      removalPolicy: cdk.RemovalPolicy.DESTROY, // For development - change to RETAIN for production
    })

    // CloudFront distribution for frontend
    const distribution = new cloudfront.Distribution(this, 'NoahDistribution', {
      defaultBehavior: {
        origin: new origins.S3Origin(frontendBucket),
        viewerProtocolPolicy: cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
        cachePolicy: cloudfront.CachePolicy.CACHING_OPTIMIZED,
        originRequestPolicy: cloudfront.OriginRequestPolicy.CORS_S3_ORIGIN,
        responseHeadersPolicy: new cloudfront.ResponseHeadersPolicy(this, 'NoahSecurityHeaders', {
          securityHeadersBehavior: {
            contentTypeOptions: { override: true },
            frameOptions: { frameOption: cloudfront.HeadersFrameOption.DENY, override: true },
            referrerPolicy: { referrerPolicy: cloudfront.HeadersReferrerPolicy.STRICT_ORIGIN_WHEN_CROSS_ORIGIN, override: true },
            strictTransportSecurity: { 
              accessControlMaxAge: cdk.Duration.seconds(31536000), 
              includeSubdomains: true, 
              preload: true, 
              override: true 
            },
            xssProtection: { protection: true, modeBlock: true, override: true },
          },
          corsBehavior: {
            accessControlAllowCredentials: false,
            accessControlAllowHeaders: ['*'],
            accessControlAllowMethods: ['GET', 'HEAD', 'OPTIONS', 'PUT', 'POST', 'PATCH', 'DELETE'],
            accessControlAllowOrigins: ['*'],
            accessControlMaxAge: cdk.Duration.seconds(86400),
            originOverride: true,
          },
        }),
      },
      additionalBehaviors: {
        '/api/*': {
          origin: new origins.LoadBalancerV2Origin(backendService.loadBalancer, {
            protocolPolicy: cloudfront.OriginProtocolPolicy.HTTP_ONLY,
          }),
          allowedMethods: cloudfront.AllowedMethods.ALLOW_ALL,
          cachePolicy: cloudfront.CachePolicy.CACHING_DISABLED,
          originRequestPolicy: cloudfront.OriginRequestPolicy.ALL_VIEWER,
          viewerProtocolPolicy: cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
        },
        '/ws/*': {
          origin: new origins.LoadBalancerV2Origin(backendService.loadBalancer, {
            protocolPolicy: cloudfront.OriginProtocolPolicy.HTTP_ONLY,
          }),
          allowedMethods: cloudfront.AllowedMethods.ALLOW_ALL,
          cachePolicy: cloudfront.CachePolicy.CACHING_DISABLED,
          originRequestPolicy: cloudfront.OriginRequestPolicy.ALL_VIEWER,
          viewerProtocolPolicy: cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
        },
        '*.js': {
          origin: new origins.S3Origin(frontendBucket),
          viewerProtocolPolicy: cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
          cachePolicy: new cloudfront.CachePolicy(this, 'NoahJSCachePolicy', {
            cachePolicyName: 'noah-js-cache-policy',
            defaultTtl: cdk.Duration.days(1),
            maxTtl: cdk.Duration.days(365),
            minTtl: cdk.Duration.seconds(0),
            headerBehavior: cloudfront.CacheHeaderBehavior.none(),
            queryStringBehavior: cloudfront.CacheQueryStringBehavior.none(),
            cookieBehavior: cloudfront.CacheCookieBehavior.none(),
          }),
        },
        '*.css': {
          origin: new origins.S3Origin(frontendBucket),
          viewerProtocolPolicy: cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
          cachePolicy: new cloudfront.CachePolicy(this, 'NoahCSSCachePolicy', {
            cachePolicyName: 'noah-css-cache-policy',
            defaultTtl: cdk.Duration.days(1),
            maxTtl: cdk.Duration.days(365),
            minTtl: cdk.Duration.seconds(0),
            headerBehavior: cloudfront.CacheHeaderBehavior.none(),
            queryStringBehavior: cloudfront.CacheQueryStringBehavior.none(),
            cookieBehavior: cloudfront.CacheCookieBehavior.none(),
          }),
        },
      },
      defaultRootObject: 'index.html',
      errorResponses: [
        {
          httpStatus: 404,
          responseHttpStatus: 200,
          responsePagePath: '/index.html',
          ttl: cdk.Duration.minutes(5),
        },
        {
          httpStatus: 403,
          responseHttpStatus: 200,
          responsePagePath: '/index.html',
          ttl: cdk.Duration.minutes(5),
        },
        {
          httpStatus: 500,
          responseHttpStatus: 500,
          responsePagePath: '/error.html',
          ttl: cdk.Duration.minutes(1),
        },
      ],
      priceClass: cloudfront.PriceClass.PRICE_CLASS_100, // Use only North America and Europe edge locations
      enableIpv6: true,
      comment: 'Noah Reading Agent CloudFront Distribution',
    })

    // Outputs
    new cdk.CfnOutput(this, 'UserPoolId', {
      value: userPool.userPoolId,
      description: 'Cognito User Pool ID',
    })

    new cdk.CfnOutput(this, 'UserPoolClientId', {
      value: userPoolClient.userPoolClientId,
      description: 'Cognito User Pool Client ID',
    })

    new cdk.CfnOutput(this, 'IdentityPoolId', {
      value: identityPool.ref,
      description: 'Cognito Identity Pool ID',
    })

    new cdk.CfnOutput(this, 'DatabaseEndpoint', {
      value: database.instanceEndpoint.hostname,
      description: 'PostgreSQL database endpoint',
    })

    // new cdk.CfnOutput(this, 'OpenSearchEndpoint', {
    //   value: searchDomain.domainEndpoint,
    //   description: 'OpenSearch domain endpoint',
    // })

    new cdk.CfnOutput(this, 'BackendUrl', {
      value: backendService.loadBalancer.loadBalancerDnsName,
      description: 'Backend service URL',
    })

    new cdk.CfnOutput(this, 'FrontendUrl', {
      value: distribution.distributionDomainName,
      description: 'Frontend CloudFront URL',
    })

    new cdk.CfnOutput(this, 'CloudFrontDistributionId', {
      value: distribution.distributionId,
      description: 'CloudFront Distribution ID',
    })

    new cdk.CfnOutput(this, 'ContentBucketName', {
      value: contentBucket.bucketName,
      description: 'S3 bucket for content storage',
    })

    new cdk.CfnOutput(this, 'EcrRepositoryUri', {
      value: ecrRepository.repositoryUri,
      description: 'ECR Repository URI for backend images',
    })
  }
}