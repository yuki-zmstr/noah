# Strands Bedrock Configuration Fix

## Problem

The Strands agent service was configured to use `"gpt-4o-mini"` which is an OpenAI model identifier, but the Strands framework was trying to call AWS Bedrock's `ConverseStream` operation, resulting in the error:

```
ValidationException: The provided model identifier is invalid.
```

## Root Cause

- **Strands agents framework** uses AWS Bedrock for model inference
- **OpenAI model IDs** (like `gpt-4o-mini`) are not valid for AWS Bedrock
- **AWS Bedrock** requires specific model identifiers like `anthropic.claude-3-5-sonnet-20241022-v2:0`

## Solution Applied

### 1. Updated Model Configuration

**File: `python-backend/src/config.py`**

```python
# Before
strands_agent_model: str = "gpt-4o-mini"

# After
strands_agent_model: str = "anthropic.claude-3-5-sonnet-20241022-v2:0"
```

**File: `python-backend/src/services/strands_config.py`**

```python
# Before
agent_model: str = Field(default="gpt-4o-mini", description="Model to use for the agent")

# After
agent_model: str = Field(default="anthropic.claude-3-5-sonnet-20241022-v2:0", description="Model to use for the agent")
```

### 2. Added Bedrock Permissions

**File: `infrastructure/lib/noah-infrastructure-stack.ts`**

Added the following permissions to the ECS task role:

- `bedrock:InvokeModel`
- `bedrock:InvokeModelWithResponseStream`
- `bedrock:Converse`
- `bedrock:ConverseStream`
- `bedrock:ListFoundationModels`
- `bedrock:GetFoundationModel`

### 3. Updated Deployment Scripts

- **`scripts/update-cloudwatch-permissions.sh`** - Now includes Bedrock permissions
- **`scripts/test-bedrock-permissions.sh`** - New script to test Bedrock access

## Model Information

### Claude 3.5 Sonnet

- **Model ID**: `anthropic.claude-3-5-sonnet-20241022-v2:0`
- **Provider**: Anthropic via AWS Bedrock
- **Capabilities**: Advanced reasoning, coding, analysis
- **Context Window**: 200K tokens
- **Streaming**: Supported via ConverseStream

### Alternative Models

If Claude 3.5 Sonnet is not available, you can use:

- `anthropic.claude-3-haiku-20240307-v1:0` (faster, cheaper)
- `anthropic.claude-3-sonnet-20240229-v1:0` (previous version)
- `amazon.nova-pro-v1:0` (Amazon's model)

## Prerequisites

### 1. Enable Anthropic Models in Bedrock

1. Go to [AWS Console > Bedrock > Model Access](https://console.aws.amazon.com/bedrock/home#/modelaccess)
2. Request access to Anthropic Claude models
3. Wait for approval (usually immediate for Claude 3.5 Sonnet)

### 2. Regional Availability

Claude 3.5 Sonnet is available in:

- `us-east-1` (N. Virginia)
- `us-west-2` (Oregon)
- `eu-west-1` (Ireland)
- `ap-southeast-2` (Sydney)

## Deployment Steps

1. **Deploy Infrastructure Updates**:

   ```bash
   ./scripts/update-cloudwatch-permissions.sh
   ```

2. **Wait for Service Restart** (2-3 minutes)

3. **Test Bedrock Access**:

   ```bash
   ./scripts/test-bedrock-permissions.sh
   ```

4. **Verify Logs**: Check that Strands agent errors are resolved

## Verification

### Success Indicators

- No more "ValidationException" errors in logs
- Strands agent service starts successfully
- Chat streaming works with Bedrock models

### Test Commands

```bash
# List available Anthropic models
aws bedrock list-foundation-models --by-provider anthropic

# Test specific model access
aws bedrock get-foundation-model --model-identifier "anthropic.claude-3-5-sonnet-20241022-v2:0"

# Check ECS service status
aws ecs describe-services --cluster NoahInfrastructureStack-NoahCluster* --services NoahInfrastructureStack-NoahBackendService*
```

## Architecture Notes

### Service Separation

- **OpenAI Services**: `ai_response_service.py`, `enhanced_intent_service.py` - Use OpenAI directly
- **Strands Services**: `strands_agent_service.py` - Use AWS Bedrock via Strands framework
- **Both can coexist** with different model providers

### Cost Considerations

- **Claude 3.5 Sonnet**: ~$3 per 1M input tokens, ~$15 per 1M output tokens
- **Claude 3 Haiku**: ~$0.25 per 1M input tokens, ~$1.25 per 1M output tokens
- **OpenAI GPT-4o-mini**: ~$0.15 per 1M input tokens, ~$0.60 per 1M output tokens

## Troubleshooting

### Common Issues

1. **Model Not Available**
   - Check regional availability
   - Request access in Bedrock console
   - Try alternative model ID

2. **Permission Denied**
   - Verify Bedrock permissions are deployed
   - Check ECS task role has correct policies
   - Ensure service has restarted

3. **Still Getting OpenAI Errors**
   - Check environment variables don't override config
   - Verify correct model ID in all config files
   - Restart application after changes

### Debug Commands

```bash
# Check current configuration
curl http://localhost:8000/api/v1/agents/info

# Check service health
curl http://localhost:8000/health

# View recent logs
aws logs tail /aws/ecs/noah-backend --follow
```

## Future Considerations

### Model Updates

- Monitor for new Claude model releases
- Update model IDs when newer versions are available
- Test performance and cost implications

### Multi-Model Strategy

- Consider using different models for different tasks
- Implement model fallback mechanisms
- Monitor usage and costs across providers
