"""
LangGraph Debate Orchestration
Manages the stateful workflow between Bull, Bear, and Referee agents
"""
from typing import Dict, Any, AsyncGenerator, Literal, Optional
from langgraph.graph import StateGraph, END
import asyncio
import json
import logging
import os

from ..models.state import AgentState, create_initial_state
from ..services.market_data import MarketDataService
from ..services.hedera import HederaService
from .bull import BullAgent
from .bear import BearAgent
from .referee import RefereeAgent

logger = logging.getLogger(__name__)


class DebateGraph:
    """Orchestrates the multi-agent debate using LangGraph"""
    
    def __init__(
        self,
        market_service: MarketDataService,
        hedera_service: HederaService,
        model: str = "gpt-4.1",
        api_key: Optional[str] = None
    ):
        self.market_service = market_service
        self.hedera_service = hedera_service
        openai_api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.bull_agent = BullAgent(model=model, api_key=openai_api_key)
        self.bear_agent = BearAgent(model=model, api_key=openai_api_key)
        self.referee_agent = RefereeAgent(model="gpt-4.1", api_key=openai_api_key)
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow"""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("fetch_market_data", self._fetch_market_data)
        workflow.add_node("bull_argues", self._bull_argues)
        workflow.add_node("bear_argues", self._bear_argues)
        workflow.add_node("check_debate_rounds", self._check_debate_rounds)
        workflow.add_node("referee_decides", self._referee_decides)
        workflow.add_node("execute_hedera", self._execute_hedera)
        
        # Set entry point
        workflow.set_entry_point("fetch_market_data")
        
        # Add edges
        workflow.add_edge("fetch_market_data", "bull_argues")
        workflow.add_edge("bull_argues", "bear_argues")
        workflow.add_edge("bear_argues", "check_debate_rounds")
        
        # Conditional edge for debate rounds
        workflow.add_conditional_edges(
            "check_debate_rounds",
            self._should_continue_debate,
            {
                "continue": "bull_argues",
                "conclude": "referee_decides"
            }
        )
        
        workflow.add_edge("referee_decides", "execute_hedera")
        workflow.add_edge("execute_hedera", END)
        
        return workflow.compile()
    
    async def _fetch_market_data(self, state: AgentState) -> Dict[str, Any]:
        """Fetch market data for the symbol"""
        logger.info(f"Fetching market data for {state['symbol']}")
        
        try:
            market_data = await self.market_service.get_market_data(state['symbol'])
            
            return {
                "market_data": market_data,
                "status": "market_data_fetched",
                "messages": [{
                    "type": "system",
                    "content": f"📊 Fetched market data for {state['symbol']}",
                    "data": {
                        "price": market_data.get("current_price"),
                        "change_24h": market_data.get("price_change_percentage_24h"),
                        "rsi": market_data.get("rsi")
                    }
                }]
            }
        except Exception as e:
            logger.error(f"Error fetching market data: {e}")
            return {
                "status": "error",
                "error": str(e),
                "messages": [{
                    "type": "error",
                    "content": f"Failed to fetch market data: {e}"
                }]
            }
    
    async def _bull_argues(self, state: AgentState) -> Dict[str, Any]:
        """Bull agent makes its argument"""
        logger.info(f"Bull agent analyzing (round {state['current_round'] + 1})")
        
        is_counter = state['current_round'] > 0
        
        if is_counter and state['bear_arguments']:
            # Counter-argument mode
            last_bear_arg = state['bear_arguments'][-1]
            result = await self.bull_agent.counter_argue(
                last_bear_arg['argument'],
                state['market_data']
            )
        else:
            # Initial argument
            result = await self.bull_agent.analyze(
                state['market_data'],
                state['user_query']
            )
        
        return {
            "bull_arguments": [result],
            "status": "bull_argued",
            "messages": [{
                "type": "bull",
                "content": result['argument'],
                "confidence": result.get('confidence', 65),
                "key_points": result.get('key_points', []),
                "round": state['current_round'] + 1
            }]
        }
    
    async def _bear_argues(self, state: AgentState) -> Dict[str, Any]:
        """Bear agent makes its argument"""
        logger.info(f"Bear agent analyzing (round {state['current_round'] + 1})")
        
        is_counter = state['current_round'] > 0
        
        if is_counter and state['bull_arguments']:
            # Counter-argument mode
            last_bull_arg = state['bull_arguments'][-1]
            result = await self.bear_agent.counter_argue(
                last_bull_arg['argument'],
                state['market_data']
            )
        else:
            # Initial argument
            result = await self.bear_agent.analyze(
                state['market_data'],
                state['user_query']
            )
        
        return {
            "bear_arguments": [result],
            "status": "bear_argued",
            "messages": [{
                "type": "bear",
                "content": result['argument'],
                "confidence": result.get('confidence', 65),
                "key_points": result.get('key_points', []),
                "round": state['current_round'] + 1
            }]
        }
    
    async def _check_debate_rounds(self, state: AgentState) -> Dict[str, Any]:
        """Check if we should continue the debate"""
        new_round = state['current_round'] + 1
        
        return {
            "current_round": new_round,
            "debate_rounds": [{
                "round": new_round,
                "bull": state['bull_arguments'][-1] if state['bull_arguments'] else None,
                "bear": state['bear_arguments'][-1] if state['bear_arguments'] else None,
            }]
        }
    
    def _should_continue_debate(self, state: AgentState) -> Literal["continue", "conclude"]:
        """Decide whether to continue debating or conclude"""
        if state['current_round'] < state['max_rounds']:
            return "continue"
        return "conclude"
    
    async def _referee_decides(self, state: AgentState) -> Dict[str, Any]:
        """Referee evaluates and picks a winner"""
        logger.info("Referee evaluating debate")
        
        verdict = await self.referee_agent.evaluate(
            state['bull_arguments'],
            state['bear_arguments'],
            state['market_data'],
            state['user_query']
        )
        
        return {
            "verdict": verdict,
            "status": "verdict_rendered",
            "messages": [{
                "type": "referee",
                "content": verdict['reasoning'],
                "winner": verdict['winner'],
                "confidence_score": verdict['confidence_score'],
                "wager_amount": verdict['wager_amount'],
                "key_factors": verdict.get('key_factors', [])
            }]
        }
    
    async def _execute_hedera(self, state: AgentState) -> Dict[str, Any]:
        """Execute Hedera transactions (HCS log + wager)"""
        logger.info("Executing Hedera transactions")
        
        verdict = state['verdict']
        
        # Create debate summary for HCS
        debate_summary = {
            "type": "AlphaDuel_Prediction",
            "symbol": state['symbol'],
            "query": state['user_query'],
            "winner": verdict['winner'],
            "confidence": verdict['confidence_score'],
            "wager_amount": verdict['wager_amount'],
            "key_factors": verdict.get('key_factors', []),
            "market_snapshot": {
                "price": state['market_data'].get('current_price'),
                "rsi": state['market_data'].get('rsi'),
            }
        }
        
        # Log to HCS
        hcs_tx = await self.hedera_service.log_to_hcs(debate_summary)
        
        # Execute wager transfer
        wager_tx = await self.hedera_service.transfer_hbar(
            amount=verdict['wager_amount'],
            memo=f"AlphaDuel: {verdict['winner']} wins with {verdict['confidence_score']}% confidence"
        )
        
        return {
            "hcs_tx": hcs_tx,
            "wager_tx": wager_tx,
            "status": "completed",
            "messages": [{
                "type": "hedera",
                "content": "Transactions executed on Hedera Testnet",
                "hcs_tx": hcs_tx,
                "wager_tx": wager_tx
            }]
        }
    
    async def run(self, user_query: str, symbol: str = "HBAR") -> AsyncGenerator[Dict[str, Any], None]:
        """
        Run the debate and yield messages as they are generated
        
        Args:
            user_query: The user's question
            symbol: The cryptocurrency symbol to analyze
            
        Yields:
            Messages from each step of the debate
        """
        initial_state = create_initial_state(user_query, symbol)
        
        # Stream through the graph
        async for event in self.graph.astream(initial_state):
            # Each event is a dict with node_name: output
            for node_name, output in event.items():
                if "messages" in output:
                    for message in output["messages"]:
                        yield {
                            "node": node_name,
                            **message
                        }
                
                # Also yield status updates
                if "status" in output:
                    yield {
                        "node": node_name,
                        "type": "status",
                        "status": output["status"]
                    }
    
    async def run_complete(self, user_query: str, symbol: str = "HBAR") -> AgentState:
        """Run the complete debate and return final state"""
        initial_state = create_initial_state(user_query, symbol)
        
        result = await self.graph.ainvoke(initial_state)
        return result


def create_debate_graph(
    market_service: MarketDataService,
    hedera_service: HederaService,
    model: str = "gpt-4.1",
    api_key: Optional[str] = None
) -> DebateGraph:
    """Factory function to create a debate graph"""
    return DebateGraph(market_service, hedera_service, model, api_key)


async def run_debate(
    user_query: str,
    symbol: str = "HBAR",
    market_service: MarketDataService = None,
    hedera_service: HederaService = None,
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Convenience function to run a debate
    
    Args:
        user_query: The user's question
        symbol: The cryptocurrency symbol
        market_service: Optional market data service
        hedera_service: Optional Hedera service
        
    Yields:
        Messages from the debate
    """
    if market_service is None:
        market_service = MarketDataService()
    
    if hedera_service is None:
        hedera_service = HederaService(
            account_id="",
            private_key="",
            escrow_account_id=""
        )
    
    graph = create_debate_graph(market_service, hedera_service)
    
    async for message in graph.run(user_query, symbol):
        yield message

