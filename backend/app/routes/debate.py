"""
Debate API Routes
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional
import json
import asyncio
import logging

from ..config import get_settings, Settings
from ..services.market_data import MarketDataService
from ..services.hedera import HederaService
from ..agents.graph import create_debate_graph

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/debate", tags=["debate"])


class DebateRequest(BaseModel):
    """Request model for starting a debate"""
    query: str = Field(..., description="The user's question about the market")
    symbol: str = Field(default="HBAR", description="Cryptocurrency symbol to analyze")
    max_rounds: int = Field(default=2, ge=1, le=3, description="Maximum debate rounds")


class DebateResponse(BaseModel):
    """Response model for debate results"""
    status: str
    winner: Optional[str] = None
    confidence_score: Optional[float] = None
    wager_amount: Optional[float] = None
    hcs_tx_url: Optional[str] = None
    wager_tx_url: Optional[str] = None


def get_services(settings: Settings = Depends(get_settings)):
    """Dependency to get initialized services"""
    market_service = MarketDataService(
        coingecko_api_key=settings.coingecko_api_key,
        tavily_api_key=settings.tavily_api_key
    )
    
    hedera_service = HederaService(
        account_id=settings.hedera_account_id,
        private_key=settings.hedera_private_key,
        escrow_account_id=settings.hedera_escrow_account_id,
        network=settings.hedera_network,
        topic_id=settings.hcs_topic_id or None
    )
    
    return market_service, hedera_service, settings.openai_api_key


@router.post("/start")
async def start_debate(
    request: DebateRequest,
    services: tuple = Depends(get_services)
):
    """
    Start a new debate (non-streaming)
    Returns the complete result after all agents have finished
    """
    market_service, hedera_service, openai_api_key = services
    
    try:
        graph = create_debate_graph(market_service, hedera_service, api_key=openai_api_key)
        result = await graph.run_complete(request.query, request.symbol)
        
        verdict = result.get("verdict", {})
        hcs_tx = result.get("hcs_tx", {})
        wager_tx = result.get("wager_tx", {})
        
        return {
            "status": "completed",
            "symbol": request.symbol,
            "winner": verdict.get("winner"),
            "confidence_score": verdict.get("confidence_score"),
            "wager_amount": verdict.get("wager_amount"),
            "reasoning": verdict.get("reasoning"),
            "key_factors": verdict.get("key_factors", []),
            "hcs_tx": hcs_tx,
            "wager_tx": wager_tx,
            "debate_rounds": result.get("debate_rounds", []),
            "bull_arguments": result.get("bull_arguments", []),
            "bear_arguments": result.get("bear_arguments", []),
        }
        
    except Exception as e:
        logger.error(f"Error in debate: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream")
async def stream_debate(
    request: DebateRequest,
    services: tuple = Depends(get_services)
):
    """
    Start a new debate with Server-Sent Events streaming
    Streams each agent's response as it is generated
    """
    market_service, hedera_service, openai_api_key = services
    
    async def event_generator():
        try:
            graph = create_debate_graph(market_service, hedera_service, api_key=openai_api_key)
            
            async for message in graph.run(request.query, request.symbol):
                # Format as SSE
                data = json.dumps(message, default=str)
                yield f"data: {data}\n\n"
                
                # Small delay to prevent overwhelming the client
                await asyncio.sleep(0.01)
            
            # Send completion event
            yield f"data: {json.dumps({'type': 'done', 'status': 'completed'})}\n\n"
            
        except Exception as e:
            logger.error(f"Error in streaming debate: {e}")
            error_data = json.dumps({"type": "error", "content": str(e)})
            yield f"data: {error_data}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "AlphaDuel Debate API"}


@router.get("/symbols")
async def get_supported_symbols():
    """Get list of supported cryptocurrency symbols"""
    return {
        "symbols": [
            {"symbol": "HBAR", "name": "Hedera", "id": "hedera-hashgraph"},
            {"symbol": "BTC", "name": "Bitcoin", "id": "bitcoin"},
            {"symbol": "ETH", "name": "Ethereum", "id": "ethereum"},
            {"symbol": "SOL", "name": "Solana", "id": "solana"},
            {"symbol": "AVAX", "name": "Avalanche", "id": "avalanche-2"},
            {"symbol": "MATIC", "name": "Polygon", "id": "matic-network"},
            {"symbol": "DOT", "name": "Polkadot", "id": "polkadot"},
            {"symbol": "LINK", "name": "Chainlink", "id": "chainlink"},
        ]
    }

