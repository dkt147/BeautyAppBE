from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    MONGODB_URL: str
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440

    # extra="ignore": the shared .env also holds the ARCH backend's settings
    # (ARCH_*, SMTP_*, TWILIO_*); pydantic-settings rejects unknown keys by default.
    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
