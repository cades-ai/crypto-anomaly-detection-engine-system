"""
Crypto Anomaly Detection Engine (CADE)
Solana Blockchain Listener Module

This module implements real-time monitoring of Solana blockchain activities,
focusing on memecoin-related transactions, liquidity pools, and wallet behaviors.
It serves as the primary data ingestion point for the CADE system.

Author: CADE Team
License: Proprietary
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Set, Callable
from datetime import datetime, timezone
import base58
import base64

from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Confirmed
from solana.rpc.types import MemcmpOpts
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.message import Message

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SolanaBlockchainListener:
    """
    Real-time Solana blockchain activity monitor specialized for memecoin analysis.
    Implements advanced filtering and preprocessing of on-chain data.
    """
    
    def __init__(
        self,
        rpc_urls: List[str],
        watched_programs: Optional[List[str]] = None,
        backup_rpcs: Optional[List[str]] = None
    ):
        """
        Initialize the blockchain listener with multiple RPC endpoints for redundancy.
        
        Args:
            rpc_urls: List of primary Solana RPC endpoints
            watched_programs: List of program IDs to monitor (e.g., Raydium, Orca)
            backup_rpcs: Backup RPC endpoints for failover
        """
        self.rpc_urls = rpc_urls
        self.backup_rpcs = backup_rpcs or []
        self.current_rpc_index = 0
        self.client: Optional[AsyncClient] = None
        
        # Default program IDs if none provided
        self.watched_programs = set(watched_programs or [
            "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8",  # Raydium
            "9W959DqEETiGZocYWCQPaJ6sBmUzgfxXfqGeTEdp3aQP",  # Orca v2
            "JUP4Fb2cqiRUcaTHdrPC8h2gNsA2ETXiPDD33WcGuJB",   # Jupiter
        ])
        
        # Initialize data structures for tracking
        self.watched_accounts: Set[str] = set()
        self.transaction_callbacks: List[Callable] = []
        self.price_updates: Dict[str, float] = {}
        self.liquidity_changes: Dict[str, List[Dict]] = {}
        
        # Performance metrics
        self.metrics = {
            'transactions_processed': 0,
            'errors_encountered': 0,
            'start_time': datetime.now(timezone.utc)
        }

    async def initialize(self) -> None:
        """Initialize RPC connection and subscription streams."""
        try:
            self.client = AsyncClient(self.rpc_urls[self.current_rpc_index])
            await self._verify_connection()
            logger.info(f"Successfully connected to RPC: {self.rpc_urls[self.current_rpc_index]}")
        except Exception as e:
            logger.error(f"Failed to initialize primary RPC connection: {e}")
            await self._failover_to_backup()

    async def _verify_connection(self) -> bool:
        """Verify RPC connection is responsive and synchronized."""
        try:
            response = await self.client.get_health()
            slot_info = await self.client.get_slot()
            
            if response != "ok" or not slot_info:
                raise ConnectionError("RPC health check failed")
                
            logger.info(f"Connected to Solana network at slot: {slot_info}")
            return True
        except Exception as e:
            logger.error(f"Connection verification failed: {e}")
            return False

    async def _failover_to_backup(self) -> None:
        """Implement failover logic to backup RPC endpoints."""
        all_rpcs = self.rpc_urls + self.backup_rpcs
        
        for idx, rpc_url in enumerate(all_rpcs):
            if idx == self.current_rpc_index:
                continue
                
            try:
                self.client = AsyncClient(rpc_url)
                if await self._verify_connection():
                    self.current_rpc_index = idx
                    logger.info(f"Successfully failed over to RPC: {rpc_url}")
                    return
            except Exception as e:
                logger.error(f"Failover attempt to {rpc_url} failed: {e}")
        
        raise ConnectionError("All RPC endpoints are unavailable")

    async def subscribe_to_program(self, program_id: str) -> None:
        """
        Subscribe to all transactions involving a specific program.
        
        Args:
            program_id: Solana program ID to monitor
        """
        try:
            pubkey = Pubkey.from_string(program_id)
            
            # Set up memcmp filter for program ID
            filter_opts = MemcmpOpts(
                offset=0,  # Program ID location in transaction
                bytes=str(pubkey)
            )
            
            # Subscribe to program transaction notifications
            await self.client.transaction_subscribe(
                commitment=Confirmed,
                encoding="base64",
                filters=[{"memcmp": filter_opts}]
            )
            
            self.watched_programs.add(program_id)
            logger.info(f"Successfully subscribed to program: {program_id}")
            
        except Exception as e:
            logger.error(f"Failed to subscribe to program {program_id}: {e}")
            raise

    async def process_transaction(self, transaction_data: Dict) -> None:
        """
        Process incoming transaction data for anomaly detection.
        
        Args:
            transaction_data: Raw transaction data from Solana RPC
        """
        try:
            # Decode transaction data
            tx_bytes = base64.b64decode(transaction_data['transaction'])
            transaction = Transaction.from_bytes(tx_bytes)
            
            # Extract relevant transaction details
            tx_info = {
                'signature': transaction_data.get('signature'),
                'slot': transaction_data.get('slot'),
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'program_ids': [str(pid) for pid in transaction.message.account_keys],
                'instructions': []
            }
            
            # Process transaction instructions
            for idx, instruction in enumerate(transaction.message.instructions):
                instruction_data = {
                    'program_id': str(transaction.message.account_keys[instruction.program_id_index]),
                    'accounts': [str(transaction.message.account_keys[i]) for i in instruction.accounts],
                    'data': base58.b58encode(instruction.data).decode('ascii')
                }
                tx_info['instructions'].append(instruction_data)
            
            # Update metrics
            self.metrics['transactions_processed'] += 1
            
            # Notify callbacks
            for callback in self.transaction_callbacks:
                await callback(tx_info)
                
        except Exception as e:
            self.metrics['errors_encountered'] += 1
            logger.error(f"Error processing transaction: {e}")

    async def start_monitoring(self) -> None:
        """Start the main monitoring loop."""
        try:
            await self.initialize()
            
            # Subscribe to all watched programs
            for program_id in self.watched_programs:
                await self.subscribe_to_program(program_id)
            
            logger.info("Started blockchain monitoring")
            
            while True:
                try:
                    # Process incoming transactions
                    response = await self.client.receive_data()
                    if response and 'result' in response:
                        await self.process_transaction(response['result'])
                except Exception as e:
                    logger.error(f"Error in monitoring loop: {e}")
                    await self._failover_to_backup()
                
                await asyncio.sleep(0.1)  # Prevent CPU overload
                
        except Exception as e:
            logger.error(f"Fatal error in blockchain monitoring: {e}")
            raise

    def add_transaction_callback(self, callback: Callable) -> None:
        """
        Add a callback function to be called for each transaction.
        
        Args:
            callback: Async function to be called with transaction data
        """
        self.transaction_callbacks.append(callback)

    def get_metrics(self) -> Dict:
        """Return current performance metrics."""
        current_time = datetime.now(timezone.utc)
        uptime = (current_time - self.metrics['start_time']).total_seconds()
        
        return {
            **self.metrics,
            'uptime_seconds': uptime,
            'transactions_per_second': self.metrics['transactions_processed'] / uptime if uptime > 0 else 0,
            'error_rate': self.metrics['errors_encountered'] / self.metrics['transactions_processed'] if self.metrics['transactions_processed'] > 0 else 0
        }

if __name__ == "__main__":
    # Example usage
    async def main():
        listener = SolanaBlockchainListener(
            rpc_urls=["https://api.mainnet-beta.solana.com"],
            backup_rpcs=["https://solana-api.projectserum.com"]
        )
        
        # Example callback
        async def print_transaction(tx_data: Dict):
            print(f"New transaction: {json.dumps(tx_data, indent=2)}")
        
        listener.add_transaction_callback(print_transaction)
        await listener.start_monitoring()
    
    asyncio.run(main())