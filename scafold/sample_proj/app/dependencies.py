'''
======================================================================
File: dependencies.py
Author: Your Name
Created: 2026-06-24 15:51:07
======================================================================

'''from functools import lru_cache

from app.config import Settings


@lru_cache
def get_settings() -> Settings:
    from app.config import settings
    return settings
