from pathlib import Path

import pytest

from iok_core.redis.settings import redis_settings


@pytest.fixture(autouse=True)
def reset_redis_singletons():
    from iok_core.redis.settings import _redis_settings_instance
    from iok_core.config.base import _core_instance

    globals()["_redis_settings_instance"] = None
    globals()["_core_instance"] = None

    yield

    globals()["_redis_settings_instance"] = None
    globals()["_core_instance"] = None