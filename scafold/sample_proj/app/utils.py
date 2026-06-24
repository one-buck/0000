'''
======================================================================
File: utils.py
Author: Your Name
Created: 2026-06-24 15:51:07
======================================================================

'''from datetime import datetime, timezone
from typing import Any


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def to_dict_or_none(obj: Any | None) -> dict | None:
    if obj is None:
        return None
    return obj.dict() if hasattr(obj, "dict") else dict(obj)
