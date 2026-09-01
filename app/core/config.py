from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Watcher"
    app_env: str = "development"
    debug: bool = False
    database_url: str = ""
    http_timeout_seconds: float = 15.0
    http_max_concurrency: int = 5

    jwt_secret_key: str = ""
    jwt_refresh_secret_key: str = ""
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    model_config = SettingsConfigDict(
        env_file=(".env",),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    @model_validator(mode="after")
    def validate_environment(self):
        if self.app_env == "production" and self.debug:
            raise ValueError("Debug mode is not allowed in production.")
        return self

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
