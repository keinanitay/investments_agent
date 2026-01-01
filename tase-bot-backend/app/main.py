from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from app.db.database import connect_to_mongo, close_mongo_connection
from app.routers import chat
from app.routers import auth
import os

@asynccontextmanager
async def lifespan(app: FastAPI):
    """manages the application lifecycle, connecting to the database on startup."""
    await connect_to_mongo()
    yield
    await close_mongo_connection()

app = FastAPI(title="TASE Bot API", lifespan=lifespan)

# cors middleware configuration to allow frontend access
origins = [
    "http://localhost:3000", # react default port
    "http://localhost:5173", # vite default port
]

# add allowed origins from environment variable for production
env_origins = os.getenv("ALLOWED_ORIGINS")
if env_origins:
    origins.extend([origin.strip() for origin in env_origins.split(",")])

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# include application routers
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])

@app.get("/")
async def root():
    """health check endpoint."""
    return {"status": "TASE Bot System Ready"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)