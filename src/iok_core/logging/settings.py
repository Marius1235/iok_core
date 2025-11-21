from __future__ import annotations

from functools import lru_cache
from typing import Literal

from ..config.base import IOKSettings
from pydantic_settings import SettingsConfigDict



class LoggingSettings(IOKSettings):
    model_config = SettingsConfigDict(env_prefix="IOK_LOG_")

    format: Literal["json", "pretty"] = "json"
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    include_trace_id: bool = True
    include_span_id: bool = True


@lru_cache
def logging_settings() -> LoggingSettings:
    return LoggingSettings()