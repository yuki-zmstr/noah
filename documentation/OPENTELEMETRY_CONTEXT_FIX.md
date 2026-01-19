# OpenTelemetry Context Error Fix

## Problem

The backend was experiencing OpenTelemetry context errors when using Strands agents:

```
ValueError: <Token var=<ContextVar name='current_context' default={} at 0x10c23f5b0> at 0x10ee7f940> was created in a different Context
```

This error occurs when async generators are interrupted or when context tokens are used across different async contexts, which is common with streaming operations.

## Root Cause

1. **OpenTelemetry Context Management** - The Strands library uses OpenTelemetry for tracing, which creates context tokens
2. **Async Generator Interruption** - When streaming is interrupted (client disconnect, error, etc.), the context tokens become invalid
3. **Context Cleanup Issues** - Improper cleanup of async generators leads to context token errors

## Solution Implemented

### 1. OpenTelemetry Configuration (`src/telemetry_config.py`)

- **Disabled OpenTelemetry by default** to avoid context issues
- **Added configuration options** to enable/disable telemetry
- **Suppressed telemetry warnings** that don't affect functionality

### 2. Enhanced Stream Context Management (`strands_agent_service.py`)

- **Added async context manager** for safe stream handling
- **Proper generator cleanup** with try/finally blocks
- **Graceful error handling** for GeneratorExit and CancelledError
- **Fallback mechanisms** when streaming fails

### 3. Robust Error Handling

- **Context-aware exception handling** for different error types
- **Logging improvements** to track streaming issues
- **Graceful degradation** to AI response service if Strands fails

### 4. Configuration Updates

- **Added OpenTelemetry settings** in config.py
- **Updated .env file** with telemetry configuration
- **Early telemetry import** in main.py to configure before other imports

## Key Changes

### Backend Files Modified:

1. `src/telemetry_config.py` - New telemetry configuration module
2. `src/config.py` - Added OpenTelemetry settings
3. `src/main.py` - Early telemetry configuration import
4. `src/services/strands_agent_service.py` - Enhanced stream context management
5. `src/services/enhanced_conversation_service.py` - Added fallback mechanisms
6. `.env` - Added telemetry configuration

### Configuration Changes:

```env
# OpenTelemetry Configuration (disabled to avoid context issues)
OPENTELEMETRY_ENABLED=false
OPENTELEMETRY_SERVICE_NAME=noah-reading-agent
```

## Testing

Created `test_strands_streaming.py` to verify the fix works correctly.

## Expected Results

- ✅ No more OpenTelemetry context errors
- ✅ Graceful handling of stream interruptions
- ✅ Proper cleanup of async generators
- ✅ Fallback to AI response service if Strands fails
- ✅ Maintained streaming functionality
- ✅ Reduced error logging noise

## Monitoring

- OpenTelemetry context warnings are suppressed
- Strands streaming errors are logged at appropriate levels
- Fallback mechanisms are logged for debugging
- Stream cleanup is handled gracefully

## Future Considerations

- Can re-enable OpenTelemetry if needed by setting `OPENTELEMETRY_ENABLED=true`
- Monitor for any remaining context issues
- Consider upgrading Strands library if newer versions fix context handling
- Implement custom telemetry if needed without OpenTelemetry
