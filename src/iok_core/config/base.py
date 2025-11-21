from __future__ import annotations

import asyncio
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict



class IOKSettings(BaseSettings):
    """
    Shared base for ALL iok_core settings.
    This is the ONLY place global config lives.
    """
    model_config = SettingsConfigDict(
        env_prefix="IOK_",
        case_sensitive=False,
        extra="ignore",
        frozen=True,
    )

    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = False
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    service_name: str = "iok-core"
    instance_id: str = ""

    redis_disabled: bool = False
    tracing_enabled: bool = True
    metrics_enabled: bool = True

    @property
    def is_development(self) -> bool:
        return self.environment == "development"


_core_instance: IOKSettings | None = None
_core_lock = asyncio.Lock()

async def core_settings() -> IOKSettings:
    global _core_instance
    if _core_instance is not None:
        return _core_instance
    async with _core_lock:
        if _core_instance is None:
            _core_instance = IOKSettings()
    return _core_instance