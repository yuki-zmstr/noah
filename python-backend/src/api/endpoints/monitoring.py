"""Monitoring and health check endpoints."""

import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel

from src.services.monitoring_service import monitoring_service, AlertLevel
from src.services.logging_config import performance_logger
from src.database import get_db
from sqlalchemy.orm import Session
from sqlalchemy import text

logger = logging.getLogger(__name__)
router = APIRouter()


class HealthStatus(BaseModel):
    """Health check response model."""
    status: str
    timestamp: str
    version: str
    uptime_seconds: float
    services: Dict[str, str]
    metrics: Dict[str, Any]


class MetricsSummary(BaseModel):
    """Metrics summary response model."""
    timestamp: str
    period_minutes: int
    request_count: int
    error_count: int
    avg_response_time_ms: float
    performance_summary: Dict[str, Dict[str, float]]


# Track application start time for uptime calculation
app_start_time = time.time()


@router.get("/health", response_model=HealthStatus)
async def health_check(db: Session = Depends(get_db)):
    """Comprehensive health check endpoint."""
    start_time = time.time()
    
    try:
        # Calculate uptime
        uptime_seconds = time.time() - app_start_time
        
        # Get monitoring service health
        monitoring_health = monitoring_service.health_check()
        
        # Check database connectivity
        db_status = "healthy"
        try:
            db.execute(text("SELECT 1"))
            db.commit()
        except Exception as e:
            db_status = f"unhealthy: {str(e)}"
            logger.error(f"Database health check failed: {e}")
        
        # Compile service statuses
        services = {
            "database": db_status,
            **monitoring_health.get("services", {})
        }
        
        # Determine overall status
        overall_status = "healthy"
        if any(status.startswith("unhealthy") for status in services.values()):
            overall_status = "unhealthy"
        elif any(status == "degraded" for status in services.values()):
            overall_status = "degraded"
        
        # Create response
        health_response = HealthStatus(
            status=overall_status,
            timestamp=datetime.utcnow().isoformat() + "Z",
            version="0.1.0",
            uptime_seconds=uptime_seconds,
            services=services,
            metrics={
                "health_check_duration_ms": (time.time() - start_time) * 1000,
                **monitoring_health.get("metrics", {})
            }
        )
        
        # Log health check
        logger.info(
            f"Health check completed: {overall_status}",
            extra={
                "status": overall_status,
                "uptime_seconds": uptime_seconds,
                "services": services
            }
        )
        
        # Track health check metric
        monitoring_service.record_metric(
            name="HealthCheck.Requests",
            value=1,
            dimensions={"Status": overall_status}
        )
        
        return health_response
        
    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        
        # Track failed health check
        monitoring_service.record_metric(
            name="HealthCheck.Errors",
            value=1,
            dimensions={"ErrorType": type(e).__name__}
        )
        
        raise HTTPException(
            status_code=503,
            detail={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        )


@router.get("/metrics/summary", response_model=MetricsSummary)
async def get_metrics_summary(
    period_minutes: int = Query(default=60, ge=1, le=1440, description="Time period in minutes")
):
    """Get application metrics summary."""
    try:
        # This is a simplified implementation
        # In a real system, you'd query CloudWatch or your metrics store
        
        # Get performance summaries from monitoring service
        performance_data = {}
        for operation in ["chat_interaction", "content_processing", "recommendation_generation"]:
            summary = monitoring_service.get_performance_summary(operation)
            if summary:
                performance_data[operation] = summary
        
        # Create mock summary (in production, this would come from actual metrics)
        summary = MetricsSummary(
            timestamp=datetime.utcnow().isoformat() + "Z",
            period_minutes=period_minutes,
            request_count=len(monitoring_service.metrics_buffer),
            error_count=len([a for a in monitoring_service.alerts_buffer if a.level.value in ["error", "critical"]]),
            avg_response_time_ms=100.0,  # This would be calculated from actual metrics
            performance_summary=performance_data
        )
        
        logger.info(f"Metrics summary requested for {period_minutes} minutes")
        
        return summary
        
    except Exception as e:
        logger.error(f"Failed to get metrics summary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/metrics/flush")
async def flush_metrics():
    """Manually flush buffered metrics to CloudWatch."""
    try:
        monitoring_service.flush_metrics()
        
        logger.info("Metrics flushed manually")
        
        return {
            "status": "success",
            "message": "Metrics flushed to CloudWatch",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
    except Exception as e:
        logger.error(f"Failed to flush metrics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logs/recent")
async def get_recent_logs(
    level: str = Query(default="INFO", description="Log level filter"),
    limit: int = Query(default=100, ge=1, le=1000, description="Number of log entries")
):
    """Get recent log entries (simplified implementation)."""
    try:
        # This is a simplified implementation
        # In production, you'd query your log aggregation system
        
        # For now, return information about log configuration
        return {
            "message": "Log retrieval not implemented in this version",
            "suggestion": "Check CloudWatch Logs or local log files",
            "log_files": [
                "/logs/noah-info.log",
                "/logs/noah-error.log",
                "/logs/noah-performance.log"
            ],
            "cloudwatch_log_groups": [
                "/aws/ecs/noah-backend"
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to get recent logs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance/operations")
async def get_operation_performance():
    """Get performance data for all tracked operations."""
    try:
        performance_data = {}
        
        # Get all tracked operations
        for operation_name in monitoring_service.performance_data.keys():
            summary = monitoring_service.get_performance_summary(operation_name)
            if summary:
                performance_data[operation_name] = summary
        
        logger.info("Operation performance data requested")
        
        return {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "operations": performance_data
        }
        
    except Exception as e:
        logger.error(f"Failed to get operation performance: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test/alert")
async def test_alert(
    level: str = Query(default="info", description="Alert level: info, warning, error, critical"),
    message: str = Query(default="Test alert", description="Alert message")
):
    """Create a test alert for monitoring validation."""
    try:
        # Map string to AlertLevel enum
        level_mapping = {
            "info": AlertLevel.INFO,
            "warning": AlertLevel.WARNING,
            "error": AlertLevel.ERROR,
            "critical": AlertLevel.CRITICAL
        }
        
        alert_level = level_mapping.get(level.lower(), AlertLevel.INFO)
        
        # Create test alert
        monitoring_service.create_alert(
            name="TestAlert",
            level=alert_level,
            message=message,
            metadata={
                "test": True,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        logger.info(f"Test alert created: {level} - {message}")
        
        return {
            "status": "success",
            "message": f"Test alert created with level {level}",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
    except Exception as e:
        logger.error(f"Failed to create test alert: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test/metric")
async def test_metric(
    name: str = Query(description="Metric name"),
    value: float = Query(description="Metric value"),
    unit: str = Query(default="Count", description="Metric unit")
):
    """Create a test metric for monitoring validation."""
    try:
        # Create test metric
        monitoring_service.record_metric(
            name=f"Test.{name}",
            value=value,
            unit=unit,
            dimensions={"Test": "true"}
        )
        
        logger.info(f"Test metric created: {name}={value} {unit}")
        
        return {
            "status": "success",
            "message": f"Test metric {name} created with value {value} {unit}",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
    except Exception as e:
        logger.error(f"Failed to create test metric: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))