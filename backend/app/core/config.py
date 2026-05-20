import secrets
import warnings

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "GPMS API"
    app_env: str = "development"
    app_debug: bool = False
    api_v1_prefix: str = "/api/v1"
    database_url: str = "sqlite:///./gpms.db"
    jwt_secret_key: str = "CHANGE_THIS_SECRET_KEY"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 120
    upload_dir: str = "uploads"
    max_upload_mb: int = 20
    cors_origins: str = "http://localhost:5500,http://127.0.0.1:5500,http://localhost:8080,http://127.0.0.1:8080"
    seed_allow_unauthenticated: bool = True

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    @field_validator("jwt_secret_key")
    @classmethod
    def validate_jwt_secret(cls, v: str, info) -> str:
        env = (info.data.get("app_env") or "development").lower()
        weak = v in ("", "CHANGE_THIS_SECRET_KEY", "secret", "changeme")
        if env == "production" and weak:
            raise ValueError(
                "JWT_SECRET_KEY must be set to a strong random value in production"
            )
        if weak and env != "production":
            warnings.warn(
                "Using default JWT_SECRET_KEY — set a strong secret in .env before deployment",
                stacklevel=2,
            )
        return v

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"

    @property
    def cors_origin_list(self) -> list[str]:
        if self.is_production:
            origins = [o.strip() for o in self.cors_origins.split(",") if o.strip()]
            return origins or ["https://localhost"]
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()] or ["*"]

    @staticmethod
    def generate_secret() -> str:
        return secrets.token_urlsafe(48)


settings = Settings()
