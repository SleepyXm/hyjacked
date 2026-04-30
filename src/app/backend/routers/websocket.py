from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from helpers.cache import get_or_fetch_candles
import asyncio

websocket_router = APIRouter()

subscriptions = {}  # { "AAPL_1m": set([websocket1, websocket2]) }
fetch_tasks = {}     # { "AAPL_1m": asyncio.Task }

async def broadcast_stock_data(ticker: str, interval: str):
    key = f"{ticker}_{interval}"

    while True:
        try:
            candles = await get_or_fetch_candles(ticker, interval, "1d")
            if not candles:
                await broadcast_to_subs(key, {"error": "No data found"})
                await asyncio.sleep(15)
                continue

            await broadcast_to_subs(key, candles[-1])
        except Exception as e:
            await broadcast_to_subs(key, {"error": f"Broadcast error: {str(e)}"})

        await asyncio.sleep(1)

async def broadcast_to_subs(key: str, message: dict):
    dead_sockets = []
    for ws in subscriptions.get(key, []):
        try:
            await ws.send_json(message)
        except:
            dead_sockets.append(ws)

    for ws in dead_sockets:
        subscriptions[key].remove(ws)


# --- Route ---
@websocket_router.websocket("/ws/stockdata")
async def websocket_stock_data(
    websocket: WebSocket,
    ticker_symbol: str,
    interval: str = Query("1m")
):
    key = f"{ticker_symbol}_{interval}"

    await websocket.accept()

    if key not in subscriptions:
        subscriptions[key] = set()

    subscriptions[key].add(websocket)

    # Start background fetcher if not running
    if key not in fetch_tasks:
        fetch_tasks[key] = asyncio.create_task(broadcast_stock_data(ticker_symbol, interval))

    try:
        while True:
            await asyncio.sleep(60)  # keep alive
    except WebSocketDisconnect:
        subscriptions[key].remove(websocket)
        if not subscriptions[key]:
            del subscriptions[key]
            fetch_tasks[key].cancel()
            del fetch_tasks[key]
        print(f"Client disconnected: {ticker_symbol} [{interval}]")