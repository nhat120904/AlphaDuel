"""
State models for LangGraph agent workflow
"""
from typing import TypedDict, Literal, Optional, List, Annotated
from pydantic import BaseModel
import operator


class MarketData(BaseModel):
    """Market data for a cryptocurrency"""
    symbol: str
    current_price: float
    price_change_24h: float
    price_change_percentage_24h: float
    market_cap: float
    total_volume: float
    high_24h: float
    low_24h: float
    rsi: Optional[float] = None
    news_summary: Optional[str] = None
    sentiment_score: Optional[float] = None


class AgentArgument(BaseModel):
    """An argument made by an agent"""
    agent: Literal["Bull", "Bear"]
    argument: str
    confidence: float
    key_points: List[str]


class DebateRound(BaseModel):
    """A round in the debate"""
    round_number: int
    bull_argument: str
    bear_argument: str


class Verdict(BaseModel):
    """The referee's final verdict"""
    winner: Literal["Bull", "Bear"]
    confidence_score: float
    wager_amount: float
    reasoning: str
    key_factors: List[str]


class HederaTransaction(BaseModel):
    """Hedera transaction details"""
    tx_id: str
    tx_type: Literal["HCS_LOG", "TRANSFER"]
    status: str
    hashscan_url: str
    amount: Optional[float] = None


class AgentState(TypedDict):
    """The state passed between agents in the LangGraph workflow"""
    # User input
    user_query: str
    symbol: str
    
    # Market data
    market_data: Optional[dict]
    
    # Debate
    debate_rounds: Annotated[List[dict], operator.add]
    current_round: int
    max_rounds: int
    
    # Agent opinions
    bull_arguments: Annotated[List[dict], operator.add]
    bear_arguments: Annotated[List[dict], operator.add]
    
    # Final verdict
    verdict: Optional[dict]
    
    # Hedera transactions
    hcs_tx: Optional[dict]
    wager_tx: Optional[dict]
    
    # Streaming messages
    messages: Annotated[List[dict], operator.add]
    
    # Status
    status: str
    error: Optional[str]


def create_initial_state(user_query: str, symbol: str = "HBAR") -> AgentState:
    """Create the initial state for a new debate"""
    return AgentState(
        user_query=user_query,
        symbol=symbol.upper(),
        market_data=None,
        debate_rounds=[],
        current_round=0,
        max_rounds=2,
        bull_arguments=[],
        bear_arguments=[],
        verdict=None,
        hcs_tx=None,
        wager_tx=None,
        messages=[],
        status="initialized",
        error=None
    )

