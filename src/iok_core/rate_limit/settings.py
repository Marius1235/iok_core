# src/iok_core/redis/settings.py
from __future__ import annotations

from functools import lru_cache
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

# Optional: inherit from shared base if you want global overrides
# from ..config.base import ConfigBase
# class RedisSettings(ConfigBase):
class RedisSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="IOK_REDIS_",   # ← all Redis env vars start with IOK_REDIS_
        case_sensitive=False,
        extra="ignore",
    )

    endpoint: str = Field(..., description="redis(s):// or rediss:// URL")
    password: SecretStr | None = Field(default=None)
    tls_enabled: bool = Field(default=True)
    client_cert_path: str = Field(default="certs/redis/client.crt")
    client_key_path: str = Field(default="certs/redis/client.key")
    max_connections: int = Field(default=20, ge=1, le=100)
    disabled: bool = Field(default=False, description="Globally disable Redis")

    # Per-consumer defaults can override these
    default_ttl_seconds: int = Field(default=60*60*24*7)


@lru_cache
def redis_settings() -> RedisSettings:
    """Thread-safe singleton — used everywhere"""
    return RedisSettings()