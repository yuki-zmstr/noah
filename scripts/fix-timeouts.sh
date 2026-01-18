#!/bin/bash

# Quick fix for local development timeout issues

echo "🔧 Applying timeout fixes for local development..."

# Restart backend with new timeout settings
echo "📦 Restarting backend services..."
cd python-backend

# Kill any existing uvicorn processes
pkill -f uvicorn || echo "No existing uvicorn processes found"

# Start backend with increased timeouts
echo "🚀 Starting backend with timeout fixes..."
python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000 --timeout-keep-alive 300 &

echo "✅ Backend restarted with timeout fixes"

# Check if Docker containers need more resources
echo "🐳 Checking Docker container resources..."
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" | head -5

echo "💡 If containers are using high CPU/memory, consider:"
echo "   - Increasing Docker Desktop memory allocation"
echo "   - Reducing OpenSearch memory: OPENSEARCH_JAVA_OPTS=-Xms256m -Xmx256m"
echo "   - Temporarily disabling Strands agents: STRANDS_ENABLED=false"

echo "✅ Timeout fixes applied!"