from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Database (async URL — uses aiomysql)
    DATABASE_URL: str

    # JWT — no default, MUST be set in .env
    SECRET_KEY: str

    # App metadata
    APP_NAME: str = "Waste Overflow Monitoring System"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True

    # CORS — set in .env as JSON array: CORS_ORIGINS=["http://example.com"]
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    # Sensor API key — if set, POST /api/bins/{id}/fill requires X-Sensor-Key header
    SENSOR_API_KEY: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


# Global singleton — import this everywhere
settings = Settings()