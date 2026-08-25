from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    GITHUB_APP_ID: str
    GITHUB_WEBHOOK_SECRET: str

    class Config:
        env_file = ".env"


settings = Settings()