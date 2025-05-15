import logging
import sys

from loguru import logger as loguru_logger


logger = loguru_logger
custom_format = (
    "[<dim><green>{time:HH:mm:ss.SS}</green></dim>] "
    "<dim><white>{file}:{function}:{line}</white></dim> - "
    "<dim><level>{message}</level></dim>"
)

logger.remove()
logger.add(sys.stderr,
           level="TRACE",
           format=custom_format,
           colorize=True)

# Suppress
pil_logger = logging.getLogger("PIL")
pil_logger.setLevel(logging.WARNING)
