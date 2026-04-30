"""
websocket.py — Real-time stock price WebSocket endpoint (Week 2 refactor)

Before (Week 1):
  Each connection ran its own broadcast loop that called the cache every second.
  The loop pushed directly to a set of WebSocket objects stored in memory.

After (Week 2):
  The price publisher (services/price_publisher.py) runs ONE background task per
  (ticker, interval) and pushes candle JSON to a Redis Pub/Sub channel.
  Each WebSocket connection here subscribes to that channel and forwards messages
  to its browser client — no polling, no in-memory subscription dicts.

Disconnect handling:
  Starlette WebSocket doesn't expose a disconnect event directly, so we run two
  concurrent tasks and use asyncio.wait(FIRST_COMPLETED) to react to whichever
  finishes first:
    forward_prices()     — reads from Redis channel, writes to WebSocket
    wait_for_disconnect() — blocks on websocket.receive_text(); raises on disconnect

  When either task finishes, we cancel the other, unsubscribe from Redis, and
  call release_publisher() so the background task stops when no clients remain.

Redis channel: ws:price:{ticker}:{interval}
"""

import json
import asyncio
from fastapi import APIRouter, WebSocket, Query
from helpers.redis import redis_client
from services.price_publisher import ensure_publisher, release_publisher

websocket_router = APIRouter()


@websocket_router.websocket("/ws/stockdata")
async def websocket_stock_data(
    websocket: WebSocket,
    ticker_symbol: str,
    interval: str = Query("1m"),
):
    await websocket.accept()

    # Register this connection with the publisher — starts the publish task if
    # this is the first subscriber for this (ticker, interval) combination
    ensure_publisher(ticker_symbol, interval)

    # Each connection gets its own pubsub object (its own Redis connection from
    # the pool) so that subscribing/unsubscribing doesn't affect other clients
    pubsub = redis_client.pubsub()
    channel = f"ws:price:{ticker_symbol}:{interval}"
    await pubsub.subscribe(channel)

    async def forward_prices() -> None:
        """Read candle messages from Redis and push them to the browser."""
        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    await websocket.send_json(json.loads(message["data"]))
        except Exception:
            pass

    async def wait_for_disconnect() -> None:
        """Block until the client disconnects (receive raises on close)."""
        try:
            while True:
                await websocket.receive_text()
        except Exception:
            pass

    forward_task    = asyncio.create_task(forward_prices())
    disconnect_task = asyncio.create_task(wait_for_disconnect())

    try:
        # Wait for whichever task ends first (disconnect or a forwarding error)
        _, pending = await asyncio.wait(
            [forward_task, disconnect_task],
            return_when=asyncio.FIRST_COMPLETED,
        )
        for task in pending:
            task.cancel()
    finally:
        # Always clean up the Redis subscription and decrement the publisher counter
        await pubsub.unsubscribe(channel)
        await pubsub.aclose()
        release_publisher(ticker_symbol, interval)
