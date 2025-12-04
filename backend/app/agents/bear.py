"""
Bear Agent - The cautious market analyst
"""
from typing import Dict, Any, Optional, AsyncGenerator
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
import re
import os

from .prompts import BEAR_SYSTEM_PROMPT, DEBATE_COUNTER_PROMPT


class BearAgent:
    """Bear Agent that argues for downside risks"""
    
    def __init__(self, model: str = "gpt-4.1", temperature: float = 0.7, api_key: Optional[str] = None):
        openai_api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.llm = ChatOpenAI(model=model, temperature=temperature, api_key=openai_api_key)
        self.system_prompt = BEAR_SYSTEM_PROMPT
    
    async def analyze(self, market_data: Dict[str, Any], user_query: str) -> Dict[str, Any]:
        """
        Analyze market data and generate bearish argument
        
        Args:
            market_data: Current market data for the asset
            user_query: The user's original question
            
        Returns:
            Bearish analysis with argument and confidence
        """
        prompt = f"""
User Query: {user_query}

Market Data:
- Symbol: {market_data.get('symbol', 'N/A')}
- Current Price: ${market_data.get('current_price', 0):.4f}
- 24h Change: {market_data.get('price_change_percentage_24h', 0):.2f}%
- 24h High: ${market_data.get('high_24h', 0):.4f}
- 24h Low: ${market_data.get('low_24h', 0):.4f}
- Volume (24h): ${market_data.get('total_volume', 0):,.0f}
- Market Cap: ${market_data.get('market_cap', 0):,.0f}
- RSI (14): {market_data.get('rsi', 50):.1f}
- News Sentiment: {market_data.get('sentiment_score', 0.5):.2f}

News Summary: {market_data.get('news_summary', 'No recent news available.')}

Provide your bearish analysis:
"""
        
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        argument = response.content
        
        # Extract confidence from the response
        confidence = self._extract_confidence(argument)
        key_points = self._extract_key_points(argument)
        
        return {
            "agent": "Bear",
            "argument": argument,
            "confidence": confidence,
            "key_points": key_points,
            "market_data_used": {
                "symbol": market_data.get('symbol'),
                "price": market_data.get('current_price'),
                "rsi": market_data.get('rsi'),
            }
        }
    
    async def counter_argue(self, bull_argument: str, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a counter-argument to the bull's position"""
        prompt = DEBATE_COUNTER_PROMPT.format(opponent_argument=bull_argument)
        
        context = f"""
Remember your bearish stance. Current market data:
- Price: ${market_data.get('current_price', 0):.4f}
- 24h Change: {market_data.get('price_change_percentage_24h', 0):.2f}%
- RSI: {market_data.get('rsi', 50):.1f}

{prompt}
"""
        
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=context)
        ]
        
        response = await self.llm.ainvoke(messages)
        
        return {
            "agent": "Bear",
            "argument": response.content,
            "type": "counter",
        }
    
    async def analyze_stream(
        self, market_data: Dict[str, Any], user_query: str
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream analysis of market data and generate bearish argument token by token
        
        Args:
            market_data: Current market data for the asset
            user_query: The user's original question
            
        Yields:
            Streaming tokens and final result with confidence/key_points
        """
        prompt = f"""
User Query: {user_query}

Market Data:
- Symbol: {market_data.get('symbol', 'N/A')}
- Current Price: ${market_data.get('current_price', 0):.4f}
- 24h Change: {market_data.get('price_change_percentage_24h', 0):.2f}%
- 24h High: ${market_data.get('high_24h', 0):.4f}
- 24h Low: ${market_data.get('low_24h', 0):.4f}
- Volume (24h): ${market_data.get('total_volume', 0):,.0f}
- Market Cap: ${market_data.get('market_cap', 0):,.0f}
- RSI (14): {market_data.get('rsi', 50):.1f}
- News Sentiment: {market_data.get('sentiment_score', 0.5):.2f}

News Summary: {market_data.get('news_summary', 'No recent news available.')}

Provide your bearish analysis:
"""
        
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=prompt)
        ]
        
        full_content = ""
        async for chunk in self.llm.astream(messages):
            token = chunk.content if isinstance(chunk.content, str) else ""
            if token:
                full_content += token
                yield {
                    "type": "token",
                    "agent": "Bear",
                    "token": token,
                }
        
        # Yield final result with extracted metadata
        confidence = self._extract_confidence(full_content)
        key_points = self._extract_key_points(full_content)
        
        yield {
            "type": "complete",
            "agent": "Bear",
            "argument": full_content,
            "confidence": confidence,
            "key_points": key_points,
            "market_data_used": {
                "symbol": market_data.get('symbol'),
                "price": market_data.get('current_price'),
                "rsi": market_data.get('rsi'),
            }
        }
    
    async def counter_argue_stream(
        self, bull_argument: str, market_data: Dict[str, Any]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream a counter-argument to the bull's position"""
        prompt = DEBATE_COUNTER_PROMPT.format(opponent_argument=bull_argument)
        
        context = f"""
Remember your bearish stance. Current market data:
- Price: ${market_data.get('current_price', 0):.4f}
- 24h Change: {market_data.get('price_change_percentage_24h', 0):.2f}%
- RSI: {market_data.get('rsi', 50):.1f}

{prompt}
"""
        
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=context)
        ]
        
        full_content = ""
        async for chunk in self.llm.astream(messages):
            token = chunk.content if isinstance(chunk.content, str) else ""
            if token:
                full_content += token
                yield {
                    "type": "token",
                    "agent": "Bear",
                    "token": token,
                }
        
        yield {
            "type": "complete",
            "agent": "Bear",
            "argument": full_content,
            "counter": True,
        }
    
    def _extract_confidence(self, text: str) -> float:
        """Extract confidence percentage from text"""
        patterns = [
            r'confidence\s*(?:level)?[:\s]*(\d+)%',
            r'(\d+)%\s*confiden',
            r'confidence[:\s]*(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                return min(100, max(0, float(match.group(1))))
        
        return 65.0
    
    def _extract_key_points(self, text: str) -> list:
        """Extract key bullet points from the argument"""
        points = []
        
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith(('•', '-', '*', '1.', '2.', '3.', '4.', '5.')):
                clean_line = re.sub(r'^[•\-*\d.]+\s*', '', line).strip()
                if clean_line and len(clean_line) > 10:
                    points.append(clean_line[:150])
        
        return points[:5]

