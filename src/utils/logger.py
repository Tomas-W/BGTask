import sys

from loguru import logger as loguru_logger

logger = loguru_logger
custom_format = "{function}:{line} - <level>{message}</level>"
logger.remove()
logger.add(sys.stderr,
           level="DEBUG",
           format=custom_format,
           colorize=True)