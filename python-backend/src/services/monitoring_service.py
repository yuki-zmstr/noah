"""Comprehensive monitoring and logging service for Noah Reading Agent."""

import logging
import time
import json
import boto3
import asyncio
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from contextlib import contextmanager
from functools import wraps
from dataclasses import dataclass, asdict
from enum import Enum

from src.config import settings

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of metrics we track."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


class AlertLevel(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class Metric:
    """Represents a custom metric."""
    name: str
    value: Union[int, float]
    unit: str
    timestamp: datetime
    dimensions: Dict[str, str]
    metric_type: MetricType


@dataclass
class Alert:
    """Represents an alert condition."""
    name: str
    level: AlertLevel
    message: str
    timestamp: datetime
    metadata: Dict[str, Any]


class MonitoringService:
    """Service for comprehensive application monitoring and logging."""

    def __init__(self):
        """Initialize monitoring service."""
        self.cloudwatch = None
        self.metrics_buffer: List[Metric] = []
        self.alerts_buffer: List[Alert] = []
        self.performance_data: Dict[str, List[float]] = {}
        
        # Initialize CloudWatch client if in AWS environment
        try:
            if settings.aws_region:
                self.cloudwatch = boto3.client('cloudwatch', region_name=settings.aws_region)
                logger.info("CloudWatch client initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize CloudWatch client: {e}")
            logger.info("Monitoring will use local logging only")

    def record_metric(
        self,
        name: str,
        value: Union[int, float],
        unit: str = "Count",
        dimensions: Optional[Dict[str, str]] = None,
        metric_type: MetricType = MetricType.COUNTER
    ):
        """Record a custom metric."""
        metric = Metric(
            name=name,
            value=value,
            unit=unit,
            timestamp=datetime.utcnow(),
            dimensions=dimensions or {},
            metric_type=metric_type
        )
        
        self.metrics_buffer.append(metric)
        
        # Log locally
        logger.info(f"Metric recorded: {name}={value} {unit} {dimensions}")
        
        # Send to CloudWatch if available
        if self.cloudwatch:
            try:
                self._send_metric_to_cloudwatch(metric)
            except Exception as e:
                logger.error(f"Failed to send metric to CloudWatch: {e}")

    def _send_metric_to_cloudwatch(self, metric: Metric):
        """Send metric to CloudWatch."""
        metric_data = {
            'MetricName': metric.name,
            'Value': metric.value,
            'Unit': metric.unit,
            'Timestamp': metric.timestamp
        }
        
        if metric.dimensions:
            metric_data['Dimensions'] = [
                {'Name': k, 'Value': v} for k, v in metric.dimensions.items()
            ]
        
        self.cloudwatch.put_metric_data(
            Namespace='Noah/ReadingAgent',
            MetricData=[metric_data]
        )

    def create_alert(
        self,
        name: str,
        level: AlertLevel,
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Create an alert."""
        alert = Alert(
            name=name,
            level=level,
            message=message,
            timestamp=datetime.utcnow(),
            metadata=metadata or {}
        )
        
        self.alerts_buffer.append(alert)
        
        # Log alert based on severity
        log_level = {
            AlertLevel.INFO: logging.INFO,
            AlertLevel.WARNING: logging.WARNING,
            AlertLevel.ERROR: logging.ERROR,
            AlertLevel.CRITICAL: logging.CRITICAL
        }[level]
        
        logger.log(log_level, f"ALERT [{level.value.upper()}] {name}: {message}")
        
        # Send to CloudWatch Logs if available
        if self.cloudwatch:
            try:
                self._send_alert_to_cloudwatch(alert)
            except Exception as e:
                logger.error(f"Failed to send alert to CloudWatch: {e}")

    def _send_alert_to_cloudwatch(self, alert: Alert):
        """Send alert to CloudWatch Logs."""
        # This would typically use CloudWatch Logs client
        # For now, we'll use the metrics client to create a custom metric
        self.record_metric(
            name=f"Alert.{alert.name}",
            value=1,
            dimensions={
                "Level": alert.level.value,
                "AlertName": alert.name
            }
        )

    @contextmanager
    def timer(self, operation_name: str, dimensions: Optional[Dict[str, str]] = None):
        """Context manager for timing operations."""
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            self.record_metric(
                name=f"Operation.Duration",
                value=duration * 1000,  # Convert to milliseconds
                unit="Milliseconds",
                dimensions={
                    "Operation": operation_name,
                    **(dimensions or {})
                },
                metric_type=MetricType.TIMER
            )
            
            # Track performance data for analysis
            if operation_name not in self.performance_data:
                self.performance_data[operation_name] = []
            self.performance_data[operation_name].append(duration)

    def performance_decorator(self, operation_name: str):
        """Decorator for automatic performance monitoring."""
        def decorator(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                with self.timer(operation_name):
                    return await func(*args, **kwargs)
            
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                with self.timer(operation_name):
                    return func(*args, **kwargs)
            
            return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
        return decorator

    def track_user_engagement(
        self,
        user_id: str,
        action: str,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Track user engagement metrics."""
        dimensions = {
            "Action": action,
            "UserId": user_id[:8] + "..." if len(user_id) > 8 else user_id  # Anonymize
        }
        
        if session_id:
            dimensions["SessionId"] = session_id[:8] + "..."
        
        self.record_metric(
            name="User.Engagement",
            value=1,
            dimensions=dimensions
        )
        
        # Log engagement event
        logger.info(f"User engagement: {action} by user {user_id[:8]}...")

    def track_chat_interaction(
        self,
        user_id: str,
        message_type: str,
        response_time_ms: Optional[float] = None,
        success: bool = True,
        error_type: Optional[str] = None
    ):
        """Track chat interaction metrics."""
        dimensions = {
            "MessageType": message_type,
            "Success": str(success)
        }
        
        if error_type:
            dimensions["ErrorType"] = error_type
        
        # Track interaction count
        self.record_metric(
            name="Chat.Interactions",
            value=1,
            dimensions=dimensions
        )
        
        # Track response time if provided
        if response_time_ms is not None:
            self.record_metric(
                name="Chat.ResponseTime",
                value=response_time_ms,
                unit="Milliseconds",
                dimensions={"MessageType": message_type},
                metric_type=MetricType.TIMER
            )
        
        # Create alert for errors
        if not success and error_type:
            self.create_alert(
                name="ChatInteractionError",
                level=AlertLevel.ERROR,
                message=f"Chat interaction failed: {error_type}",
                metadata={
                    "user_id": user_id[:8] + "...",
                    "message_type": message_type,
                    "error_type": error_type
                }
            )

    def track_recommendation_performance(
        self,
        user_id: str,
        recommendation_type: str,
        count: int,
        generation_time_ms: float,
        success: bool = True
    ):
        """Track recommendation generation performance."""
        dimensions = {
            "RecommendationType": recommendation_type,
            "Success": str(success)
        }
        
        # Track recommendation count
        self.record_metric(
            name="Recommendations.Generated",
            value=count,
            dimensions=dimensions
        )
        
        # Track generation time
        self.record_metric(
            name="Recommendations.GenerationTime",
            value=generation_time_ms,
            unit="Milliseconds",
            dimensions=dimensions,
            metric_type=MetricType.TIMER
        )

    def track_content_processing(
        self,
        content_type: str,
        language: str,
        processing_time_ms: float,
        success: bool = True,
        error_type: Optional[str] = None
    ):
        """Track content processing metrics."""
        dimensions = {
            "ContentType": content_type,
            "Language": language,
            "Success": str(success)
        }
        
        if error_type:
            dimensions["ErrorType"] = error_type
        
        # Track processing count
        self.record_metric(
            name="Content.Processed",
            value=1,
            dimensions=dimensions
        )
        
        # Track processing time
        self.record_metric(
            name="Content.ProcessingTime",
            value=processing_time_ms,
            unit="Milliseconds",
            dimensions=dimensions,
            metric_type=MetricType.TIMER
        )

    def track_database_operation(
        self,
        operation: str,
        table: str,
        duration_ms: float,
        success: bool = True,
        error_type: Optional[str] = None
    ):
        """Track database operation metrics."""
        dimensions = {
            "Operation": operation,
            "Table": table,
            "Success": str(success)
        }
        
        if error_type:
            dimensions["ErrorType"] = error_type
        
        # Track operation count
        self.record_metric(
            name="Database.Operations",
            value=1,
            dimensions=dimensions
        )
        
        # Track operation duration
        self.record_metric(
            name="Database.OperationTime",
            value=duration_ms,
            unit="Milliseconds",
            dimensions=dimensions,
            metric_type=MetricType.TIMER
        )
        
        # Alert on slow operations
        if duration_ms > 5000:  # 5 seconds
            self.create_alert(
                name="SlowDatabaseOperation",
                level=AlertLevel.WARNING,
                message=f"Slow database operation: {operation} on {table} took {duration_ms}ms",
                metadata={
                    "operation": operation,
                    "table": table,
                    "duration_ms": duration_ms
                }
            )

    def get_performance_summary(self, operation_name: str) -> Dict[str, float]:
        """Get performance summary for an operation."""
        if operation_name not in self.performance_data:
            return {}
        
        durations = self.performance_data[operation_name]
        if not durations:
            return {}
        
        return {
            "count": len(durations),
            "avg_ms": sum(durations) * 1000 / len(durations),
            "min_ms": min(durations) * 1000,
            "max_ms": max(durations) * 1000,
            "p95_ms": sorted(durations)[int(len(durations) * 0.95)] * 1000 if len(durations) > 1 else durations[0] * 1000
        }

    def flush_metrics(self):
        """Flush buffered metrics to CloudWatch."""
        if not self.cloudwatch or not self.metrics_buffer:
            return
        
        try:
            # Send metrics in batches of 20 (CloudWatch limit)
            batch_size = 20
            for i in range(0, len(self.metrics_buffer), batch_size):
                batch = self.metrics_buffer[i:i + batch_size]
                metric_data = []
                
                for metric in batch:
                    data = {
                        'MetricName': metric.name,
                        'Value': metric.value,
                        'Unit': metric.unit,
                        'Timestamp': metric.timestamp
                    }
                    
                    if metric.dimensions:
                        data['Dimensions'] = [
                            {'Name': k, 'Value': v} for k, v in metric.dimensions.items()
                        ]
                    
                    metric_data.append(data)
                
                self.cloudwatch.put_metric_data(
                    Namespace='Noah/ReadingAgent',
                    MetricData=metric_data
                )
            
            logger.info(f"Flushed {len(self.metrics_buffer)} metrics to CloudWatch")
            self.metrics_buffer.clear()
            
        except Exception as e:
            logger.error(f"Failed to flush metrics to CloudWatch: {e}")

    def health_check(self) -> Dict[str, Any]:
        """Perform health check and return status."""
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "services": {},
            "metrics": {
                "buffered_metrics": len(self.metrics_buffer),
                "buffered_alerts": len(self.alerts_buffer)
            }
        }
        
        # Check CloudWatch connectivity
        if self.cloudwatch:
            try:
                # Simple test to verify CloudWatch access
                self.cloudwatch.list_metrics(Namespace='Noah/ReadingAgent', MaxRecords=1)
                health_status["services"]["cloudwatch"] = "healthy"
            except Exception as e:
                health_status["services"]["cloudwatch"] = f"unhealthy: {str(e)}"
                health_status["status"] = "degraded"
        else:
            health_status["services"]["cloudwatch"] = "not_configured"
        
        return health_status


# Global monitoring service instance
monitoring_service = MonitoringService()