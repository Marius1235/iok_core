from __future__ import annotations

import asyncio
import ssl
import logging
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import AsyncIterator, Optional
from urllib.parse import urlparse, urlunparse

from redis.asyncio import Redis, ConnectionPool
from redis.asyncio.connection import (
    SSLConnection,
    UnixDomainSocketConnection,
)
from redis.exceptions import (
    ConnectionError as RedisPyConnectionError,
    TimeoutError as RedisPyTimeoutError,
    AuthenticationError,
)

from ..config.base import core_settings
from .settings import RedisSettings
from .exceptions import (
    RedisConnectionError,
    RedisDisabledError,
    RedisCircuitBreakerOpen,
)
from .settings import redis_settings



logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RedisSessionConfig:
    prefix: str = ""
    default_ttl: Optional[int] = None
    circuit_breaker: bool = True
    health_check: bool = True


class RedisHandler:
    _client: Optional[Redis] = None
    _lock = asyncio.Lock()

    @classmethod
    async def client(cls) -> Redis:
        if cls._client is not None:
            return cls._client

        async with cls._lock:
            if cls._client is not None:
                return cls._client

            settings = await redis_settings()
            global_settings = await core_settings()

            if settings.disabled or global_settings.redis_disabled:
                raise RedisDisabledError("Redis is disabled via config")

            try:
                pool = await cls._build_pool(settings)
                client = Redis.from_pool(pool)

                await asyncio.wait_for(client.ping(), timeout=10)
                logger.info("iok_core RedisHandler initialized")
                cls._client = client

            except RedisPyConnectionError as exc:
                raise RedisConnectionError("Cannot reach Redis server") from exc
            except RedisPyTimeoutError as exc:
                raise RedisConnectionError("Redis timeout during initialization") from exc
            except AuthenticationError as exc:
                raise RedisConnectionError("Redis authentication failed") from exc
            except Exception as exc:
                raise RedisConnectionError("Unexpected Redis initialization error") from exc

        return cls._client

    @classmethod
    async def _build_pool(cls, settings: RedisSettings) -> ConnectionPool:
        url = cls._build_url(settings)  # only used for unix or non-TLS

        base_kwargs = {
            "max_connections": settings.max_connections,
            "socket_connect_timeout": 5,
            "socket_timeout": 10,
            "socket_keepalive": True,
            "retry_on_timeout": True,
            "health_check_interval": 30,
            "decode_responses": True,
        }

        if url.startswith("unix://"):
            return ConnectionPool(
                connection_class=UnixDomainSocketConnection,
                path=url[7:],
                **base_kwargs,
            )

        if not settings.tls_enabled:
            return ConnectionPool.from_url(url, **base_kwargs)

        # ─────────────────────── FINAL WORKING TLS SETUP (2025) ───────────────────────
        logger.debug("Building Redis TLS connection pool with custom CA")

        # Build the connection kwargs with individual SSL parameters (this is the only way)
        connection_kwargs = {
            "host": settings.host,
            "port": settings.port,
            "password": settings.password.get_secret_value() if settings.password else None,
            "ssl_check_hostname": settings.tls_check_hostname,
            "ssl_cert_reqs": ssl.CERT_REQUIRED if settings.tls_ca_cert_path else ssl.CERT_NONE,
        }

        if settings.tls_ca_cert_path:
            ca_path = Path(settings.tls_ca_cert_path).expanduser()
            if not ca_path.exists():
                raise RedisConnectionError(f"CA certificate not found: {ca_path}")
            connection_kwargs["ssl_ca_certs"] = str(ca_path)

        if settings.client_cert_path and settings.client_key_path:
            cert_path = Path(settings.client_cert_path).expanduser()
            key_path = Path(settings.client_key_path).expanduser()
            if cert_path.exists() and key_path.exists():
                connection_kwargs["ssl_certfile"] = str(cert_path)
                connection_kwargs["ssl_keyfile"] = str(key_path)
            else:
                logger.warning("mTLS cert/key missing on disk — proceeding without client cert")

        connection_kwargs.update(base_kwargs)

        return ConnectionPool(
            connection_class=SSLConnection,
            **connection_kwargs,
        )
    

    @staticmethod
    def _build_url(settings: RedisSettings) -> str:
        scheme = "rediss" if settings.tls_enabled else "redis"
        url = f"{scheme}://{settings.host}:{settings.port}"

        if settings.password and settings.password.get_secret_value():
            pw = settings.password.get_secret_value()
            url = url.replace("://", f"://:{pw}@", 1)

        logger.debug("Constructed Redis URL: %s", url)
        return url
    

    @classmethod
    @asynccontextmanager
    async def session(cls, config: RedisSessionConfig = RedisSessionConfig()) -> AsyncIterator[Redis]:
        client = await cls.client()
        try:
            if config.health_check:
                await asyncio.wait_for(client.ping(), timeout=5)
            yield client
        except RedisPyConnectionError as exc:
            logger.exception(f"Detailed Redis connection failure – this is the real error\n{exc}")
            if config.circuit_breaker:
                raise RedisCircuitBreakerOpen(retry_after_seconds=30) from exc
            raise RedisConnectionError("Redis connection lost") from exc
        except RedisPyTimeoutError as exc:
            if config.circuit_breaker:
                raise RedisCircuitBreakerOpen(retry_after_seconds=15) from exc
            raise RedisConnectionError("Redis operation timed out") from exc
        except Exception as exc:
            logger.error("Unexpected Redis error in session", exc_info=True)
            raise RedisConnectionError("Redis operation failed") from exc

    @classmethod
    async def close(cls) -> None:
        if cls._client:
            await cls._client.aclose()
            cls._client = None
            logger.info("iok_core RedisHandler closed")