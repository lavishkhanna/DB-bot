import logging
import sys

def setup_logging(log_level: str = "INFO"):
    """
    Configure logging for the application.

    This function forcefully configures logging even if handlers already exist
    (which happens when running with uvicorn). It ensures application logs
    are visible in the terminal.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Convert string level to logging constant
    level = getattr(logging, log_level.upper(), logging.INFO)

    # Get the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove any existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create console handler that outputs to stdout
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)

    # Add handler to root logger
    root_logger.addHandler(console_handler)

    # Set level for app loggers to ensure they propagate
    app_logger = logging.getLogger('app')
    app_logger.setLevel(level)

    # Log that logging is configured
    root_logger.info(f"Logging configured with level: {log_level.upper()}")
