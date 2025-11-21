from __future__ import annotations

import logging
import sys
from typing import Any

import structlog
from structlog.contextvars import bind_contextvars, merge_contextvars
from structlog.processors import JSONRenderer, TimeStamper, add_log_level, StackInfoRenderer

from .settings import LoggingSettings
from ..config.base import core_settings


def configure_logging() -> None:
    settings = LoggingSettings()
    core = core_settings()

    level = settings.level if core.debug else getattr(logging, settings.level)

    shared_processors = [
        merge_contextvars,
        add_log_level,
        StackInfoRenderer(),
        TimeStamper(fmt="iso", utc=True, key="timestamp"),
    ]

    if settings.format == "json":
        renderer = JSONRenderer(sort_keys=True)
        if settings.include_trace_id or settings.include_span_id:
            from opentelemetry.trace import get_current_span

            def add_trace_and_span_id(logger, method_name, event_dict):
                span = get_current_span()
                if span.is_recording():
                    ctx = span.get_span_context()
                    if settings.include_trace_id:
                        event_dict["trace_id"] = f"{ctx.trace_id:032x}"
                    if settings.include_span_id:
                        event_dict["span_id"] = f"{ctx.span_id:016x}"
                return event_dict
            shared_processors.append(add_trace_and_span_id)

        final_processors = shared_processors + [renderer]
    else:
        from structlog.dev import ConsoleRenderer
        final_processors = shared_processors + [ConsoleRenderer(colors=True)]

    structlog.configure(
        processors=final_processors,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Set root logger level
    logging.getLogger().setLevel(level)
    logging.getLogger("iok_core").setLevel(level)

    # Silence noisy loggers
    for noisy in ["httpx", "httpcore", "passlib"]:
        logging.getLogger(noisy).setLevel(logging.WARNING)


# Auto-configure on import
configure_logging()