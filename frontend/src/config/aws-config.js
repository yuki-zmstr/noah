// Development configuration - these will be replaced by environment variables in production
export const awsConfig = {
    region: import.meta.env.VITE_AWS_REGION || 'us-east-1',
    userPoolId: import.meta.env.VITE_COGNITO_USER_POOL_ID || '',
    userPoolWebClientId: import.meta.env.VITE_COGNITO_CLIENT_ID || '',
    identityPoolId: import.meta.env.VITE_COGNITO_IDENTITY_POOL_ID || '',
    apiEndpoint: import.meta.env.VITE_API_ENDPOINT || 'http://localhost:8000',
};
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
};
