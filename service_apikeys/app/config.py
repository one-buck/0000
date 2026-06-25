'''
======================================================================
File: config.py
Author: Z Name, 
Created: 2026-06-25
======================================================================
'''

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SERVICE_NAME: str = "api-key-management"
    SERVICE_PORT: str = "8000"
    SERVICE_URL: str = "localhost"
    KEY_PREFIX_TEST: str = "sk_test"
    KEY_PREFIX_DEV: str = "sk_dev"
    DEFAULT_KEY_LENGTH: int = 32
    LOG_LEVEL: str = "INFO"
    DATABASE_URL: str

    class Config:
        env_file = ".env"


settings = Settings()
