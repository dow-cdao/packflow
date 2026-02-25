import os
import sys

from loguru import logger

logger.remove()
logger.add(sys.stderr, level=os.getenv("PACKFLOW_LOG_LEVEL", "INFO"))


def get_logger():
    return logger
