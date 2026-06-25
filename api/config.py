from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://apikey_user:apikey_pass@db:5432/apikey_db"
    SERVICE_NAME: str = "api-key-management"
    KEY_PREFIX_TEST: str = "sk_test"
    KEY_PREFIX_DEV: str = "sk_dev"
    DEFAULT_KEY_LENGTH: int = 32

    class Config:
        env_file = ".env"


settings = Settings()