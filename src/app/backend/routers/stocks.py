"""
stocks.py — Stock data REST endpoints + paper trading engine

Stock data endpoints (Week 1):
  GET /api/stockdata          — historical OHLC candles for any ticker/interval/period
  GET /api/stockdata/intraday — intraday candles (short period, fine interval)

  Both endpoints call get_or_fetch_candles() which checks Redis first and only
  hits yfinance on a cache miss.  buy_price is stored in the cache but stripped
  from the REST response (the frontend only needs OHLC for the chart).

Paper trading endpoints (Week 3):
  POST   /api/trade           — open a new position (stored in Redis, survives restarts)
  DELETE /api/trade/{id}      — close a position (moves it to history list)
  GET    /api/trades          — list all open positions for the current user
  GET    /api/trades/history  — last 100 closed trades for the current user

Trade storage in Redis:
  trades:counter:{user_id}   String  — INCR gives each trade a unique integer ID
  trades:active:{user_id}    Hash    — field = trade_id, value = JSON trade object
  trades:history:{user_id}   List    — LPUSH closed trades, capped at 500 entries

All trade endpoints require authentication (Depends(get_current_user)).
Trades are scoped to the authenticated user, so one user cannot see another's trades.
"""

import json
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel
from helpers.cache import get_or_fetch_candles
from helpers.redis import redis_client
from utils.auth import get_current_user
from models.user.user import User

stock_router = APIRouter()

INTERVALS = {"1m", "5m", "15m", "30m", "1h", "1d"}
PERIODS   = {"1d", "5d", "1mo", "3mo"}

# Maximum number of closed trades kept per user in the history list
TRADE_HISTORY_CAP = 500


class TradeAction(BaseModel):
    ticker:     str
    action:     str    # "buy" or "sell"
    price:      float  # mid price at time of trade
    time:       int    # Unix timestamp
    buy_price:  float  # spread ask (what you pay to go long)
    sell_price: float  # spread bid (what you receive to go short)


# ---------------------------------------------------------------------------
# Stock data
# ---------------------------------------------------------------------------

@stock_router.get("/stockdata")
async def get_stock_data(
    ticker_symbol: str,
    interval: str = Query("5m"),
    period:   str = Query("1mo"),
):
    if interval not in INTERVALS or period not in PERIODS:
        raise HTTPException(status_code=400, detail="Invalid interval or period")

    try:
        candles = await get_or_fetch_candles(ticker_symbol, interval, period)
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")

    # Strip buy_price — the charting frontend only needs OHLC + timestamp
    return [{"time": c["time"], "open": c["open"], "high": c["high"], "low": c["low"], "close": c["close"]} for c in candles]


@stock_router.get("/stockdata/intraday")
async def get_intraday_data(
    ticker_symbol: str,
    interval: str = Query("15m"),
    period:   str = Query("1d"),
):
    if interval not in INTERVALS:
        raise HTTPException(status_code=400, detail="Invalid interval")
    if period not in PERIODS:
        raise HTTPException(status_code=400, detail="Invalid period")

    try:
        candles = await get_or_fetch_candles(ticker_symbol, interval, period)
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")

    return [{"time": c["time"], "open": c["open"], "high": c["high"], "low": c["low"], "close": c["close"]} for c in candles]


# ---------------------------------------------------------------------------
# Paper trading
# ---------------------------------------------------------------------------

@stock_router.post("/trade")
async def place_trade(
    trade: TradeAction,
    current_user: User = Depends(get_current_user),
):
    user_id  = str(current_user.id)

    # INCR is atomic — safe even if multiple requests arrive simultaneously
    trade_id = await redis_client.incr(f"trades:counter:{user_id}")

    direction   = 1 if trade.action == "buy" else -1
    entry_price = trade.price
    # exit_price is the spread price the user immediately faces after opening
    exit_price  = trade.sell_price if trade.action == "buy" else trade.buy_price
    spread      = round(trade.sell_price - trade.buy_price, 4)
    pnl         = round((exit_price - entry_price) * direction, 4)

    trade_data = {
        "trade_id":    trade_id,
        "ticker":      trade.ticker,
        "action":      trade.action,
        "entry_price": entry_price,
        "exit_price":  exit_price,
        "spread":      spread,
        "pnl":         pnl,
        "time":        trade.time,
    }

    # HSET — one field per trade inside a hash keyed by user, so listing all
    # open trades for a user is a single HGETALL call
    await redis_client.hset(f"trades:active:{user_id}", str(trade_id), json.dumps(trade_data))
    return {"message": "Trade executed", "data": trade_data}


@stock_router.delete("/trade/{trade_id}")
async def delete_trade(
    trade_id: int,
    current_user: User = Depends(get_current_user),
):
    user_id    = str(current_user.id)
    active_key = f"trades:active:{user_id}"

    trade_json = await redis_client.hget(active_key, str(trade_id))
    if not trade_json:
        raise HTTPException(status_code=404, detail="Trade not found")

    await redis_client.hdel(active_key, str(trade_id))

    # Move to history list — LPUSH prepends so index 0 is always the most recent.
    # LTRIM discards anything beyond the cap so the list doesn't grow unbounded.
    history_key = f"trades:history:{user_id}"
    await redis_client.lpush(history_key, trade_json)
    await redis_client.ltrim(history_key, 0, TRADE_HISTORY_CAP - 1)

    return {"message": "Trade removed"}


@stock_router.get("/trades")
async def get_trades(current_user: User = Depends(get_current_user)):
    """Return all open positions for the authenticated user, newest first."""
    user_id = str(current_user.id)
    raw     = await redis_client.hgetall(f"trades:active:{user_id}")
    trades  = [json.loads(v) for v in raw.values()]
    trades.sort(key=lambda t: t["time"], reverse=True)
    return trades


@stock_router.get("/trades/history")
async def get_trade_history(current_user: User = Depends(get_current_user)):
    """Return the last 100 closed trades for the authenticated user."""
    user_id = str(current_user.id)
    raw     = await redis_client.lrange(f"trades:history:{user_id}", 0, 99)
    return [json.loads(t) for t in raw]
