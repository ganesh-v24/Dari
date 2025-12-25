from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_ENV: str = "dev"

    MAPS_API_KEY: str | None = None
    LLM_PROVIDER: str = "groq"

    class Config:
        env_file = ".env"

settings = Settings()
