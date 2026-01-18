"""Monitoring middleware for FastAPI application."""

import time
import logging
import uuid
from typing import Callable, Optional
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from src.services.monitoring_service import monitoring_service, AlertLevel, MetricType
from src.services.logging_config import performance_logger


class MonitoringMiddleware(BaseHTTPMiddleware):
    """Middleware for comprehensive request monitoring and logging."""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.logger = logging.getLogger(__name__)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with monitoring."""
        # Generate request ID for tracing
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Extract user information if available
        user_id = self._extract_user_id(request)
        
        # Start timing
        start_time = time.time()
        
        # Log request start
        self.logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.query_params),
                "user_agent": request.headers.get("user-agent"),
                "client_ip": self._get_client_ip(request),
                "user_id": user_id
            }
        )
        
        # Track request start
        monitoring_service.record_metric(
            name="HTTP.Requests",
            value=1,
            dimensions={
                "Method": request.method,
                "Path": self._normalize_path(request.url.path),
                "UserAgent": self._normalize_user_agent(request.headers.get("user-agent", "unknown"))
            }
        )
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Log successful response
            self.logger.info(
                f"Request completed: {request.method} {request.url.path}",
                extra={
                    "request_id": request_id,
                    "status_code": response.status_code,
                    "duration_ms": duration_ms,
                    "user_id": user_id
                }
            )
            
            # Track response metrics
            self._track_response_metrics(request, response, duration_ms, user_id)
            
            # Log performance data
            performance_logger.log_api_request(
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=duration_ms,
                user_id=user_id
            )
            
            # Add response headers for tracing
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            # Calculate duration for error case
            duration_ms = (time.time() - start_time) * 1000
            
            # Log error
            self.logger.error(
                f"Request failed: {request.method} {request.url.path}",
                extra={
                    "request_id": request_id,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "duration_ms": duration_ms,
                    "user_id": user_id
                },
                exc_info=True
            )
            
            # Track error metrics
            monitoring_service.record_metric(
                name="HTTP.Errors",
                value=1,
                dimensions={
                    "Method": request.method,
                    "Path": self._normalize_path(request.url.path),
                    "ErrorType": type(e).__name__
                }
            )
            
            # Create alert for server errors
            monitoring_service.create_alert(
                name="HTTPError",
                level=AlertLevel.ERROR,
                message=f"HTTP request failed: {request.method} {request.url.path} - {str(e)}",
                metadata={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "error_type": type(e).__name__,
                    "user_id": user_id
                }
            )
            
            # Return error response
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal server error",
                    "request_id": request_id
                },
                headers={"X-Request-ID": request_id}
            )
    
    def _extract_user_id(self, request: Request) -> Optional[str]:
        """Extract user ID from request if available."""
        # Try to get from JWT token or session
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            # In a real implementation, you'd decode the JWT token
            # For now, we'll just return a placeholder
            return "authenticated_user"
        
        # Try to get from query params or headers
        user_id = request.query_params.get("user_id")
        if not user_id:
            user_id = request.headers.get("x-user-id")
        
        return user_id
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address, considering load balancer headers."""
        # Check for forwarded headers (from load balancer)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fallback to direct client IP
        if request.client:
            return request.client.host
        
        return "unknown"
    
    def _normalize_path(self, path: str) -> str:
        """Normalize path for metrics (remove IDs and sensitive data)."""
        # Replace UUIDs and numeric IDs with placeholders
        import re
        
        # Replace UUIDs
        path = re.sub(
            r'/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',
            '/{uuid}',
            path,
            flags=re.IGNORECASE
        )
        
        # Replace numeric IDs
        path = re.sub(r'/\d+', '/{id}', path)
        
        return path
    
    def _normalize_user_agent(self, user_agent: str) -> str:
        """Normalize user agent for metrics."""
        if not user_agent:
            return "unknown"
        
        # Extract browser/client type
        user_agent_lower = user_agent.lower()
        
        if "chrome" in user_agent_lower:
            return "chrome"
        elif "firefox" in user_agent_lower:
            return "firefox"
        elif "safari" in user_agent_lower:
            return "safari"
        elif "edge" in user_agent_lower:
            return "edge"
        elif "postman" in user_agent_lower:
            return "postman"
        elif "curl" in user_agent_lower:
            return "curl"
        elif "python" in user_agent_lower:
            return "python"
        else:
            return "other"
    
    def _track_response_metrics(
        self,
        request: Request,
        response: Response,
        duration_ms: float,
        user_id: Optional[str]
    ):
        """Track detailed response metrics."""
        path_normalized = self._normalize_path(request.url.path)
        
        # Track response time
        monitoring_service.record_metric(
            name="HTTP.ResponseTime",
            value=duration_ms,
            unit="Milliseconds",
            dimensions={
                "Method": request.method,
                "Path": path_normalized,
                "StatusCode": str(response.status_code)
            },
            metric_type=MetricType.TIMER
        )
        
        # Track status codes
        monitoring_service.record_metric(
            name="HTTP.StatusCodes",
            value=1,
            dimensions={
                "Method": request.method,
                "Path": path_normalized,
                "StatusCode": str(response.status_code),
                "StatusClass": f"{response.status_code // 100}xx"
            }
        )
        
        # Alert on slow requests
        if duration_ms > 5000:  # 5 seconds
            monitoring_service.create_alert(
                name="SlowHTTPRequest",
                level=AlertLevel.WARNING,
                message=f"Slow HTTP request: {request.method} {request.url.path} took {duration_ms:.2f}ms",
                metadata={
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": duration_ms,
                    "user_id": user_id
                }
            )
        
        # Alert on client errors (4xx)
        if 400 <= response.status_code < 500:
            monitoring_service.record_metric(
                name="HTTP.ClientErrors",
                value=1,
                dimensions={
                    "Method": request.method,
                    "Path": path_normalized,
                    "StatusCode": str(response.status_code)
                }
            )
        
        # Alert on server errors (5xx)
        elif response.status_code >= 500:
            monitoring_service.record_metric(
                name="HTTP.ServerErrors",
                value=1,
                dimensions={
                    "Method": request.method,
                    "Path": path_normalized,
                    "StatusCode": str(response.status_code)
                }
            )
            
            monitoring_service.create_alert(
                name="HTTPServerError",
                level=AlertLevel.ERROR,
                message=f"HTTP server error: {request.method} {request.url.path} returned {response.status_code}",
                metadata={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "user_id": user_id
                }
            )