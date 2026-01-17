export interface AWSConfig {
    region: string;
    userPoolId: string;
    userPoolWebClientId: string;
    identityPoolId: string;
    apiEndpoint: string;
}
export declare const awsConfig: AWSConfig;
export declare const cognitoConfig: {
    Auth: {
        region: string;
        userPoolId: string;
        userPoolWebClientId: string;
        identityPoolId: string;
        mandatorySignIn: boolean;
        authenticationFlowType: string;
        oauth: {
            domain: string;
            scope: string[];
            redirectSignIn: string;
            redirectSignOut: string;
            responseType: string;
        };
    };
    API: {
        endpoints: {
            name: string;
            endpoint: string;
            region: string;
        }[];
    };
};
