from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers.stocks import stock_router
from .routers.search import search_router
from .routers.websocket import websocket_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
<<<<<<< Updated upstream
    allow_origins=["http://localhost:3000"],
=======
    allow_origins=["http://localhost:3001", "http://localhost:3000"],
>>>>>>> Stashed changes
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(stock_router, prefix="/api")
app.include_router(search_router, prefix="/api")
app.include_router(websocket_router, prefix="/api")