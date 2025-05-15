import logging
import sys

from loguru import logger as loguru_logger


logger = loguru_logger
custom_format = (
    "[<green>{time:HH:mm:ss.SS}</green>] "
    "<white>{file}:{function}:{line}</white> - "
    "<level>{message}</level>"
)

logger.remove()
logger.add(sys.stderr,
           level="TRACE",
           format=custom_format,
           colorize=True)

logger.remove()
logger.add(sys.stderr,
           level="TRACE",
           format=custom_format,
           colorize=True)

# Suppress
pil_logger = logging.getLogger("PIL")
pil_logger.setLevel(logging.WARNING)
