import os 
import logging
from azure.monitor.opentelemetry import configure_azure_monitor

logger = logging.getLogger("brand-guardian-telemetry")


def setup_telemetry():
    """
    Initializes Azure Monitor OpenTelemetry
    Tracks: HTTP requests, database queries, errors, performance metrics
    Sends this data to azure monitor
    it auto captures every API request
    No need to manually log each endpoint

    """
    # retrieve connection string

    connection_string = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")

    if not connection_string:
        logger.warning("APPLICATIONINSIGHTS_CONNECTION_STRING not found")
        return

    try:
        configure_azure_monitor(
            connection_string=connection_string,
            logger_name = "brand-guardian-telemetry"
            )
        logger.info("Telemetry setup complete")
    except Exception as e:
        logger.error(f"Telemetry setup failed: {str(e)}")


        