# tests/unit/test_settings.py
import pytest

def test_redis_settings_defaults(monkeypatch):
    monkeypatch.delenv("IOK_REDIS_ENDPOINT", raising=False)

    from iok_core.redis.settings import RedisSettings

    with pytest.raises(ValueError):
        RedisSettings()