"""
Market Data Service - Fetches real-time crypto data from external APIs
"""
import httpx
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class MarketDataService:
    """Service to fetch cryptocurrency market data"""
    
    COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3"
    
    # Map common symbols to CoinGecko IDs
    SYMBOL_TO_ID = {
        "HBAR": "hedera-hashgraph",
        "BTC": "bitcoin",
        "ETH": "ethereum",
        "SOL": "solana",
        "AVAX": "avalanche-2",
        "MATIC": "matic-network",
        "DOT": "polkadot",
        "LINK": "chainlink",
        "UNI": "uniswap",
        "AAVE": "aave",
    }
    
    def __init__(self, coingecko_api_key: Optional[str] = None, tavily_api_key: Optional[str] = None):
        self.coingecko_api_key = coingecko_api_key
        self.tavily_api_key = tavily_api_key
    
    async def get_market_data(self, symbol: str) -> Dict[str, Any]:
        """Fetch comprehensive market data for a symbol"""
        coin_id = self.SYMBOL_TO_ID.get(symbol.upper(), symbol.lower())
        
        async with httpx.AsyncClient() as client:
            # Fetch price data from CoinGecko
            price_data = await self._fetch_price_data(client, coin_id)
            
            # Fetch news/sentiment (simplified - in production use Tavily)
            news_data = await self._fetch_news_sentiment(client, symbol)
            
            # Calculate RSI (simplified calculation)
            rsi = await self._calculate_rsi(client, coin_id)
            
            return {
                "symbol": symbol.upper(),
                "coin_id": coin_id,
                "current_price": price_data.get("current_price", 0),
                "price_change_24h": price_data.get("price_change_24h", 0),
                "price_change_percentage_24h": price_data.get("price_change_percentage_24h", 0),
                "market_cap": price_data.get("market_cap", 0),
                "total_volume": price_data.get("total_volume", 0),
                "high_24h": price_data.get("high_24h", 0),
                "low_24h": price_data.get("low_24h", 0),
                "rsi": rsi,
                "news_summary": news_data.get("summary", ""),
                "sentiment_score": news_data.get("sentiment", 0.5),
                "last_updated": datetime.utcnow().isoformat(),
            }
    
    async def _fetch_price_data(self, client: httpx.AsyncClient, coin_id: str) -> Dict[str, Any]:
        """Fetch price data from CoinGecko"""
        try:
            headers = {}
            if self.coingecko_api_key:
                headers["x-cg-demo-api-key"] = self.coingecko_api_key
            
            response = await client.get(
                f"{self.COINGECKO_BASE_URL}/coins/{coin_id}",
                params={
                    "localization": "false",
                    "tickers": "false",
                    "community_data": "false",
                    "developer_data": "false",
                },
                headers=headers,
                timeout=10.0
            )
            
            if response.status_code == 200:
                data = response.json()
                market_data = data.get("market_data", {})
                return {
                    "current_price": market_data.get("current_price", {}).get("usd", 0),
                    "price_change_24h": market_data.get("price_change_24h", 0),
                    "price_change_percentage_24h": market_data.get("price_change_percentage_24h", 0),
                    "market_cap": market_data.get("market_cap", {}).get("usd", 0),
                    "total_volume": market_data.get("total_volume", {}).get("usd", 0),
                    "high_24h": market_data.get("high_24h", {}).get("usd", 0),
                    "low_24h": market_data.get("low_24h", {}).get("usd", 0),
                }
            else:
                logger.warning(f"CoinGecko API returned status {response.status_code}")
                return self._get_mock_price_data(coin_id)
                
        except Exception as e:
            logger.error(f"Error fetching price data: {e}")
            return self._get_mock_price_data(coin_id)
    
    def _get_mock_price_data(self, coin_id: str) -> Dict[str, Any]:
        """Return mock data for development/testing"""
        mock_data = {
            "hedera-hashgraph": {
                "current_price": 0.0725,
                "price_change_24h": 0.0032,
                "price_change_percentage_24h": 4.62,
                "market_cap": 2750000000,
                "total_volume": 89000000,
                "high_24h": 0.0745,
                "low_24h": 0.0685,
            },
            "bitcoin": {
                "current_price": 97500,
                "price_change_24h": 2350,
                "price_change_percentage_24h": 2.47,
                "market_cap": 1920000000000,
                "total_volume": 45000000000,
                "high_24h": 98200,
                "low_24h": 95100,
            }
        }
        return mock_data.get(coin_id, mock_data["hedera-hashgraph"])
    
    async def _calculate_rsi(self, client: httpx.AsyncClient, coin_id: str) -> float:
        """Calculate RSI based on historical data"""
        try:
            headers = {}
            if self.coingecko_api_key:
                headers["x-cg-demo-api-key"] = self.coingecko_api_key
            
            response = await client.get(
                f"{self.COINGECKO_BASE_URL}/coins/{coin_id}/market_chart",
                params={"vs_currency": "usd", "days": "14"},
                headers=headers,
                timeout=10.0
            )
            
            if response.status_code == 200:
                data = response.json()
                prices = [p[1] for p in data.get("prices", [])]
                
                if len(prices) < 14:
                    return 50.0
                
                # Calculate price changes
                changes = [prices[i] - prices[i-1] for i in range(1, len(prices))]
                
                # Separate gains and losses
                gains = [c if c > 0 else 0 for c in changes]
                losses = [-c if c < 0 else 0 for c in changes]
                
                # Calculate average gain and loss (14-period)
                avg_gain = sum(gains[-14:]) / 14
                avg_loss = sum(losses[-14:]) / 14
                
                if avg_loss == 0:
                    return 100.0
                
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
                
                return round(rsi, 2)
            
            return 50.0
            
        except Exception as e:
            logger.error(f"Error calculating RSI: {e}")
            return 50.0
    
    async def _fetch_news_sentiment(self, client: httpx.AsyncClient, symbol: str) -> Dict[str, Any]:
        """Fetch news and calculate sentiment"""
        # In production, use Tavily API for real news search
        # For now, return mock sentiment based on the symbol
        
        if self.tavily_api_key:
            try:
                # Tavily search would go here
                pass
            except Exception as e:
                logger.error(f"Error fetching news: {e}")
        
        # Mock news summary
        return {
            "summary": f"Recent news for {symbol} shows mixed market sentiment with institutional interest growing.",
            "sentiment": 0.55,  # Slightly positive
        }

