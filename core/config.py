from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Database (async URL — uses aiomysql)
    DATABASE_URL: str

    # JWT (used for login module later)
    SECRET_KEY: str = "dev-secret-not-for-production"

    # App metadata
    APP_NAME: str = "Waste Overflow Monitoring System"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True

    # Tell Pydantic to read from .env
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # ignore unknown vars in .env without failing
    )


# Global singleton — import this everywhere
settings = Settings()