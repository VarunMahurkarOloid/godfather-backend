from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from routes import auth, missions, players, trades, families, admin, blackmarket
from utils.google_client import init_sheets

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_sheets()
    yield
    # Shutdown (cleanup if needed)

app = FastAPI(title="The Godfather: Office Mafia API", lifespan=lifespan)

# CORS middleware - allow all origins for development
# In production, ngrok tunnels are temporary and Vercel domains may vary
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for flexibility with ngrok and Vercel
    allow_credentials=False,  # Set to False when using wildcard origins
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "Welcome to The Godfather: Office Mafia API",
        "version": "1.0",
        "status": "operational"
    }

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(players.router, prefix="/player", tags=["Players"])
app.include_router(missions.router, prefix="/missions", tags=["Missions"])
app.include_router(trades.router, prefix="/trades", tags=["Trades"])
app.include_router(families.router, prefix="/families", tags=["Families"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])
app.include_router(blackmarket.router, prefix="/blackmarket", tags=["Black Market"])
# Debug router removed for production security

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
