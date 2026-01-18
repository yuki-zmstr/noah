"""Enhanced logging configuration for Noah Reading Agent."""

import logging
import logging.config
import json
import sys
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

from src.config import settings


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields from record
        for key, value in record.__dict__.items():
            if key not in {
                'name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                'filename', 'module', 'lineno', 'funcName', 'created',
                'msecs', 'relativeCreated', 'thread', 'threadName',
                'processName', 'process', 'getMessage', 'exc_info',
                'exc_text', 'stack_info'
            }:
                log_entry[key] = value
        
        return json.dumps(log_entry, default=str)


class ContextFilter(logging.Filter):
    """Add contextual information to log records."""
    
    def __init__(self, service_name: str = "noah-reading-agent"):
        super().__init__()
        self.service_name = service_name
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Add context to log record."""
        record.service = self.service_name
        record.environment = "production" if not settings.debug else "development"
        return True


def setup_logging():
    """Configure comprehensive logging for the application."""
    
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Determine log level
    log_level = "DEBUG" if settings.debug else "INFO"
    
    # Logging configuration
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
            "detailed": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
            "json": {
                "()": JSONFormatter
            }
        },
        "filters": {
            "context": {
                "()": ContextFilter
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": log_level,
                "formatter": "json" if not settings.debug else "standard",
                "filters": ["context"],
                "stream": sys.stdout
            },
            "file_info": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "json",
                "filters": ["context"],
                "filename": "logs/noah-info.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5
            },
            "file_error": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "ERROR",
                "formatter": "detailed",
                "filters": ["context"],
                "filename": "logs/noah-error.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5
            },
            "file_performance": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "json",
                "filters": ["context"],
                "filename": "logs/noah-performance.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 3
            }
        },
        "loggers": {
            # Root logger
            "": {
                "level": log_level,
                "handlers": ["console", "file_info", "file_error"]
            },
            # Application loggers
            "src": {
                "level": log_level,
                "handlers": ["console", "file_info", "file_error"],
                "propagate": False
            },
            # Performance logger
            "performance": {
                "level": "INFO",
                "handlers": ["file_performance"],
                "propagate": False
            },
            # Third-party loggers
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console", "file_info"],
                "propagate": False
            },
            "uvicorn.access": {
                "level": "INFO",
                "handlers": ["file_info"],
                "propagate": False
            },
            "sqlalchemy": {
                "level": "WARNING",
                "handlers": ["console", "file_error"],
                "propagate": False
            },
            "boto3": {
                "level": "WARNING",
                "handlers": ["console", "file_error"],
                "propagate": False
            },
            "botocore": {
                "level": "WARNING",
                "handlers": ["console", "file_error"],
                "propagate": False
            },
            "httpx": {
                "level": "WARNING",
                "handlers": ["console", "file_error"],
                "propagate": False
            }
        }
    }
    
    # Apply logging configuration
    logging.config.dictConfig(config)
    
    # Log startup message
    logger = logging.getLogger(__name__)
    logger.info(
        "Logging configured successfully",
        extra={
            "log_level": log_level,
            "debug_mode": settings.debug,
            "service": "noah-reading-agent"
        }
    )


class PerformanceLogger:
    """Specialized logger for performance metrics."""
    
    def __init__(self):
        self.logger = logging.getLogger("performance")
    
    def log_operation(
        self,
        operation: str,
        duration_ms: float,
        success: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log performance data for an operation."""
        self.logger.info(
            f"Operation completed: {operation}",
            extra={
                "operation": operation,
                "duration_ms": duration_ms,
                "success": success,
                "metadata": metadata or {}
            }
        )
    
    def log_user_interaction(
        self,
        user_id: str,
        action: str,
        duration_ms: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log user interaction performance."""
        extra_data = {
            "user_id": user_id[:8] + "..." if len(user_id) > 8 else user_id,
            "action": action,
            "metadata": metadata or {}
        }
        
        if duration_ms is not None:
            extra_data["duration_ms"] = duration_ms
        
        self.logger.info(
            f"User interaction: {action}",
            extra=extra_data
        )
    
    def log_api_request(
        self,
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
        user_id: Optional[str] = None
    ):
        """Log API request performance."""
        self.logger.info(
            f"API request: {method} {path}",
            extra={
                "method": method,
                "path": path,
                "status_code": status_code,
                "duration_ms": duration_ms,
                "user_id": user_id[:8] + "..." if user_id and len(user_id) > 8 else user_id
            }
        )


# Global performance logger instance
performance_logger = PerformanceLogger()


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name."""
    return logging.getLogger(name)


def log_with_context(
    logger: logging.Logger,
    level: int,
    message: str,
    **context
):
    """Log a message with additional context."""
    logger.log(level, message, extra=context)