# Proxy Headers Configuration

## Overview

The Noah Reading Agent backend now includes ProxyHeadersMiddleware to properly handle forwarded headers from the Application Load Balancer (ALB) and CloudFront distribution.

## What ProxyHeadersMiddleware Does

ProxyHeadersMiddleware processes the following headers from trusted proxies:

- `X-Forwarded-For`: Client IP addresses
- `X-Forwarded-Proto`: Original protocol (http/https)
- `X-Forwarded-Host`: Original host header
- `X-Forwarded-Port`: Original port

## Configuration

### Environment Variables

- `PROXY_HEADERS_ENABLED`: Enable/disable proxy headers middleware (default: true)
- `TRUSTED_HOSTS`: Comma-separated list of trusted proxy hosts (default: "\*")

### Production Considerations

In production, consider restricting `TRUSTED_HOSTS` to specific IP ranges:

```
TRUSTED_HOSTS=10.0.0.0/8,172.16.0.0/12,192.168.0.0/16
```

## Middleware Order

The middleware is applied in this order:

1. ProxyHeadersMiddleware (handles forwarded headers)
2. MonitoringMiddleware (tracks requests)
3. CORSMiddleware (handles CORS)

## Debug Endpoint

When `DEBUG=true`, you can check proxy headers at:

```
GET /api/debug/headers
```

This endpoint returns:

- All request headers
- Client IP information
- Forwarded header values
- CloudFront-specific headers

## AWS Infrastructure

The infrastructure automatically configures:

- ALB with health checks on `/health`
- CloudFront distribution with proper origin settings
- Environment variables for proxy configuration

## Testing

To test proxy headers locally:

```bash
curl -H "X-Forwarded-For: 203.0.113.1" \
     -H "X-Forwarded-Proto: https" \
     -H "X-Forwarded-Host: example.com" \
     http://localhost:8000/api/debug/headers
```

## Security Notes

- ProxyHeadersMiddleware only processes headers from trusted hosts
- In production, restrict trusted hosts to your actual proxy infrastructure
- The middleware prevents header spoofing from untrusted sources
