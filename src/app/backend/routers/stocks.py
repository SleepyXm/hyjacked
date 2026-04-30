from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from helpers.cache import get_or_fetch_candles

stock_router = APIRouter()

class TradeAction(BaseModel):
    ticker: str
    action: str
    price: float
    time: int
    buy_price: float
    sell_price: float


INTERVALS = {"1m", "5m", "15m", "30m", "1h", "1d"}
PERIODS = {"1d", "5d", "1mo", "3mo"}


@stock_router.get("/stockdata")
async def get_stock_data(
    ticker_symbol: str,
    interval: str = Query("5m"),
    period: str = Query("1mo")
):
    if interval not in INTERVALS or period not in PERIODS:
        raise HTTPException(status_code=400, detail="Invalid interval or period")

    try:
        candles = await get_or_fetch_candles(ticker_symbol, interval, period)
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")

    return [{"time": c["time"], "open": c["open"], "high": c["high"], "low": c["low"], "close": c["close"]} for c in candles]


@stock_router.get("/stockdata/intraday")
async def get_intraday_data(
    ticker_symbol: str,
    interval: str = Query("15m"),
    period: str = Query("1d")
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

active_trades = {}
trade_counter = 0

@stock_router.post("/trade")
async def place_trade(trade: TradeAction):
    global trade_counter
    trade_counter += 1
    trade_id = trade_counter

    direction = 1 if trade.action == "buy" else -1

    entry_price = trade.price
    exit_price = trade.sell_price if trade.action == "buy" else trade.buy_price
    spread = round(trade.sell_price - trade.buy_price, 4)
    pnl = round((exit_price - entry_price) * direction, 4)

    active_trades[trade_id] = {
        "ticker": trade.ticker,
        "action": trade.action,
        "entry_price": entry_price,
        "exit_price": exit_price,
        "spread": spread,
        "pnl": pnl,
        "time": trade.time,
    }

    return {
        "message": "Trade executed",
        "data": {**active_trades[trade_id], "trade_id": trade_id},
    }

@stock_router.delete("/trade/{trade_id}")
async def delete_trade(trade_id: int):
    if trade_id not in active_trades:
        raise HTTPException(status_code=404, detail="Trade not found")
    del active_trades[trade_id]
    return {"message": "Trade removed"}