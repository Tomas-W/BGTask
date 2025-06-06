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

# Add custom levels
logger.timing = lambda message: logger.opt(depth=1).log("TIMING", message)

# Add custom colors
logger.level("TIMING", no=15, color="<fg 200,0,250>")  # purple/pink
logger.level("INFO", color="<fg 255,165,0>")           # orange
logger.level("WARNING", color="<fg 235,235,0>")        # brighter yellow

# Suppress
pil_logger = logging.getLogger("PIL")
pil_logger.setLevel(logging.WARNING)
