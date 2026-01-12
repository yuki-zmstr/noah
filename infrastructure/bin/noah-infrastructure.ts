#!/usr/bin/env node
import 'source-map-support/register'
import * as cdk from 'aws-cdk-lib'
import { NoahInfrastructureStack } from '../lib/noah-infrastructure-stack'

const app = new cdk.App()

new NoahInfrastructureStack(app, 'NoahInfrastructureStack', {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION || 'us-east-1',
  },
})