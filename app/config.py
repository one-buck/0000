from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://adminu:adminu@localhost:5432/chat_db"
    class Config:
        env_file = ".env"

settings = Settings()