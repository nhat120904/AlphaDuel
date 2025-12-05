"""
Configuration settings for AlphaDuel Backend
"""
import os
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # OpenAI
    openai_api_key: str = ""
    
    # Hedera Testnet
    hedera_account_id: str = ""
    hedera_private_key: str = ""
    hedera_escrow_account_id: str = ""
    hedera_network: str = "testnet"
    
    # External APIs
    tavily_api_key: str = ""
    coingecko_api_key: str = ""
    
    # App Config
    debug: bool = True
    app_name: str = "AlphaDuel"
    
    # HCS Topic (will be created on first run if not set)
    hcs_topic_id: str = ""
    
    # LLM Temperature Settings
    bull_temperature: float = 0
    bear_temperature: float = 0
    referee_temperature: float = 0
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()

