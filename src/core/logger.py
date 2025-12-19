import logging

from rich.logging import RichHandler


def setup_logger(name: str = "iam-simulator", level: str = "INFO") -> logging.Logger:
    """
    Set up a logger with Rich formatting.

    Args:
        name: Name of the logger
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        Configured logger instance
    """
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True)],
    )
    return logging.getLogger(name)
