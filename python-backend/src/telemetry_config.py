"""OpenTelemetry configuration and management."""

import os
import logging
from src.config import settings

logger = logging.getLogger(__name__)


def configure_telemetry():
    """Configure OpenTelemetry based on settings."""
    if not settings.opentelemetry_enabled:
        # Disable OpenTelemetry to avoid context issues
        os.environ["OTEL_SDK_DISABLED"] = "true"
        logger.info("OpenTelemetry disabled via configuration")
    else:
        # Configure OpenTelemetry if enabled
        if settings.opentelemetry_endpoint:
            os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = settings.opentelemetry_endpoint
        
        os.environ["OTEL_SERVICE_NAME"] = settings.opentelemetry_service_name
        logger.info("OpenTelemetry enabled and configured")


def suppress_telemetry_warnings():
    """Suppress OpenTelemetry context warnings that don't affect functionality."""
    # Suppress specific OpenTelemetry warnings
    logging.getLogger("opentelemetry.context").setLevel(logging.CRITICAL)
    logging.getLogger("opentelemetry.trace").setLevel(logging.WARNING)
    
    # Suppress Strands telemetry warnings
    logging.getLogger("strands.agent.agent").setLevel(logging.WARNING)
    logging.getLogger("strands.event_loop.event_loop").setLevel(logging.WARNING)


# Configure telemetry on import
configure_telemetry()
suppress_telemetry_warnings()