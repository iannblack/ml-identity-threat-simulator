import logging
import sys
from rich.logging import RichHandler

def setup_logger(name: str = "iam-simulator", level: str = "INFO"):
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True)]
    )
    return logging.getLogger(name)
