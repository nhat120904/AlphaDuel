"""
AlphaDuel Backend - FastAPI Application
The On-Chain AI Debate Arena with "Skin in the Game"
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import sys
import os
from dotenv import load_dotenv

# Load .env file BEFORE importing config
load_dotenv()

from .config import get_settings
from .routes.debate import router as debate_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="AlphaDuel API",
    description="""
    🐂 vs 🐻 The On-Chain AI Debate Arena
    
    AlphaDuel deploys competing AI agents—a Bull and a Bear—to debate 
    cryptocurrency market trends in real-time. The system uses Hedera 
    Blockchain to record predictions and programmatically wager HBAR 
    tokens based on the AI's confidence level.
    
    ## Features
    
    - **Multi-Agent Debate**: Bull and Bear agents argue market outlook
    - **Referee Agent**: Impartial judge determines the winner
    - **Hedera Integration**: Predictions logged to HCS, wagers executed on-chain
    - **Real-time Streaming**: Watch the debate unfold in real-time
    
    ## Endpoints
    
    - `POST /api/debate/start` - Start a complete debate
    - `POST /api/debate/stream` - Stream a debate with SSE
    - `GET /api/debate/symbols` - Get supported cryptocurrencies
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
settings = get_settings()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://*.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(debate_router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "AlphaDuel API",
        "version": "1.0.0",
        "description": "The On-Chain AI Debate Arena with Skin in the Game",
        "docs": "/docs",
        "health": "/api/debate/health"
    }


@app.on_event("startup")
async def startup_event():
    """Application startup"""
    logger.info("🚀 AlphaDuel API starting up...")
    logger.info(f"Debug mode: {settings.debug}")
    
    if not settings.openai_api_key:
        logger.warning("⚠️ OPENAI_API_KEY not set - AI agents will not work")
    
    if not settings.hedera_account_id:
        logger.warning("⚠️ Hedera credentials not set - running in simulation mode")
    
    logger.info("✅ AlphaDuel API ready!")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown"""
    logger.info("👋 AlphaDuel API shutting down...")

