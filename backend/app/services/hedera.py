"""
Hedera Service - Handles debate logging to local file for blockchain record
This is a simplified implementation that logs to local files
For production, replace with actual Hedera SDK integration
"""
import json
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime
import logging
import hashlib
import os

logger = logging.getLogger(__name__)


class HederaService:
    """
    Service to log debate results to local files (blockchain simulation)
    
    This implementation logs debate results to local files for record keeping.
    Replace with actual Hedera SDK when production-ready environment is available.
    """
    
    HASHSCAN_TESTNET_URL = "https://hashscan.io/testnet"
    
    def __init__(
        self,
        account_id: str,
        private_key: str,
        escrow_account_id: str,
        network: str = "testnet",
        topic_id: Optional[str] = None
    ):
        self.account_id = account_id
        self.private_key = private_key
        self.escrow_account_id = escrow_account_id
        self.network = network
        self.topic_id = topic_id or "0.0.1234567"
        
        # Create logs directory if it doesn't exist
        self.logs_dir = "hedera_logs"
        os.makedirs(self.logs_dir, exist_ok=True)
        
        logger.info(f"Hedera service initialized for {self.network} (file-based logging)")
    
    async def create_topic(self, memo: str = "AlphaDuel Debate Log") -> str:
        """Create a new topic for logging debates"""
        topic_id = f"0.0.{abs(hash(memo)) % 10000000}"
        self.topic_id = topic_id
        
        # Log topic creation
        topic_log = {
            "action": "create_topic",
            "topic_id": topic_id,
            "memo": memo,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        log_file = os.path.join(self.logs_dir, f"topic_{topic_id}.json")
        with open(log_file, 'w') as f:
            json.dump(topic_log, f, indent=2)
        
        logger.info(f"Created topic: {topic_id}")
        return topic_id
    
    async def log_to_hcs(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Log a message to Hedera Consensus Service (file-based)
        
        Args:
            message: The message to log (will be JSON serialized)
            
        Returns:
            Transaction details including tx_id and file path
        """
        message_str = json.dumps(message, default=str)
        timestamp = datetime.utcnow().isoformat()
        
        # Generate transaction ID
        tx_hash = hashlib.sha256(f"{timestamp}{message_str}".encode()).hexdigest()[:16]
        tx_id = f"{self.account_id}@{int(datetime.utcnow().timestamp())}"
        
        # Create log entry
        log_entry = {
            "tx_id": tx_id,
            "tx_type": "HCS_LOG",
            "status": "SUCCESS",
            "topic_id": self.topic_id,
            "message": message,
            "timestamp": timestamp,
            "network": self.network
        }
        
        # Save to file
        log_file = os.path.join(self.logs_dir, f"hcs_log_{tx_hash}.json")
        with open(log_file, 'w') as f:
            json.dump(log_entry, f, indent=2)
        
        logger.info(f"Logged to HCS: {tx_id} -> {log_file}")
        
        return {
            "tx_id": tx_id,
            "tx_type": "HCS_LOG",
            "status": "SUCCESS",
            "topic_id": self.topic_id,
            "hashscan_url": f"{self.HASHSCAN_TESTNET_URL}/transaction/{tx_id.replace('@', '-').replace('.', '')}",
            "message_preview": message_str[:100],
            "timestamp": timestamp,
            "log_file": log_file
        }
    
    async def transfer_hbar(self, amount: float, memo: str = "") -> Dict[str, Any]:
        """
        Transfer HBAR to the escrow account (file-based logging)
        
        Args:
            amount: Amount of HBAR to transfer
            memo: Transaction memo
            
        Returns:
            Transaction details including tx_id and file path
        """
        timestamp = datetime.utcnow().isoformat()
        
        # Generate transaction ID
        tx_id = f"{self.account_id}@{int(datetime.utcnow().timestamp())}"
        
        # Create transfer log entry
        transfer_entry = {
            "tx_id": tx_id,
            "tx_type": "TRANSFER",
            "status": "SUCCESS",
            "amount": amount,
            "from_account": self.account_id,
            "to_account": self.escrow_account_id,
            "memo": memo,
            "timestamp": timestamp,
            "network": self.network
        }
        
        # Save to file
        transfer_hash = hashlib.sha256(f"{tx_id}{amount}".encode()).hexdigest()[:16]
        log_file = os.path.join(self.logs_dir, f"transfer_{transfer_hash}.json")
        with open(log_file, 'w') as f:
            json.dump(transfer_entry, f, indent=2)
        
        logger.info(f"Transferred {amount} HBAR: {tx_id} -> {log_file}")
        
        return {
            "tx_id": tx_id,
            "tx_type": "TRANSFER",
            "status": "SUCCESS",
            "amount": amount,
            "from_account": self.account_id,
            "to_account": self.escrow_account_id,
            "hashscan_url": f"{self.HASHSCAN_TESTNET_URL}/transaction/{tx_id.replace('@', '-').replace('.', '')}",
            "memo": memo,
            "timestamp": timestamp,
            "log_file": log_file
        }
    
    async def get_account_balance(self) -> float:
        """Get the HBAR balance of the operator account (mock)"""
        return 1000.0  # Mock balance
    
    def calculate_wager_amount(self, confidence_score: float, base_amount: float = 10.0) -> float:
        """
        Calculate wager amount based on confidence score
        
        Args:
            confidence_score: Score from 0-100
            base_amount: Base wager amount in HBAR
            
        Returns:
            Calculated wager amount
        """
        # Scale wager based on confidence (higher confidence = higher wager)
        # Min: 10% of base, Max: 100% of base
        multiplier = max(0.1, min(1.0, confidence_score / 100))
        return round(base_amount * multiplier, 2)
