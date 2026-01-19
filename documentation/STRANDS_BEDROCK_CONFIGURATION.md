# Strands Bedrock Configuration for ap-northeast-1 (Tokyo)

## Problem

The Strands agent service was encountering a ValidationException when trying to use the Claude 3.5 Sonnet v2 model in `ap-northeast-1`:

```
ValidationException: Invocation of model ID anthropic.claude-3-5-sonnet-20241022-v2:0 with on-demand throughput isn't supported. Retry your request with the ID or ARN of an inference profile that contains this model.
```

## Root Cause

- **Claude 3.5 Sonnet v2** (`anthropic.claude-3-5-sonnet-20241022-v2:0`) requires an **inference profile** for on-demand throughput
- **ap-northeast-1** doesn't have the US inference profile (`us.` prefix)
- **Direct model access** works for older Claude versions in Tokyo region

## Solution for ap-northeast-1 (Tokyo)

### Updated Model Configuration

**File: `python-backend/src/config.py`**

```python
# Before
strands_agent_model: str = "anthropic.claude-3-5-sonnet-20241022-v2:0"

# After (for ap-northeast-1)
strands_agent_model: str = "anthropic.claude-3-5-sonnet-20240620-v1:0"
```

**File: `python-backend/src/services/strands_config.py`**

```python
# Before
agent_model: str = Field(default="anthropic.claude-3-5-sonnet-20241022-v2:0", description="Model to use for the agent")

# After (for ap-northeast-1)
agent_model: str = Field(default="anthropic.claude-3-5-sonnet-20240620-v1:0", description="Model to use for the agent")
```

### Why This Works

- **Claude 3.5 Sonnet v1** (`anthropic.claude-3-5-sonnet-20240620-v1:0`) supports direct on-demand access in `ap-northeast-1`
- **No inference profile required** for this model version
- **Available since August 2024** in Tokyo region
- **Same capabilities** as v2 for most use cases

## Model Configuration for ap-northeast-1

### Recommended Configuration

```python
strands_agent_model: str = "anthropic.claude-3-5-sonnet-20240620-v1:0"
```

### Alternative Options

```python
# Faster, cheaper option
strands_agent_model: str = "anthropic.claude-3-haiku-20240307-v1:0"

# If you need Claude 4.5 and have data residency requirements (requires special setup)
strands_agent_model: str = "jp.anthropic.claude-sonnet-4-5-20250929-v1:0"
```

### Model Availability in ap-northeast-1

- ✅ `anthropic.claude-3-5-sonnet-20240620-v1:0` - **Recommended**
- ✅ `anthropic.claude-3-haiku-20240307-v1:0` - Faster/cheaper option
- ❌ `anthropic.claude-3-5-sonnet-20241022-v2:0` - Requires inference profile (not available)
- ⚠️ `jp.anthropic.claude-sonnet-4-5-20250929-v1:0` - Requires Japan CRIS setup

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

## Prerequisites

### 1. Enable Anthropic Models in Bedrock

1. Go to [AWS Console > Bedrock > Model Access](https://console.aws.amazon.com/bedrock/home#/modelaccess)
2. Request access to Anthropic Claude models
3. Wait for approval (usually immediate for Claude 3.5 Sonnet)

### 2. Regional Availability for ap-northeast-1

Claude 3.5 Sonnet v1 is available in `ap-northeast-1` (Tokyo) since August 2024.

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

### Test Commands for ap-northeast-1

```bash
# List available Anthropic models in Tokyo
aws bedrock list-foundation-models --by-provider anthropic --region ap-northeast-1

# Test Claude 3.5 Sonnet v1 access
aws bedrock get-foundation-model --model-identifier "anthropic.claude-3-5-sonnet-20240620-v1:0" --region ap-northeast-1

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

## Troubleshooting for ap-northeast-1

### Common Issues

1. **Model Requires Inference Profile**
   - Error: "on-demand throughput isn't supported"
   - Solution: Use `anthropic.claude-3-5-sonnet-20240620-v1:0` instead of `anthropic.claude-3-5-sonnet-20241022-v2:0`
   - The v2 model requires inference profiles not available in ap-northeast-1

2. **Model Not Available in Region**
   - Check availability: `aws bedrock list-foundation-models --by-provider anthropic --region ap-northeast-1`
   - Request access in Bedrock console for ap-northeast-1 specifically
   - Use Claude 3.5 Sonnet v1 or Claude 3 Haiku as alternatives

3. **Permission Denied**
   - Verify Bedrock permissions are deployed for ap-northeast-1
   - Check ECS task role has correct policies
   - Ensure service has restarted after configuration changes

4. **Wrong Region Configuration**
   - Ensure AWS_REGION is set to ap-northeast-1
   - Verify Bedrock client is using the correct region
   - Check that model access was requested in ap-northeast-1, not other regions

### Debug Commands for ap-northeast-1

```bash
# Check current configuration
curl http://localhost:8000/api/v1/agents/info

# Check service health
curl http://localhost:8000/health

# List available models in Tokyo
aws bedrock list-foundation-models --by-provider anthropic --region ap-northeast-1

# Test Claude 3.5 Sonnet v1 access
aws bedrock get-foundation-model --model-identifier "anthropic.claude-3-5-sonnet-20240620-v1:0" --region ap-northeast-1

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
