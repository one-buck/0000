from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "changeme_postgres"
    POSTGRES_DB: str = "app_db"
    POSTGRES_PORT: int = 5432

    MINIO_ROOT_USER: str = "minioadmin"
    MINIO_ROOT_PASSWORD: str = "minioadmin"
    MINIO_API_PORT: int = 9000
    MINIO_BUCKET: str = "chat-media"

    ELASTICSEARCH_HOST: str = "localhost"
    ELASTICSEARCH_PORT: int = 9200

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@localhost:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def MINIO_ENDPOINT(self) -> str:
        return f"localhost:{self.MINIO_API_PORT}"

    class Config:
        env_file = ".env"


settings = Settings()