import logging
import os
import secrets
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class Settings:
    def __init__(self) -> None:
        self.environment = os.getenv("ENVIRONMENT", "development").lower()
        self.database_url = os.getenv("DATABASE_URL", "sqlite:///./db.database")
        self.secret_key = os.getenv("SECRET_KEY")
        self.algorithm = os.getenv("ALGORITHM", "HS256")
        self.access_token_expire_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
        self.ai_base_url = os.getenv("AI_BASE_URL", "https://openrouter.ai/api/v1")
        self.ai_api_key = os.getenv("OPENAI_API_KEY")
        self.ai_model = os.getenv("AI_MODEL", "gpt-4o-mini")
        self.ai_timeout_seconds = float(os.getenv("AI_TIMEOUT_SECONDS", "20"))
        default_requests = "60" if self.environment == "development" else "10"
        self.ai_rate_limit_requests = int(os.getenv("AI_RATE_LIMIT_REQUESTS", default_requests))
        self.ai_rate_limit_window_seconds = int(os.getenv("AI_RATE_LIMIT_WINDOW_SECONDS", "60"))
        self.log_level = os.getenv("LOG_LEVEL", "INFO").upper()

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    def get_secret_key(self) -> str:
        if self.secret_key:
            return self.secret_key

        if self.is_production:
            raise RuntimeError("SECRET_KEY must be set when ENVIRONMENT=production.")

        fallback_key = secrets.token_urlsafe(32)
        logger.warning(
            "SECRET_KEY is not set. Using an ephemeral development key; existing tokens will stop working on restart."
        )
        return fallback_key

    def validate(self) -> None:
        if self.access_token_expire_minutes <= 0:
            raise RuntimeError("ACCESS_TOKEN_EXPIRE_MINUTES must be greater than 0.")
        if self.ai_timeout_seconds <= 0:
            raise RuntimeError("AI_TIMEOUT_SECONDS must be greater than 0.")
        if self.ai_rate_limit_requests <= 0:
            raise RuntimeError("AI_RATE_LIMIT_REQUESTS must be greater than 0.")
        if self.ai_rate_limit_window_seconds <= 0:
            raise RuntimeError("AI_RATE_LIMIT_WINDOW_SECONDS must be greater than 0.")
        self.get_secret_key()


@lru_cache
def get_settings() -> Settings:
    current_settings = Settings()
    current_settings.validate()
    return current_settings


settings = get_settings()

DATABASE_URL = settings.database_url
SECRET_KEY = settings.get_secret_key()
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes
