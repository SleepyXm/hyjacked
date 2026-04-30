import json
import asyncio
from helpers.redis import redis_client
from routers.utils.stock_utils import load_stock_data

# TTL in seconds per interval — how long a yfinance response stays fresh
CACHE_TTL: dict[str, int] = {
    "1m":  20,
    "5m":  60,
    "15m": 180,
    "30m": 300,
    "1h":  600,
    "1d":  1800,
    "1wk": 10800,
    "1mo": 21600,
}


async def get_or_fetch_candles(ticker: str, interval: str, period: str) -> list[dict]:
    """Return candles from Redis cache, falling back to yfinance on miss."""
    cache_key = f"stock:data:{ticker}:{interval}:{period}"

    cached = await redis_client.get(cache_key)
    if cached:
        return json.loads(cached)

    loop = asyncio.get_running_loop()
    data, mapping = await loop.run_in_executor(None, load_stock_data, ticker, interval, period)

    candles = _serialize_candles(data, mapping)
    ttl = CACHE_TTL.get(interval, 60)
    await redis_client.setex(cache_key, ttl, json.dumps(candles))

    return candles


def _serialize_candles(data, mapping) -> list[dict]:
    open_col  = mapping["open_col"]
    high_col  = mapping["high_col"]
    low_col   = mapping["low_col"]
    close_col = mapping["close_col"]

    return [
        {
            "time":      int(idx.timestamp()),
            "open":      float(row[open_col]),
            "high":      float(row[high_col]),
            "low":       float(row[low_col]),
            "close":     float(row[close_col]),
            "buy_price": float(row["Buy_Price"]),
        }
        for idx, row in data.iterrows()
    ]
