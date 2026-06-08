"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """All configuration is read from environment variables."""

    # Database — individual params allow pointing to any external server
    DB_HOST: str = "db"
    DB_PORT: int = 5432
    DB_USER: str = "lawny"
    DB_PASSWORD: str = "lawny_secret"
    DB_NAME: str = "lawny"

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @property
    def DATABASE_URL_SYNC(self) -> str:
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    # Optional PIN protection
    APP_PIN: Optional[str] = None

    # AI Providers — all optional; at least one must be set to enable AI features
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None

    # MapTiler (for enhanced satellite tiles)
    MAPTILER_KEY: Optional[str] = None

    # Timezone
    TZ: str = "America/New_York"

    @property
    def ai_enabled(self) -> bool:
        return bool(self.OPENAI_API_KEY or self.ANTHROPIC_API_KEY or self.GEMINI_API_KEY)

    @property
    def openai_enabled(self) -> bool:
        return bool(self.OPENAI_API_KEY)

    @property
    def anthropic_enabled(self) -> bool:
        return bool(self.ANTHROPIC_API_KEY)

    @property
    def gemini_enabled(self) -> bool:
        return bool(self.GEMINI_API_KEY)

    @property
    def maptiler_enabled(self) -> bool:
        return bool(self.MAPTILER_KEY)

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
