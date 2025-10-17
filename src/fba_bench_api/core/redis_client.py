from __future__ import annotations

import asyncio
import logging
import os
import random
from typing import Optional

from redis.asyncio import Redis
from redis.asyncio.client import PubSub

from fba_bench_core.config import get_settings

logger = logging.getLogger(__name__)

# Singleton async Redis client (lazy)
_redis_singleton: Optional[Redis] = None


def get_redis_url() -> str:
    """Resolve Redis URL from centralized settings (prefers FBA_BENCH_REDIS_URL, then REDIS_URL)."""
    settings = get_settings()
    url = settings.preferred_redis_url
    if url:
        return url
    raise ValueError("Redis URL is not configured. Please set FBA_BENCH_REDIS_URL.")


async def get_redis() -> Redis:
    """
    Get/create a singleton async Redis client configured from env with
    resilient initialization (exponential backoff and jitter on initial ping).
    """
    global _redis_singleton
    if _redis_singleton is None:
        url = get_redis_url()
        logger.info("Initializing Redis client: %s", url)
        _redis_singleton = Redis.from_url(
            url,
            decode_responses=True,
            health_check_interval=30,
            retry_on_timeout=True,
        )

        # Retry settings (configurable via env, with safe defaults)
        max_retries = int(os.getenv("REDIS_MAX_RETRIES", "5"))
        base_delay_ms = int(os.getenv("REDIS_BASE_DELAY_MS", "100"))  # 100ms
        max_delay_ms = int(os.getenv("REDIS_MAX_DELAY_MS", "2000"))  # 2s

        attempt = 0
        last_exc: Optional[Exception] = None
        while True:
            try:
                await _redis_singleton.ping()
                break  # success
            except Exception as exc:
                last_exc = exc
                attempt += 1
                if attempt > max_retries:
                    # Ensure we don't retain a broken singleton
                    await close_redis()
                    logger.error(
                        "Redis unavailable at %s after %d retries: %s",
                        url,
                        max_retries,
                        exc,
                    )
                    raise
                # Exponential backoff with full jitter
                backoff_ms = min(max_delay_ms, base_delay_ms * (2 ** (attempt - 1)))
                sleep_ms = random.randint(int(backoff_ms / 2), backoff_ms)
                logger.warning(
                    "Redis ping failed (attempt %d/%d): %s. Retrying in %dms",
                    attempt,
                    max_retries,
                    exc,
                    sleep_ms,
                )
                await asyncio.sleep(sleep_ms / 1000.0)
    return _redis_singleton


async def get_pubsub() -> PubSub:
    """
    Return a new PubSub object bound to the singleton client.

    Note: Caller is responsible for closing the PubSub via pubsub.close().
    """
    client = await get_redis()
    # ignore_subscribe_messages=True filters out subscribe/unsubscribe ack messages
    return client.pubsub(ignore_subscribe_messages=True)


async def close_redis() -> None:
    """Close the singleton Redis client (used on graceful shutdown)."""
    global _redis_singleton
    if _redis_singleton is not None:
        try:
            await _redis_singleton.close()
        except Exception as exc:
            logger.warning("Error closing Redis client: %s", exc)
        finally:
            _redis_singleton = None
