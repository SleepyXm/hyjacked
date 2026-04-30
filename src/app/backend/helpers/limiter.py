"""
limiter.py — Rate limiter configuration

slowapi (a FastAPI port of Flask-Limiter) uses the `limits` library under the hood.
Passing a Redis URI as storage_uri tells `limits` to store counters in Redis instead
of in-memory.

Why Redis backing matters:
  - In-memory counters reset on every server restart, so the limit is bypassable
    by quickly restarting the process (or simply running multiple workers).
  - With Redis, counters are shared across all Uvicorn workers and survive restarts,
    making the limit actually enforceable in production.
"""

import os
from slowapi import Limiter
from slowapi.util import get_remote_address

# Re-use the same Redis instance the rest of the app connects to
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

limiter = Limiter(
    key_func=get_remote_address,   # rate-limit by client IP address
    storage_uri=REDIS_URL,         # persist counters in Redis
)
