'''
======================================================================
File: logger.py
Author: Z Name, 
Created: 2026-06-25
======================================================================
'''

import logging
import sys

from app.config import settings


def setup_logging() -> logging.Logger:
    """Configure application logging."""
    logger = logging.getLogger(settings.SERVICE_NAME)
    logger.setLevel(logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)

    if not logger.handlers:
        logger.addHandler(handler)

    return logger


logger = setup_logging()