"""
Hedera Service - Real integration using hiero-sdk-python
"""
import json
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime
import logging
import httpx

logger = logging.getLogger(__name__)

try:
    from hedera import (
        Client,
        AccountId,
        PrivateKey,
        TopicId,
        TopicMessageSubmitTransaction,
        TransferTransaction,
        Hbar
    )
    HEDERA_AVAILABLE = True
except Exception as e:
    HEDERA_AVAILABLE = False
    Client = None
    AccountId = None  
    PrivateKey = None
    TopicId = None
    TopicMessageSubmitTransaction = None
    TransferTransaction = None
    Hbar = None
    logger.warning(f"Hedera SDK not available: {e}")



class HederaService:
    """
    Service to interact with Hedera Testnet using hashgraph-sdk
    Uses official Hedera Python SDK for real blockchain transactions
    """
    
    HASHSCAN_TESTNET_URL = "https://hashscan.io/testnet"
    MIRROR_NODE_URL = "https://testnet.mirrornode.hedera.com/api/v1"
    
    def __init__(
        self,
        account_id: str,
        private_key: str,
        escrow_account_id: str,
        network: str = "testnet",
        topic_id: Optional[str] = None
    ):
        if not account_id or not private_key:
            raise Exception("Hedera account ID and private key are required")
        
        if not topic_id:
            raise Exception("HCS_TOPIC_ID must be set in .env file. Create topic manually at https://portal.hedera.com")
            
        self.account_id = account_id
        self.private_key = private_key
        self.escrow_account_id = escrow_account_id
        self.network = network
        self.topic_id = topic_id
        
        # Initialize Hedera client if SDK available
        if HEDERA_AVAILABLE:
            self.client = Client.forTestnet() if network == "testnet" else Client.forMainnet()
            # Remove 0x prefix if present
            key_str = private_key[2:] if private_key.startswith('0x') else private_key
            # Try ECDSA first (hex format suggests ECDSA/secp256k1)
            try:
                priv_key = PrivateKey.fromStringECDSA(key_str)
            except:
                priv_key = PrivateKey.fromStringED25519(key_str)
            
            self.client.setOperator(
                AccountId.fromString(account_id),
                priv_key
            )
            # Parse topic ID to TopicId object
            self.topic_id_obj = TopicId.fromString(topic_id)
            logger.info(f"✅ Hedera service initialized with SDK for {self.network}")
            logger.info(f"Account: {self.account_id}")
            logger.info(f"Topic: {self.topic_id}")
        else:
            self.client = None
            logger.warning(f"⚠️ Hedera service initialized (REST API mode only)")
            logger.info(f"Account: {self.account_id}")
            logger.info(f"Topic: {self.topic_id}")
    
    async def verify_topic(self) -> bool:
        """Verify topic exists on Hedera testnet"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                topic_url = f"{self.MIRROR_NODE_URL}/topics/{self.topic_id}"
                response = await client.get(topic_url)
                if response.status_code == 200:
                    topic_data = response.json()
                    logger.info(f"✅ Topic {self.topic_id} verified on Hedera testnet")
                    logger.info(f"Topic memo: {topic_data.get('memo', 'N/A')}")
                    return True
                else:
                    logger.error(f"❌ Topic {self.topic_id} not found on Hedera testnet")
                    return False
        except Exception as e:
            logger.error(f"Error verifying topic: {e}")
            return False
    
    async def log_to_hcs(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Log debate summary to Hedera Consensus Service
        
        Args:
            message: The message to log (will be JSON serialized)
            
        Returns:
            Transaction details
        """
        message_str = json.dumps(message, default=str)
        timestamp = datetime.utcnow().isoformat()
        
        try:
            # Verify topic exists
            topic_exists = await self.verify_topic()
            if not topic_exists:
                raise Exception(f"Topic {self.topic_id} not found on Hedera testnet")
            
            logger.info(f"📝 Submitting debate summary to topic {self.topic_id}")
            
            if HEDERA_AVAILABLE and self.client:
                # Limit message size (HCS max ~1024 bytes per chunk, keep it smaller for safety)
                if len(message_str) > 800:
                    logger.warning(f"Message too large ({len(message_str)} bytes), truncating to 800 bytes")
                    message_str = message_str[:797] + "..."
                
                # Real submission with SDK
                transaction = TopicMessageSubmitTransaction() \
                    .setTopicId(self.topic_id_obj) \
                    .setMessage(message_str) \
                    .setMaxTransactionFee(Hbar(2))
                
                logger.info(f"Executing transaction (message size: {len(message_str)} bytes)...")
                
                # Execute with longer timeout
                try:
                    response = await asyncio.wait_for(
                        asyncio.to_thread(transaction.execute, self.client),
                        timeout=30.0
                    )
                    receipt = await asyncio.to_thread(response.getReceipt, self.client)
                except asyncio.TimeoutError:
                    logger.error("Transaction timeout after 30s - testnet may be slow or unreachable")
                    raise Exception("Transaction timeout - testnet may be experiencing issues")
                
                tx_id = response.transactionId.toString()
                
                logger.info(f"✅ Message submitted to HCS!")
                logger.info(f"Transaction ID: {tx_id}")
                logger.info(f"Hashscan: {self.HASHSCAN_TESTNET_URL}/transaction/{tx_id}")
                
                return {
                    "tx_id": tx_id,
                    "tx_type": "HCS_LOG",
                    "status": str(receipt.status),
                    "topic_id": self.topic_id,
                    "hashscan_url": f"{self.HASHSCAN_TESTNET_URL}/transaction/{tx_id}",
                    "message_preview": message_str[:100],
                    "timestamp": timestamp
                }
            else:
                # Fallback without SDK
                logger.warning("SDK not available, returning prepared status")
                return {
                    "tx_id": "PENDING",
                    "tx_type": "HCS_LOG",
                    "status": "PREPARED",
                    "topic_id": self.topic_id,
                    "hashscan_url": f"{self.HASHSCAN_TESTNET_URL}/topic/{self.topic_id}",
                    "message_preview": message_str[:100],
                    "timestamp": timestamp,
                    "note": "SDK not available"
                }
                
        except Exception as e:
            logger.error(f"Error logging to HCS: {e}")
            raise
    
    async def transfer_hbar(self, amount: float, memo: str = "") -> Dict[str, Any]:
        """
        Transfer HBAR to escrow account
        
        Args:
            amount: Amount of HBAR to transfer
            memo: Transaction memo
            
        Returns:
            Transaction details
        """
        timestamp = datetime.utcnow().isoformat()
        
        try:
            logger.info(f"💰 Transferring {amount} HBAR to escrow")
            
            if HEDERA_AVAILABLE and self.client:
                # Real transfer with SDK
                from_account = AccountId.fromString(self.account_id)
                to_account = AccountId.fromString(self.escrow_account_id)
                
                transaction = TransferTransaction() \
                    .addHbarTransfer(from_account, Hbar(-amount)) \
                    .addHbarTransfer(to_account, Hbar(amount)) \
                    .setMaxTransactionFee(Hbar(1))
                
                if memo:
                    transaction = transaction.setTransactionMemo(memo)
                
                logger.info(f"Executing transfer transaction...")
                
                try:
                    response = await asyncio.wait_for(
                        asyncio.to_thread(transaction.execute, self.client),
                        timeout=30.0
                    )
                    receipt = await asyncio.to_thread(response.getReceipt, self.client)
                except asyncio.TimeoutError:
                    logger.error("Transfer timeout after 30s - testnet may be slow")
                    raise Exception("Transfer timeout - testnet may be experiencing issues")
                
                tx_id = response.transactionId.toString()
                balance = await self.get_account_balance()
                
                logger.info(f"✅ HBAR transfer successful!")
                logger.info(f"Transaction ID: {tx_id}")
                logger.info(f"Hashscan: {self.HASHSCAN_TESTNET_URL}/transaction/{tx_id}")
                logger.info(f"New balance: {balance} HBAR")
                
                return {
                    "tx_id": tx_id,
                    "tx_type": "TRANSFER",
                    "status": str(receipt.status),
                    "amount": amount,
                    "from_account": self.account_id,
                    "from_balance": balance,
                    "to_account": self.escrow_account_id,
                    "hashscan_url": f"{self.HASHSCAN_TESTNET_URL}/transaction/{tx_id}",
                    "memo": memo,
                    "timestamp": timestamp
                }
            else:
                # Fallback without SDK
                balance = await self.get_account_balance()
                logger.warning("SDK not available, returning prepared status")
                return {
                    "tx_id": "PENDING",
                    "tx_type": "TRANSFER",
                    "status": "PREPARED",
                    "amount": amount,
                    "from_account": self.account_id,
                    "from_balance": balance,
                    "to_account": self.escrow_account_id,
                    "hashscan_url": f"{self.HASHSCAN_TESTNET_URL}/account/{self.account_id}",
                    "memo": memo,
                    "timestamp": timestamp,
                    "note": "SDK not available"
                }
                    
        except Exception as e:
            logger.error(f"Error transferring HBAR: {e}")
            raise
    
    async def get_account_balance(self) -> float:
        """Get the real HBAR balance from Hedera testnet"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                account_url = f"{self.MIRROR_NODE_URL}/accounts/{self.account_id}"
                response = await client.get(account_url)
                
                if response.status_code == 200:
                    account_data = response.json()
                    balance = int(account_data.get("balance", {}).get("balance", 0)) / 100_000_000
                    logger.info(f"Real balance for {self.account_id}: {balance} HBAR")
                    return balance
                else:
                    raise Exception(f"Failed to get balance for {self.account_id}")
                    
            except Exception as e:
                logger.error(f"Error getting balance: {e}")
                raise
    
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
