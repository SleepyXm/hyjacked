"""
price_publisher.py — Centralised price feed (Week 2)

Problem this solves:
  Before pub/sub, every WebSocket connection called yfinance independently.
  10 clients watching AAPL_1m = 10 parallel yfinance polls per second.

How it works now:
  One asyncio Task (the "publisher") runs per (ticker, interval) pair.
  It polls the stock data cache every second and publishes the latest candle
  to a Redis Pub/Sub channel.  Any number of WebSocket handlers can subscribe
  to that channel and forward messages to their clients.

  10 clients watching AAPL_1m = 1 publisher task, 10 lightweight Redis subscribers.

Lifecycle:
  ensure_publisher()  — called when a WebSocket client connects.
                        Increments a subscriber counter; starts the task if not running.
  release_publisher() — called when a WebSocket client disconnects.
                        Decrements the counter; cancels the task when it hits 0.
  cancel_all()        — called on app shutdown to cleanly cancel every running task.

Redis keys written by the publisher:
  ws:price:{ticker}:{interval}  — Pub/Sub channel (consumed by WebSocket handlers)
  price:latest:{ticker}         — Latest candle JSON, TTL 10 s
                                  (consumed by the portfolio P&L endpoint)
"""

import json
import asyncio
from helpers.redis import redis_client
from helpers.cache import get_or_fetch_candles

# Maps "AAPL:1m" → running asyncio.Task
_publishers: dict[str, asyncio.Task] = {}

# Maps "AAPL:1m" → number of active WebSocket subscribers
_subscriber_count: dict[str, int] = {}

# price:latest expires after this many seconds so stale prices don't linger
# if the feed crashes or all clients disconnect
PRICE_LATEST_TTL = 10


async def _publish_loop(ticker: str, interval: str) -> None:
    """
    Runs forever until cancelled.  On each tick:
      1. Fetch the latest candle from the cache (yfinance only called on cache miss)
      2. Publish the candle JSON to the Pub/Sub channel
      3. Update price:latest:{ticker} for the portfolio P&L endpoint
    """
    channel = f"ws:price:{ticker}:{interval}"
    while True:
        try:
            candles = await get_or_fetch_candles(ticker, interval, "1d")
            if candles:
                payload = json.dumps(candles[-1])
                await redis_client.publish(channel, payload)
                # Keep a separate single-value key so the portfolio endpoint can
                # read the current price without having to subscribe to the channel
                await redis_client.setex(f"price:latest:{ticker}", PRICE_LATEST_TTL, payload)
        except Exception:
            pass  # never crash the loop — transient errors (network, bad data) are fine
        await asyncio.sleep(1)


def ensure_publisher(ticker: str, interval: str) -> None:
    """Increment subscriber count and start the publisher task if needed."""
    key = f"{ticker}:{interval}"
    _subscriber_count[key] = _subscriber_count.get(key, 0) + 1
    # Also restart the task if it finished unexpectedly (task.done() == True)
    if key not in _publishers or _publishers[key].done():
        _publishers[key] = asyncio.create_task(_publish_loop(ticker, interval))


def release_publisher(ticker: str, interval: str) -> None:
    """Decrement subscriber count and cancel the publisher when the channel empties."""
    key = f"{ticker}:{interval}"
    _subscriber_count[key] = max(0, _subscriber_count.get(key, 1) - 1)
    if _subscriber_count[key] == 0 and key in _publishers:
        _publishers[key].cancel()
        del _publishers[key]


def cancel_all() -> None:
    """Cancel every running publisher task — called during app shutdown."""
    for task in _publishers.values():
        task.cancel()
    _publishers.clear()
    _subscriber_count.clear()
