# tests/unit/test_redis_handler.py
import pytest
from unittest.mock import AsyncMock, patch

from iok_core.redis.handler import RedisHandler
from iok_core.redis.exceptions import RedisDisabledError
from iok_core.redis.settings import RedisSettings
from iok_core.config.base import IOKSettings


@pytest.mark.asyncio
async def test_disabled_via_settings(monkeypatch):
    monkeypatch.setenv("IOK_REDIS_ENDPOINT", "redis://localhost:6379")

    # Create a real settings instance with disabled=True
    disabled_settings = RedisSettings(
        endpoint="redis://localhost:6379",
        disabled=True,                    # <-- this is what disables it
        tls_enabled=False,                # optional: avoid mTLS certificate loading noise
    )

    # Patch the async function to return our pre-configured instance
    with patch("iok_core.redis.handler.redis_settings", return_value=disabled_settings):
        with patch("iok_core.redis.handler.core_settings"):  # no need to mock if not used
            with pytest.raises(RedisDisabledError, match="Redis is disabled via config"):
                await RedisHandler.client()


@pytest.mark.asyncio
async def test_disabled_via_settings_async_mock(monkeypatch):
    monkeypatch.setenv("IOK_REDIS_ENDPOINT", "redis://localhost:6379")

    mock_redis_settings = AsyncMock()
    mock_redis_settings.return_value.disabled = True
    mock_redis_settings.return_value.endpoint = "redis://localhost:6379"

    with patch("iok_core.redis.handler.redis_settings", mock_redis_settings):
        with pytest.raises(RedisDisabledError):
            await RedisHandler.client()


@pytest.mark.asyncio
async def test_disabled_via_global(monkeypatch):
    monkeypatch.setenv("IOK_REDIS_ENDPOINT", "redis://localhost:6379")

    # Normal redis settings (not disabled)
    normal_redis_settings = RedisSettings(endpoint="redis://localhost:6379")

    # But global config has redis_disabled = True
    disabled_global = IOKSettings(redis_disabled=True)  # type: ignore

    with patch("iok_core.redis.handler.redis_settings", return_value=normal_redis_settings):
        with patch("iok_core.redis.handler.core_settings", return_value=disabled_global):
            with pytest.raises(RedisDisabledError, match="Redis is disabled via config"):
                await RedisHandler.client()