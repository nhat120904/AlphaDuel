"""
LangGraph Debate Orchestration
Manages the stateful workflow between Bull, Bear, and Referee agents
"""
from typing import Dict, Any, AsyncGenerator, Literal, Optional
from langgraph.graph import StateGraph, END
from langgraph.graph.state import CompiledStateGraph
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
    
    def _build_graph(self) -> CompiledStateGraph:
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
        """Bull agent makes its argument (non-streaming for graph nodes)"""
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
    
    async def _bull_argues_stream(
        self, state: AgentState
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Bull agent makes its argument with streaming"""
        logger.info(f"Bull agent analyzing (round {state['current_round'] + 1}) - streaming")
        
        is_counter = state['current_round'] > 0
        result = None
        
        if is_counter and state['bear_arguments']:
            # Counter-argument mode with streaming
            last_bear_arg = state['bear_arguments'][-1]
            async for chunk in self.bull_agent.counter_argue_stream(
                last_bear_arg['argument'],
                state['market_data']
            ):
                if chunk["type"] == "token":
                    yield {
                        "node": "bull_argues",
                        "type": "bull_token",
                        "token": chunk["token"],
                        "round": state['current_round'] + 1
                    }
                elif chunk["type"] == "complete":
                    result = chunk
        else:
            # Initial argument with streaming
            async for chunk in self.bull_agent.analyze_stream(
                state['market_data'],
                state['user_query']
            ):
                if chunk["type"] == "token":
                    yield {
                        "node": "bull_argues",
                        "type": "bull_token",
                        "token": chunk["token"],
                        "round": state['current_round'] + 1
                    }
                elif chunk["type"] == "complete":
                    result = chunk
        
        # Yield the complete message at the end
        if result:
            yield {
                "node": "bull_argues",
                "type": "bull_complete",
                "content": result.get('argument', ''),
                "confidence": result.get('confidence', 65),
                "key_points": result.get('key_points', []),
                "round": state['current_round'] + 1,
                "result": result
            }
    
    async def _bear_argues(self, state: AgentState) -> Dict[str, Any]:
        """Bear agent makes its argument (non-streaming for graph nodes)"""
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
    
    async def _bear_argues_stream(
        self, state: AgentState
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Bear agent makes its argument with streaming"""
        logger.info(f"Bear agent analyzing (round {state['current_round'] + 1}) - streaming")
        
        is_counter = state['current_round'] > 0
        result = None
        
        if is_counter and state['bull_arguments']:
            # Counter-argument mode with streaming
            last_bull_arg = state['bull_arguments'][-1]
            async for chunk in self.bear_agent.counter_argue_stream(
                last_bull_arg['argument'],
                state['market_data']
            ):
                if chunk["type"] == "token":
                    yield {
                        "node": "bear_argues",
                        "type": "bear_token",
                        "token": chunk["token"],
                        "round": state['current_round'] + 1
                    }
                elif chunk["type"] == "complete":
                    result = chunk
        else:
            # Initial argument with streaming
            async for chunk in self.bear_agent.analyze_stream(
                state['market_data'],
                state['user_query']
            ):
                if chunk["type"] == "token":
                    yield {
                        "node": "bear_argues",
                        "type": "bear_token",
                        "token": chunk["token"],
                        "round": state['current_round'] + 1
                    }
                elif chunk["type"] == "complete":
                    result = chunk
        
        # Yield the complete message at the end
        if result:
            yield {
                "node": "bear_argues",
                "type": "bear_complete",
                "content": result.get('argument', ''),
                "confidence": result.get('confidence', 65),
                "key_points": result.get('key_points', []),
                "round": state['current_round'] + 1,
                "result": result
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
        """Referee evaluates and picks a winner (non-streaming for graph nodes)"""
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
    
    async def _referee_decides_stream(
        self, state: AgentState
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Referee evaluates and picks a winner with streaming"""
        logger.info("Referee evaluating debate - streaming")
        
        verdict = None
        async for chunk in self.referee_agent.evaluate_stream(
            state['bull_arguments'],
            state['bear_arguments'],
            state['market_data'],
            state['user_query']
        ):
            if chunk["type"] == "token":
                yield {
                    "node": "referee_decides",
                    "type": "referee_token",
                    "token": chunk["token"],
                }
            elif chunk["type"] == "complete":
                verdict = chunk
        
        # Yield the complete verdict
        if verdict:
            yield {
                "node": "referee_decides",
                "type": "referee_complete",
                "content": verdict.get('reasoning', ''),
                "winner": verdict.get('winner'),
                "confidence_score": verdict.get('confidence_score'),
                "wager_amount": verdict.get('wager_amount'),
                "key_factors": verdict.get('key_factors', []),
                "verdict": verdict
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
        Run the debate and yield messages as they are generated (non-streaming LLM)
        
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
    
    async def run_stream(
        self, user_query: str, symbol: str = "HBAR"
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Run the debate with token-by-token streaming from each agent
        
        Args:
            user_query: The user's question
            symbol: The cryptocurrency symbol to analyze
            
        Yields:
            Streaming tokens and messages from each step of the debate
        """
        state = create_initial_state(user_query, symbol)
        
        # Step 1: Fetch market data (non-streaming, just data fetch)
        yield {
            "node": "fetch_market_data",
            "type": "status",
            "status": "fetching_market_data"
        }
        
        market_result = await self._fetch_market_data(state)
        state["market_data"] = market_result.get("market_data", {})
        state["status"] = market_result.get("status")
        
        if market_result.get("messages"):
            for message in market_result["messages"]:
                yield {"node": "fetch_market_data", **message}
        
        if market_result.get("status") == "error":
            return
        
        # Debate loop
        while state["current_round"] < state["max_rounds"]:
            current_round = state["current_round"]
            
            # Step 2: Bull argues with streaming
            yield {
                "node": "bull_argues",
                "type": "status",
                "status": "bull_analyzing",
                "round": current_round + 1
            }
            
            bull_result = None
            async for chunk in self._bull_argues_stream(state):
                yield chunk
                if chunk.get("type") == "bull_complete":
                    bull_result = chunk.get("result")
            
            if bull_result:
                state["bull_arguments"] = state.get("bull_arguments", []) + [bull_result]
            
            # Step 3: Bear argues with streaming
            yield {
                "node": "bear_argues",
                "type": "status",
                "status": "bear_analyzing",
                "round": current_round + 1
            }
            
            bear_result = None
            async for chunk in self._bear_argues_stream(state):
                yield chunk
                if chunk.get("type") == "bear_complete":
                    bear_result = chunk.get("result")
            
            if bear_result:
                state["bear_arguments"] = state.get("bear_arguments", []) + [bear_result]
            
            # Increment round
            state["current_round"] = current_round + 1
            
            yield {
                "node": "check_debate_rounds",
                "type": "status",
                "status": "round_complete",
                "round": state["current_round"],
                "max_rounds": state["max_rounds"]
            }
        
        # Step 4: Referee decides with streaming
        yield {
            "node": "referee_decides",
            "type": "status",
            "status": "referee_evaluating"
        }
        
        verdict = None
        async for chunk in self._referee_decides_stream(state):
            yield chunk
            if chunk.get("type") == "referee_complete":
                verdict = chunk.get("verdict")
        
        if verdict:
            state["verdict"] = verdict
        
        # Step 5: Execute Hedera transactions
        yield {
            "node": "execute_hedera",
            "type": "status",
            "status": "executing_hedera"
        }
        
        hedera_result = await self._execute_hedera(state)
        
        if hedera_result.get("messages"):
            for message in hedera_result["messages"]:
                yield {"node": "execute_hedera", **message}
        
        yield {
            "node": "complete",
            "type": "status",
            "status": "completed",
            "final_state": {
                "winner": state.get("verdict", {}).get("winner"),
                "confidence_score": state.get("verdict", {}).get("confidence_score"),
                "wager_amount": state.get("verdict", {}).get("wager_amount"),
                "hcs_tx": hedera_result.get("hcs_tx"),
                "wager_tx": hedera_result.get("wager_tx"),
            }
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
    market_service: Optional[MarketDataService] = None,
    hedera_service: Optional[HederaService] = None,
    stream: bool = False,
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Convenience function to run a debate
    
    Args:
        user_query: The user's question
        symbol: The cryptocurrency symbol
        market_service: Optional market data service
        hedera_service: Optional Hedera service
        stream: If True, use token-by-token streaming from agents
        
    Yields:
        Messages from the debate (tokens if stream=True)
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
    
    if stream:
        async for message in graph.run_stream(user_query, symbol):
            yield message
    else:
        async for message in graph.run(user_query, symbol):
            yield message

