'''
======================================================================
File: config.py
Author: Your Name
Created: 2026-06-24 15:51:07
======================================================================

'''from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SERVICE_NAME: str = "service"
    DATABASE_URL: str
    REDIS_URL: str | None = None
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"


settings = Settings()
