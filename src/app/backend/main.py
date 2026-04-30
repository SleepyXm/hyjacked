"""
main.py — FastAPI application entry point

Startup order:
  1. CORS middleware added (browsers require this for cross-origin cookie requests)
  2. slowapi rate-limit middleware added (must come after CORS)
  3. All routers registered under /api
  4. On startup: Redis ping to confirm the connection is healthy
  5. On shutdown: all background publisher tasks are cancelled cleanly
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from routers.stocks import stock_router
from routers.search import search_router
from routers.websocket import websocket_router
from routers.portfolio import portfolio_router
from routers.auth.auth import auth_router as auth
from routers.auth.profile import profile_router
from helpers.redis import redis_client
from helpers.limiter import limiter
from services.price_publisher import cancel_all

app = FastAPI()

# Attach the limiter instance to app state so slowapi middleware can find it
app.state.limiter = limiter

# Return 429 with a JSON body when a rate limit is exceeded
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001", "http://localhost:3000"],
    allow_credentials=True,   # required for httpOnly cookie auth
    allow_methods=["*"],
    allow_headers=["*"],
)

# SlowAPI middleware intercepts requests and increments Redis rate-limit counters
app.add_middleware(SlowAPIMiddleware)

app.include_router(stock_router,    prefix="/api")
app.include_router(search_router,   prefix="/api")
app.include_router(websocket_router, prefix="/api")
app.include_router(portfolio_router, prefix="/api")
app.include_router(auth,            prefix="/api/auth")
app.include_router(profile_router,  prefix="/api/user")


@app.on_event("startup")
async def startup_event():
    try:
        await redis_client.ping()
        print("Redis is online!")
    except Exception as e:
        # App will still start but caching and rate limiting will be degraded
        print(f"Redis connection failed: {e}")


@app.on_event("shutdown")
async def shutdown_cleanup():
    # Cancel all running price-publisher asyncio tasks so they don't linger
    cancel_all()
