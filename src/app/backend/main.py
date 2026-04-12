from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.stocks import stock_router
from routers.search import search_router
from routers.websocket import websocket_router
from routers.auth.auth import auth_router as auth
from routers.auth.profile import profile_router
from helpers.redis import redis_client

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(stock_router, prefix="/api")
app.include_router(search_router, prefix="/api")
app.include_router(websocket_router, prefix="/api")
app.include_router(auth, prefix="/api/auth")
app.include_router(profile_router, prefix="/api/user")



@app.on_event("startup")
async def startup_event():
    # Check if redis is alive
    try:
        await redis_client.ping()
        print("Redis is online!")
    except Exception as e:
        print(f"Redis connection failed: {e}")
    

@app.on_event("shutdown")
async def shutdown_cleanup():
    await redis_client.delete("") # <--- Fill with any redis workers you set.