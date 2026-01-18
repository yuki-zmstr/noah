// AWS Configuration for Noah Reading Agent
export interface AWSConfig {
  region: string
  userPoolId: string
  userPoolWebClientId: string
  identityPoolId: string
  apiEndpoint: string
}

// Production configuration - detect if we're in production and use production values
const isProduction = window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1'

// Production values (fallback when env vars don't work)
const productionConfig = {
  region: 'ap-northeast-1',
  userPoolId: 'ap-northeast-1_K4gyhxpG9',
  userPoolWebClientId: '14ivj9dtdk1c65t390g1l9vbpc',
  identityPoolId: 'ap-northeast-1:af1ce951-b348-41d1-9a7a-50fceb21efd2',
  apiEndpoint: 'http://NoahIn-NoahB-oKNHtTs5iPix-286806897.ap-northeast-1.elb.amazonaws.com',
}

// Development configuration
const developmentConfig = {
  region: 'us-east-1',
  userPoolId: '',
  userPoolWebClientId: '',
  identityPoolId: '',
  apiEndpoint: 'http://localhost:8000',
}

// Use environment variables if available, otherwise use production/development defaults
export const awsConfig: AWSConfig = {
  region: import.meta.env.VITE_AWS_REGION || (isProduction ? productionConfig.region : developmentConfig.region),
  userPoolId: import.meta.env.VITE_COGNITO_USER_POOL_ID || (isProduction ? productionConfig.userPoolId : developmentConfig.userPoolId),
  userPoolWebClientId: import.meta.env.VITE_COGNITO_CLIENT_ID || (isProduction ? productionConfig.userPoolWebClientId : developmentConfig.userPoolWebClientId),
  identityPoolId: import.meta.env.VITE_COGNITO_IDENTITY_POOL_ID || (isProduction ? productionConfig.identityPoolId : developmentConfig.identityPoolId),
  apiEndpoint: import.meta.env.VITE_API_ENDPOINT || (isProduction ? productionConfig.apiEndpoint : developmentConfig.apiEndpoint),
}

// Debug logging for environment variables
console.log('Environment detection:', {
  hostname: window.location.hostname,
  isProduction,
  envVars: {
    VITE_AWS_REGION: import.meta.env.VITE_AWS_REGION,
    VITE_API_ENDPOINT: import.meta.env.VITE_API_ENDPOINT,
    VITE_COGNITO_USER_POOL_ID: import.meta.env.VITE_COGNITO_USER_POOL_ID,
  },
  NODE_ENV: import.meta.env.NODE_ENV,
  MODE: import.meta.env.MODE
})

console.log('Final awsConfig:', awsConfig)

// Cognito configuration for AWS Amplify
export const cognitoConfig = {
  Auth: {
    region: awsConfig.region,
    userPoolId: awsConfig.userPoolId,
    userPoolWebClientId: awsConfig.userPoolWebClientId,
    identityPoolId: awsConfig.identityPoolId,
    mandatorySignIn: true,
    authenticationFlowType: 'USER_SRP_AUTH',
    oauth: {
      domain: `noah-${awsConfig.userPoolId}.auth.${awsConfig.region}.amazoncognito.com`,
      scope: ['email', 'openid', 'profile'],
      redirectSignIn: window.location.origin,
      redirectSignOut: window.location.origin,
      responseType: 'code',
    },
  },
  API: {
    endpoints: [
      {
        name: 'noah-api',
        endpoint: awsConfig.apiEndpoint,
        region: awsConfig.region,
      },
    ],
  },
}