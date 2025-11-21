from __future__ import annotations

import asyncio

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from ..config.base import IOKSettings

class RedisSettings(IOKSettings):
    model_config = SettingsConfigDict(env_prefix="IOK_REDIS_")

    host: str = "localhost"
    port: int = 6379
    password: SecretStr | None = None

    tls_enabled: bool = True
    client_cert_path: str | None = None
    client_key_path: str | None = None
    tls_ca_cert_path: str | None = None
    tls_check_hostname: bool = False
    
    max_connections: int = Field(default=20, ge=5, le=200)
    disabled: bool = False



_redis_settings_instance: RedisSettings | None = None
_redis_settings_lock = asyncio.Lock()


async def redis_settings() -> RedisSettings:
    global _redis_settings_instance
    if _redis_settings_instance is not None:
        return _redis_settings_instance

    async with _redis_settings_lock:
        if _redis_settings_instance is None:
            _redis_settings_instance = RedisSettings()
    return _redis_settings_instance


def redis_settings_sync() -> RedisSettings:
    import anyio
    return anyio.run(redis_settings)