from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    GITHUB_APP_ID: str
    GITHUB_WEBHOOK_SECRET: str
    PRIVATE_KEY_PATH:str
    DATABASE_URL:str
    OPENAI_API_KEY:str
    OPENAI_MODEL:str

    class Config:
        env_file = ".env"


settings = Settings()