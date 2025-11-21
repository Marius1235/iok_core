import pytest
import asyncio
import logging
from pathlib import Path

from iok_core.redis import RedisHandler
from iok_core.redis.exceptions import RedisConnectionError


@pytest.mark.asyncio
async def test_real_connection():
    from iok_core.redis.settings import redis_settings
    from iok_core.redis.handler import logger as redis_logger

    redis_logger.setLevel(logging.DEBUG)

    s = await redis_settings()

    print("\n=== REDIS CONFIG LOADED BY TEST ===")
    print(f"Host: {s.host}")
    print(f"Port: {s.port}")
    print(f"Password set: {bool(s.password)}")
    print(f"TLS: {s.tls_enabled}")
    print(f"Client cert path exists: {Path(s.client_cert_path).expanduser().exists() if s.client_cert_path else False}")
    print(f"Client key path exists: {Path(s.client_key_path).expanduser().exists() if s.client_key_path else False}")
    print(f"CA cert path exists: {Path(s.tls_ca_cert_path).expanduser().exists() if s.tls_ca_cert_path else False}")
    print(f"TLS check hostname: {s.tls_check_hostname}")
    print("========================================\n")

    try:
        client = await RedisHandler.client()

        assert await client.ping() is True or await client.ping() == "PONG"

        key = "test:iok_core:integration"
        await client.set(key, "value", ex=5)
        value = await client.get(key)
        assert value == "value"

        await asyncio.sleep(6)
        assert await client.get(key) is None

        print("Redis integration test PASSED with TLS + password + custom CA!")

    except Exception as e:
        print(f"\nRedis connection FAILED: {type(e).__name__}: {e}")
        print("\nLast 20 log lines:")
        pytest.fail("Redis connection failed — see logs above")
    finally:
        await RedisHandler.close()