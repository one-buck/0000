'''
======================================================================
File: config.py
Author: Z Name, 
Created: 2026-06-25
======================================================================
'''

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    DATABASE_URL: str = "postgresql+asyncpg://apikey_user:apikey_pass@db:5432/apikey_db"
    SERVICE_NAME: str = "api-key-management"
    KEY_PREFIX_LIVE: str = "sk_live"
    KEY_PREFIX_TEST: str = "sk_test"
    KEY_PREFIX_DEV: str = "sk_dev"
    DEFAULT_KEY_LENGTH: int = 32

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
