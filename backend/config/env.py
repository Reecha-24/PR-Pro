from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    GITHUB_APP_ID: str
    GITHUB_WEBHOOK_SECRET: str
    PRIVATE_KEY_PATH: Optional[str] = None
    GITHUB_PRIVATE_KEY: Optional[str] = None
    DATABASE_URL: str
    OPENAI_API_KEY: str
    OPENAI_MODEL: str
    GITHUB_PRIVATE_KEY:str
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0


    class Config:
        env_file = ".env"


settings = Settings()