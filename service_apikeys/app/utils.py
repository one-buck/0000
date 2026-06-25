'''
======================================================================
File: utils.py
Author: Z Name, 
Created: 2026-06-25
======================================================================
'''

from datetime import datetime, timezone
from typing import Any


def now_utc() -> datetime:
    return datetime.now(timezone.utc)

