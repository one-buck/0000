from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://apikey_user:apikey_pass@db:5432/apikey_db"
    service_name: str = "api-key-management"
    key_prefix_live: str = "sk_live"
    key_prefix_test: str = "sk_test"
    key_prefix_dev: str = "sk_dev"
    default_key_length: int = 32

    class Config:
        env_file = ".env1"


settings = Settings()