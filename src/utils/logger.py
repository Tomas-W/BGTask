import sys

from loguru import logger as loguru_logger

logger = loguru_logger
custom_format = "[<green>{time:HH:mm:ss.SS}</green>] {file}:{function}:{line} - <level>{message}</level>"
logger.remove()
logger.add(sys.stderr,
           level="TRACE",
           format=custom_format,
           colorize=True)