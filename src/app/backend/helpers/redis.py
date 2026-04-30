"""
redis.py — Shared async Redis client

A single redis.asyncio client is created once at import time and reused
across the entire application (cache layer, pub/sub, trade storage, tokens).

decode_responses=True means all values come back as Python strings instead
of bytes, so we never need to call .decode() manually.

The connection pool is managed automatically by the library — individual
coroutines borrow a connection from the pool, use it, then return it.
"""

import redis.asyncio as redis
import os

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

redis_client = redis.from_url(REDIS_URL, decode_responses=True)
