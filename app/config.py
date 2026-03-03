from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    MONGODB_URL: str
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440

    model_config = {"env_file": ".env"}


settings = Settings()
