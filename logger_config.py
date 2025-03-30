import sys
from loguru import logger

# Remove default logger
logger.remove()

# Configure logging with loguru
logger.add(sys.stderr, level="DEBUG")
# logger.add("sensor.log", rotation="1 MB", retention="7 days", level="INFO")
