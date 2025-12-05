"""
Referee Agent - The impartial judge
"""
from typing import Dict, Any, List, Optional, AsyncGenerator
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
import json
import re
import os

from .prompts import REFEREE_SYSTEM_PROMPT
from ..config import get_settings


class RefereeAgent:
    """Referee Agent that evaluates the debate and determines a winner"""
    
    def __init__(self, model: str = "gpt-4.1", temperature: Optional[float] = None, api_key: Optional[str] = None):
        # Use a more capable model for judgment with lower temperature for consistency
        settings = get_settings()
        openai_api_key = api_key or settings.openai_api_key
        temp = temperature if temperature is not None else settings.referee_temperature
        self.llm = ChatOpenAI(model=model, temperature=temp, api_key=openai_api_key)
        self.system_prompt = REFEREE_SYSTEM_PROMPT
    
    async def evaluate(
        self,
        bull_arguments: List[Dict[str, Any]],
        bear_arguments: List[Dict[str, Any]],
        market_data: Dict[str, Any],
        user_query: str
    ) -> Dict[str, Any]:
        """
        Evaluate the debate and determine a winner
        
        Args:
            bull_arguments: List of bull agent's arguments
            bear_arguments: List of bear agent's arguments
            market_data: Current market data
            user_query: Original user question
            
        Returns:
            Verdict with winner, confidence score, and reasoning
        """
        # Format the debate for the referee
        debate_summary = self._format_debate(bull_arguments, bear_arguments)
        
        prompt = f"""
User's Original Question: {user_query}

Asset: {market_data.get('symbol', 'N/A')}
Current Price: ${market_data.get('current_price', 0):.4f}
24h Change: {market_data.get('price_change_percentage_24h', 0):.2f}%
RSI: {market_data.get('rsi', 50):.1f}

=== DEBATE TRANSCRIPT ===

{debate_summary}

=== END DEBATE ===

Based on the arguments presented, provide your verdict as a JSON object.
Remember to be objective and base your decision on the quality of arguments and evidence presented.
"""
        
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        verdict = self._parse_verdict(response.content)
        
        # Calculate wager based on confidence
        verdict["wager_amount"] = self._calculate_wager(verdict.get("confidence_score", 50))
        
        return verdict
    
    async def evaluate_stream(
        self,
        bull_arguments: List[Dict[str, Any]],
        bear_arguments: List[Dict[str, Any]],
        market_data: Dict[str, Any],
        user_query: str
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream evaluation of the debate and determine a winner
        
        Args:
            bull_arguments: List of bull agent's arguments
            bear_arguments: List of bear agent's arguments
            market_data: Current market data
            user_query: Original user question
            
        Yields:
            Streaming tokens and final verdict with winner, confidence score, and reasoning
        """
        # Format the debate for the referee
        debate_summary = self._format_debate(bull_arguments, bear_arguments)
        
        prompt = f"""
User's Original Question: {user_query}

Asset: {market_data.get('symbol', 'N/A')}
Current Price: ${market_data.get('current_price', 0):.4f}
24h Change: {market_data.get('price_change_percentage_24h', 0):.2f}%
RSI: {market_data.get('rsi', 50):.1f}

=== DEBATE TRANSCRIPT ===

{debate_summary}

=== END DEBATE ===

Based on the arguments presented, provide your verdict as a JSON object.
Remember to be objective and base your decision on the quality of arguments and evidence presented.
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
                    "agent": "Referee",
                    "token": token,
                }
        
        # Parse and yield final verdict
        verdict = self._parse_verdict(full_content)
        verdict["wager_amount"] = self._calculate_wager(verdict.get("confidence_score", 50))
        
        yield {
            "type": "complete",
            "agent": "Referee",
            **verdict,
        }
    
    def _format_debate(
        self,
        bull_arguments: List[Dict[str, Any]],
        bear_arguments: List[Dict[str, Any]]
    ) -> str:
        """Format the debate arguments into a readable transcript"""
        lines = []
        
        # Interleave arguments by round
        max_rounds = max(len(bull_arguments), len(bear_arguments))
        
        for i in range(max_rounds):
            if i < len(bull_arguments):
                arg = bull_arguments[i]
                arg_type = "Initial Argument" if i == 0 else f"Counter-Argument {i}"
                lines.append(f"🐂 BULL AGENT ({arg_type}):")
                lines.append(arg.get('argument', ''))
                lines.append(f"Stated Confidence: {arg.get('confidence', 'N/A')}%")
                lines.append("")
            
            if i < len(bear_arguments):
                arg = bear_arguments[i]
                arg_type = "Initial Argument" if i == 0 else f"Counter-Argument {i}"
                lines.append(f"🐻 BEAR AGENT ({arg_type}):")
                lines.append(arg.get('argument', ''))
                lines.append(f"Stated Confidence: {arg.get('confidence', 'N/A')}%")
                lines.append("")
        
        return "\n".join(lines)
    
    def _parse_verdict(self, response: str) -> Dict[str, Any]:
        """Parse the referee's response into a structured verdict"""
        # Try to extract JSON from the response
        try:
            # Look for JSON in the response
            json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
            if json_match:
                verdict = json.loads(json_match.group())
                return {
                    "winner": verdict.get("winner", "Bull"),
                    "confidence_score": float(verdict.get("confidence_score", 50)),
                    "reasoning": verdict.get("reasoning", response),
                    "key_factors": verdict.get("key_factors", []),
                }
        except json.JSONDecodeError:
            pass
        
        # Fallback: Parse manually
        winner = "Bull" if "bull" in response.lower()[:200] else "Bear"
        
        # Try to extract confidence
        confidence = 50.0
        conf_match = re.search(r'confidence[:\s]*(\d+)', response.lower())
        if conf_match:
            confidence = float(conf_match.group(1))
        
        return {
            "winner": winner,
            "confidence_score": confidence,
            "reasoning": response,
            "key_factors": self._extract_factors(response),
        }
    
    def _extract_factors(self, text: str) -> List[str]:
        """Extract key factors from the reasoning"""
        factors = []
        
        # Look for numbered points or bullet points
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith(('•', '-', '*', '1.', '2.', '3.', '4.', '5.')):
                clean_line = re.sub(r'^[•\-*\d.]+\s*', '', line).strip()
                if clean_line and len(clean_line) > 10:
                    factors.append(clean_line[:200])
        
        return factors[:5]
    
    def _calculate_wager(self, confidence_score: float, base_amount: float = 10.0) -> float:
        """Calculate wager amount based on confidence"""
        # Scale: 0-40% confidence = 10% of base, 40-70% = 50%, 70-100% = 100%
        if confidence_score < 40:
            multiplier = 0.1
        elif confidence_score < 70:
            multiplier = 0.5
        else:
            multiplier = 1.0
        
        return round(base_amount * multiplier, 2)

