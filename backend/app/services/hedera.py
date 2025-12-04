"""
Hedera Service - Handles HCS logging and HBAR transfers
Using the official Hiero SDK: https://github.com/hiero-ledger/hiero-sdk-python
"""
import json
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime
import logging
import hashlib

logger = logging.getLogger(__name__)


class HederaService:
    """
    Service to interact with Hedera Blockchain using the Hiero Python SDK.
    
    This implementation provides both real Hedera SDK integration
    and a simulation mode for development/testing without real credentials.
    
    SDK Reference: https://github.com/hiero-ledger/hiero-sdk-python
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
        self.topic_id = topic_id
        self.client = None
        self.operator_id = None
        self.operator_key = None
        self.is_simulation = not (account_id and private_key)
        
        if not self.is_simulation:
            self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the Hedera client using Hiero SDK"""
        try:
            # Import from hiero_sdk_python (official Hedera Python SDK)
            from hiero_sdk_python import (
                Client,
                AccountId,
                PrivateKey,
            )
            
            # Create client for testnet or mainnet
            if self.network == "testnet":
                self.client = Client.for_testnet()
            else:
                self.client = Client.for_mainnet()
            
            # Parse operator credentials
            self.operator_id = AccountId.from_string(self.account_id)
            self.operator_key = PrivateKey.from_string(self.private_key)
            
            # Set the operator (payer account)
            self.client.set_operator(self.operator_id, self.operator_key)
            
            logger.info(f"Hedera client initialized for {self.network} using Hiero SDK")
            
        except ImportError as e:
            logger.warning(f"Hiero SDK not installed ({e}), using simulation mode")
            self.is_simulation = True
        except Exception as e:
            logger.error(f"Failed to initialize Hedera client: {e}")
            self.is_simulation = True
    
    async def create_topic(self, memo: str = "AlphaDuel Debate Log") -> str:
        """Create a new HCS topic for logging debates"""
        if self.is_simulation:
            # Generate a simulated topic ID
            topic_id = f"0.0.{abs(hash(memo)) % 10000000}"
            logger.info(f"[SIMULATION] Created topic: {topic_id}")
            return topic_id
        
        try:
            from hiero_sdk_python import TopicCreateTransaction
            
            # Create the topic
            transaction = TopicCreateTransaction()
            transaction.set_topic_memo(memo)
            
            # Execute the transaction
            response = await asyncio.to_thread(transaction.execute, self.client)
            receipt = await asyncio.to_thread(response.get_receipt, self.client)
            
            topic_id = str(receipt.topic_id)
            self.topic_id = topic_id
            logger.info(f"Created HCS topic: {topic_id}")
            
            return topic_id
            
        except Exception as e:
            logger.error(f"Error creating topic: {e}")
            raise
    
    async def log_to_hcs(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Log a message to Hedera Consensus Service
        
        Args:
            message: The message to log (will be JSON serialized)
            
        Returns:
            Transaction details including tx_id and hashscan URL
        """
        message_str = json.dumps(message, default=str)
        timestamp = datetime.utcnow().isoformat()
        
        if self.is_simulation:
            # Generate a simulated transaction ID
            tx_hash = hashlib.sha256(f"{timestamp}{message_str}".encode()).hexdigest()[:24]
            tx_id = f"{self.account_id or '0.0.12345'}@{int(datetime.utcnow().timestamp())}"
            
            logger.info(f"[SIMULATION] Logged to HCS: {tx_id}")
            
            return {
                "tx_id": tx_id,
                "tx_type": "HCS_LOG",
                "status": "SUCCESS",
                "topic_id": self.topic_id or "0.0.1234567",
                "hashscan_url": f"{self.HASHSCAN_TESTNET_URL}/transaction/{tx_id.replace('@', '-').replace('.', '')}",
                "message_preview": message_str[:100],
                "timestamp": timestamp,
                "simulation": True
            }
        
        try:
            from hiero_sdk_python import TopicMessageSubmitTransaction, TopicId
            
            # Create topic if not exists
            if not self.topic_id:
                self.topic_id = await self.create_topic()
            
            # Submit message to the topic
            transaction = TopicMessageSubmitTransaction()
            transaction.set_topic_id(TopicId.from_string(self.topic_id))
            transaction.set_message(message_str)
            
            # Execute the transaction
            response = await asyncio.to_thread(transaction.execute, self.client)
            receipt = await asyncio.to_thread(response.get_receipt, self.client)
            
            tx_id = str(response.transaction_id)
            
            return {
                "tx_id": tx_id,
                "tx_type": "HCS_LOG",
                "status": str(receipt.status),
                "topic_id": self.topic_id,
                "hashscan_url": f"{self.HASHSCAN_TESTNET_URL}/transaction/{tx_id.replace('@', '-').replace('.', '')}",
                "message_preview": message_str[:100],
                "timestamp": timestamp,
                "simulation": False
            }
            
        except Exception as e:
            logger.error(f"Error logging to HCS: {e}")
            raise
    
    async def transfer_hbar(self, amount: float, memo: str = "") -> Dict[str, Any]:
        """
        Transfer HBAR to the escrow account (the wager)
        
        Args:
            amount: Amount of HBAR to transfer
            memo: Transaction memo
            
        Returns:
            Transaction details including tx_id and hashscan URL
        """
        timestamp = datetime.utcnow().isoformat()
        
        if self.is_simulation:
            # Generate a simulated transaction ID
            tx_id = f"{self.account_id or '0.0.12345'}@{int(datetime.utcnow().timestamp())}"
            
            logger.info(f"[SIMULATION] Transferred {amount} HBAR: {tx_id}")
            
            return {
                "tx_id": tx_id,
                "tx_type": "TRANSFER",
                "status": "SUCCESS",
                "amount": amount,
                "from_account": self.account_id or "0.0.12345",
                "to_account": self.escrow_account_id or "0.0.67890",
                "hashscan_url": f"{self.HASHSCAN_TESTNET_URL}/transaction/{tx_id.replace('@', '-').replace('.', '')}",
                "memo": memo,
                "timestamp": timestamp,
                "simulation": True
            }
        
        try:
            from hiero_sdk_python import (
                TransferTransaction,
                AccountId,
                Hbar,
            )
            
            sender = AccountId.from_string(self.account_id)
            receiver = AccountId.from_string(self.escrow_account_id)
            
            # Create transfer transaction
            transaction = TransferTransaction()
            transaction.add_hbar_transfer(sender, Hbar.from_tinybars(-int(amount * 100_000_000)))  # Negative for sender
            transaction.add_hbar_transfer(receiver, Hbar.from_tinybars(int(amount * 100_000_000)))  # Positive for receiver
            
            if memo:
                transaction.set_transaction_memo(memo)
            
            # Execute the transaction
            response = await asyncio.to_thread(transaction.execute, self.client)
            receipt = await asyncio.to_thread(response.get_receipt, self.client)
            
            tx_id = str(response.transaction_id)
            
            return {
                "tx_id": tx_id,
                "tx_type": "TRANSFER",
                "status": str(receipt.status),
                "amount": amount,
                "from_account": self.account_id,
                "to_account": self.escrow_account_id,
                "hashscan_url": f"{self.HASHSCAN_TESTNET_URL}/transaction/{tx_id.replace('@', '-').replace('.', '')}",
                "memo": memo,
                "timestamp": timestamp,
                "simulation": False
            }
            
        except Exception as e:
            logger.error(f"Error transferring HBAR: {e}")
            raise
    
    async def get_account_balance(self) -> Optional[float]:
        """Get the HBAR balance of the operator account"""
        if self.is_simulation:
            return 1000.0  # Mock balance
        
        try:
            from hiero_sdk_python import AccountBalanceQuery
            
            balance = AccountBalanceQuery(account_id=self.operator_id).execute(self.client)
            return float(balance.hbars)
            
        except Exception as e:
            logger.error(f"Error getting balance: {e}")
            return None
    
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
