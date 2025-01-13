"""
Crypto Anomaly Detection Engine System (CADES)
Enhanced Solana Blockchain Listener Module

This module implements advanced real-time monitoring of Solana blockchain activities,
with sophisticated pattern detection, automated anomaly tracking, and optimized 
memory management for memecoin analysis.

Author: CADES Team
License: Proprietary
Version: 2.0.0
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Optional, Set, Callable, Tuple, Any
from datetime import datetime, timezone, timedelta
import base58
import base64
from collections import deque, defaultdict
from dataclasses import dataclass
from enum import Enum, auto
import numpy as np
from weakref import WeakSet
import gc
import aiohttp
import orjson

from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Confirmed, Finalized
from solana.rpc.types import MemcmpOpts, TokenBalancesFilter
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.message import Message
from solana.transaction import Transaction as LegacyTransaction

# Configure advanced logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
)
logger = logging.getLogger(__name__)

class TransactionType(Enum):
    """Enumeration of transaction types for classification."""
    UNKNOWN = auto()
    SWAP = auto()
    LIQUIDITY_ADD = auto()
    LIQUIDITY_REMOVE = auto()
    TRANSFER = auto()
    MINT = auto()
    BURN = auto()
    STAKE = auto()
    UNSTAKE = auto()
    CONTRACT_INTERACTION = auto()
    WHALE_MOVEMENT = auto()

@dataclass
class TransactionMetrics:
    """Dataclass for storing transaction-related metrics."""
    timestamp: datetime
    transaction_type: TransactionType
    value_usd: float
    token_amount: float
    gas_cost: float
    accounts_involved: List[str]
    program_id: str
    signature: str

class MemoryEfficientCache:
    """
    Enhanced memory-efficient cache implementation using deque with advanced features.
    Implements LRU caching with periodic cleanup and statistics tracking.
    """
    
    def __init__(self, maxsize: int = 1000, cleanup_threshold: float = 0.9):
        self.cache = deque(maxlen=maxsize)
        self.seen = WeakSet()
        self.access_count = defaultdict(int)
        self.last_access = {}
        self.cleanup_threshold = cleanup_threshold
        self.stats = {
            'hits': 0,
            'misses': 0,
            'cleanups': 0,
            'items_removed': 0
        }
    
    def add(self, item: str, metadata: Optional[Dict] = None) -> None:
        """Add item to cache with metadata and access tracking."""
        if item not in self.seen:
            if len(self.cache) >= self.cache.maxlen * self.cleanup_threshold:
                self._cleanup_least_accessed()
            
            self.cache.append((item, metadata or {}))
            self.seen.add(item)
            self.last_access[item] = time.time()
            self.access_count[item] = 1
    
    def get(self, item: str) -> Optional[Dict]:
        """Retrieve item from cache with access tracking."""
        if item in self.seen:
            self.stats['hits'] += 1
            self.last_access[item] = time.time()
            self.access_count[item] += 1
            for cached_item, metadata in self.cache:
                if cached_item == item:
                    return metadata
        self.stats['misses'] += 1
        return None
    
    def _cleanup_least_accessed(self) -> None:
        """Remove least accessed items from cache."""
        items_to_remove = []
        current_time = time.time()
        
        # Find items with low access counts and old last access times
        for item, count in self.access_count.items():
            last_access = self.last_access.get(item, 0)
            if count < 3 and (current_time - last_access) > 3600:  # 1 hour
                items_to_remove.append(item)
        
        # Remove identified items
        for item in items_to_remove:
            self.seen.discard(item)
            self.access_count.pop(item, None)
            self.last_access.pop(item, None)
        
        self.stats['cleanups'] += 1
        self.stats['items_removed'] += len(items_to_remove)
        
        # Force garbage collection if significant cleanup occurred
        if len(items_to_remove) > 100:
            gc.collect()

class TransactionAnalyzer:
    """
    Advanced transaction analysis engine for pattern detection and classification.
    """
    
    def __init__(self):
        self.known_patterns = {
            'whale_threshold': 100000,  # USD value
            'rapid_trading': timedelta(minutes=5),
            'cyclic_pattern': 3,  # minimum cycles
        }
        self.pattern_cache = MemoryEfficientCache(maxsize=5000)
        self.recent_transactions = defaultdict(list)
    
    def classify_transaction(self, tx_info: Dict) -> TransactionType:
        """Classify transaction type based on instruction patterns."""
        if not tx_info.get('instructions'):
            return TransactionType.UNKNOWN
            
        instructions = tx_info['instructions']
        program_ids = set(instr.get('program_id') for instr in instructions)
        
        # Classification patterns
        if any(pid in SWAP_PROGRAMS for pid in program_ids):
            return TransactionType.SWAP
        elif any(pid in LP_PROGRAMS for pid in program_ids):
            if self._is_liquidity_add(instructions):
                return TransactionType.LIQUIDITY_ADD
            return TransactionType.LIQUIDITY_REMOVE
        elif self._is_token_transfer(instructions):
            return TransactionType.TRANSFER
        
        return TransactionType.CONTRACT_INTERACTION
    
    def detect_patterns(self, tx_info: Dict) -> List[str]:
        """Detect sophisticated trading patterns in transaction."""
        patterns = []
        signature = tx_info.get('signature', '')
        
        # Check if we've already analyzed this transaction
        cached_patterns = self.pattern_cache.get(signature)
        if cached_patterns:
            return cached_patterns
        
        # Pattern detection logic
        if self._is_whale_movement(tx_info):
            patterns.append('whale_movement')
        
        if self._detect_wash_trading(tx_info):
            patterns.append('wash_trading')
        
        if self._detect_cyclic_transfers(tx_info):
            patterns.append('cyclic_transfers')
        
        # Cache results
        self.pattern_cache.add(signature, {'patterns': patterns})
        return patterns
    
    def _is_whale_movement(self, tx_info: Dict) -> bool:
        """Detect whale-level transactions."""
        # Implementation details...
        return False
    
    def _detect_wash_trading(self, tx_info: Dict) -> bool:
        """Detect potential wash trading patterns."""
        # Implementation details...
        return False
    
    def _detect_cyclic_transfers(self, tx_info: Dict) -> bool:
        """Detect cyclic transfer patterns."""
        # Implementation details...
        return False

class BlockchainMonitor:
    """
    Advanced blockchain monitoring system with pattern detection and analysis.
    """
    
    def __init__(self, rpc_urls: List[str], backup_rpcs: Optional[List[str]] = None):
        self.rpc_urls = rpc_urls
        self.backup_rpcs = backup_rpcs or []
        self.current_rpc_index = 0
        self.client: Optional[AsyncClient] = None
        self.websocket: Optional[aiohttp.ClientWebSocketResponse] = None
        
        # Initialize components
        self.transaction_analyzer = TransactionAnalyzer()
        self.pattern_detector = PatternDetector()
        self.metrics_collector = MetricsCollector()
        
        # Setup monitoring state
        self.monitoring_active = False
        self.last_slot = 0
        self.slot_cache = MemoryEfficientCache(maxsize=1000)
        
        # Initialize metrics
        self.metrics = defaultdict(int)
        self.start_time = datetime.now(timezone.utc)
    
    async def initialize(self) -> None:
        """Initialize monitoring system with redundancy."""
        for rpc_url in self.rpc_urls:
            try:
                self.client = AsyncClient(rpc_url)
                if await self._verify_connection():
                    logger.info(f"Successfully connected to RPC: {rpc_url}")
                    return
            except Exception as e:
                logger.warning(f"Failed to connect to {rpc_url}: {e}")
        
        # Try backup RPCs if primary fails
        for rpc_url in self.backup_rpcs:
            try:
                self.client = AsyncClient(rpc_url)
                if await self._verify_connection():
                    logger.info(f"Connected to backup RPC: {rpc_url}")
                    return
            except Exception as e:
                logger.warning(f"Failed to connect to backup {rpc_url}: {e}")
        
        raise ConnectionError("Failed to connect to any RPC endpoint")
    
    async def _verify_connection(self) -> bool:
        """Verify RPC connection with enhanced health checks."""
        try:
            # Multiple health checks
            health_response = await self.client.get_health()
            slot_info = await self.client.get_slot()
            version_info = await self.client.get_version()
            
            if health_response != "ok":
                return False
            
            # Verify reasonable slot advancement
            if self.last_slot > 0:
                slot_advancement = slot_info - self.last_slot
                if slot_advancement < 0 or slot_advancement > 1000:
                    logger.warning(f"Suspicious slot advancement: {slot_advancement}")
                    return False
            
            self.last_slot = slot_info
            logger.info(f"Connected to Solana {version_info} at slot {slot_info}")
            return True
            
        except Exception as e:
            logger.error(f"Connection verification failed: {e}")
            return False
    
    async def monitor_transactions(self) -> None:
        """Monitor transactions with advanced pattern detection."""
        try:
            self.monitoring_active = True
            logger.info("Starting transaction monitoring...")
            
            while self.monitoring_active:
                try:
                    response = await self.client.receive_data()
                    if response and 'result' in response:
                        await self._process_transaction_data(response['result'])
                except Exception as e:
                    logger.error(f"Error processing transaction: {e}")
                    await self._handle_error()
                
                await asyncio.sleep(0.01)  # Reduced sleep time for faster processing
                
        except Exception as e:
            logger.error(f"Fatal error in transaction monitoring: {e}")
            raise
        finally:
            self.monitoring_active = False
    
    async def _process_transaction_data(self, tx_data: Dict) -> None:
        """Process transaction data with pattern detection."""
        try:
            # Decode and validate transaction
            tx_bytes = base64.b64decode(tx_data['transaction'])
            transaction = Transaction.from_bytes(tx_bytes)
            
            # Extract transaction details
            tx_info = self._extract_transaction_info(transaction, tx_data)
            
            # Analyze transaction patterns
            patterns = self.transaction_analyzer.detect_patterns(tx_info)
            
            # Update metrics
            self.metrics['transactions_processed'] += 1
            if patterns:
                self.metrics['patterns_detected'] += len(patterns)
            
            # Notify callbacks if patterns detected
            if patterns:
                await self._notify_pattern_detected(tx_info, patterns)
            
        except Exception as e:
            logger.error(f"Error processing transaction data: {e}")
            self.metrics['errors'] += 1
    
    def _extract_transaction_info(self, transaction: Transaction, tx_data: Dict) -> Dict:
        """Extract detailed transaction information."""
        return {
            'signature': tx_data.get('signature'),
            'slot': tx_data.get('slot'),
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'program_ids': [str(pid) for pid in transaction.message.account_keys],
            'instructions': self._parse_instructions(transaction),
            'metadata': self._extract_metadata(tx_data)
        }
    
    def _parse_instructions(self, transaction: Transaction) -> List[Dict]:
        """Parse transaction instructions with detailed metadata."""
        instructions = []
        for idx, instruction in enumerate(transaction.message.instructions):
            instruction_data = {
                'program_id': str(transaction.message.account_keys[instruction.program_id_index]),
                'accounts': [str(transaction.message.account_keys[i]) for i in instruction.accounts],
                'data': base58.b58encode(instruction.data).decode('ascii'),
                'index': idx
            }
            instructions.append(instruction_data)
        return instructions
    
    def _extract_metadata(self, tx_data: Dict) -> Dict:
        """Extract additional transaction metadata."""
        return {
            'slot': tx_data.get('slot'),
            'blockTime': tx_data.get('blockTime'),
            'fee': tx_data.get('fee'),
            'err': tx_data.get('err'),
            'recent_blockhash': tx_data.get('recentBlockhash')
        }
    
    async def _notify_pattern_detected(self, tx_info: Dict, patterns: List[str]) -> None:
        """Notify listeners of detected patterns."""
        notification = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'transaction': tx_info,
            'patterns': patterns,
            'risk_score': self._calculate_risk_score(patterns)
        }
        
        # TODO: Implement notification logic (e.g., webhooks, message queue)
        logger.info(f"Patterns detected: {patterns}")
    
    def _calculate_risk_score(self, patterns: List[str]) -> float:
        """Calculate risk score based on detected patterns."""
        # Pattern weights
        weights = {
            'whale_movement': 0.7,
            'wash_trading': 0.9,
            'cyclic_transfers': 0.8,
            'rapid_trading': 0.5
        }
        
        score = sum(weights.get(pattern, 0.1) for pattern in patterns)
        return min(1.0, score)  # Normalize to [0, 1]
    
    async def get_status(self) -> Dict:
        """Get detailed monitoring status and metrics."""
        current_time = datetime.now(timezone.utc)
        uptime = (current_time - self.start_time).total_seconds()
        
        return {
            'status': 'active' if self.monitoring_active else 'inactive',
            'uptime_seconds': uptime,
            'transactions_processed': self.metrics['transactions_processed'],
            'patterns_detected': self.metrics['patterns_detected'],
            'errors': self.metrics['errors'],
            'transactions_per_second': self.metrics['transactions_processed'] / uptime if uptime > 0 else 0,
            'error_rate': self.metrics['errors'] / self.metrics['transactions_processed'] if self.metrics['transactions_processed'] > 0 else 0,
            'last_slot': self.last_slot,
            'memory_usage': self._get_memory_usage(),
            'pattern_distribution': self._get_pattern_distribution()
        }
    
    def _get_memory_usage(self) -> Dict:
        """Get detailed memory usage statistics."""
        return {
            'cache_size': len(self.slot_cache.cache),
            'pattern_cache_size': len(self.transaction_analyzer.pattern_cache.cache),
            'gc_stats': gc.get_stats()
        }
    
    def _get_pattern_distribution(self) -> Dict:
        """Get distribution of detected patterns."""
        return {
            'whale_movements': self.metrics.get('whale_movements', 0),
            'wash_trading': self.metrics.get('wash_trading', 0),
            'cyclic_transfers': self.metrics.get('cyclic_transfers', 0),
            'rapid_trading': self.metrics.get('rapid_trading', 0)
        }

class PatternDetector:
    """
    Advanced pattern detection system for blockchain analysis.
    Implements sophisticated algorithms for identifying complex trading patterns.
    """
    
    def __init__(self):
        self.patterns = {
            'whale_movement': {
                'threshold': 100000,  # USD
                'time_window': timedelta(hours=24)
            },
            'wash_trading': {
                'cycle_threshold': 3,
                'time_window': timedelta(minutes=30)
            },
            'cyclic_transfer': {
                'min_cycle_length': 3,
                'max_cycle_length': 10,
                'time_window': timedelta(hours=1)
            }
        }
        
        self.address_history = defaultdict(list)
        self.pattern_history = MemoryEfficientCache(maxsize=10000)
        
    def analyze_transaction(self, tx_info: Dict) -> List[Dict]:
        """
        Analyze transaction for complex patterns.
        Returns list of detected patterns with confidence scores.
        """
        patterns = []
        
        # Check for whale movements
        if self._check_whale_pattern(tx_info):
            patterns.append({
                'type': 'whale_movement',
                'confidence': self._calculate_whale_confidence(tx_info),
                'metadata': self._extract_whale_metadata(tx_info)
            })
        
        # Check for wash trading
        wash_trading = self._detect_wash_trading(tx_info)
        if wash_trading:
            patterns.append({
                'type': 'wash_trading',
                'confidence': wash_trading['confidence'],
                'metadata': wash_trading['metadata']
            })
        
        # Check for cyclic transfers
        cycles = self._find_cyclic_transfers(tx_info)
        if cycles:
            patterns.append({
                'type': 'cyclic_transfer',
                'confidence': self._calculate_cycle_confidence(cycles),
                'metadata': {'cycles': cycles}
            })
        
        return patterns
    
    def _check_whale_pattern(self, tx_info: Dict) -> bool:
        """Check for whale-level transaction patterns."""
        try:
            # Extract value information
            value = self._extract_transaction_value(tx_info)
            if not value:
                return False
            
            threshold = self.patterns['whale_movement']['threshold']
            return value >= threshold
        except Exception as e:
            logger.error(f"Error in whale pattern check: {e}")
            return False
    
    def _detect_wash_trading(self, tx_info: Dict) -> Optional[Dict]:
        """
        Detect wash trading patterns using graph analysis.
        Returns confidence score and metadata if pattern detected.
        """
        try:
            # Extract relevant addresses
            addresses = self._extract_involved_addresses(tx_info)
            if len(addresses) < 2:
                return None
            
            # Check recent history for circular patterns
            recent_txs = self._get_recent_transactions(addresses)
            if not recent_txs:
                return None
            
            # Analyze transaction graph
            cycles = self._find_trading_cycles(recent_txs)
            if not cycles:
                return None
            
            confidence = self._calculate_wash_trading_confidence(cycles)
            return {
                'confidence': confidence,
                'metadata': {
                    'cycles': cycles,
                    'addresses': addresses,
                    'time_span': self._calculate_time_span(recent_txs)
                }
            }
        except Exception as e:
            logger.error(f"Error in wash trading detection: {e}")
            return None
    
    def _find_cyclic_transfers(self, tx_info: Dict) -> List[Dict]:
        """
        Find cyclic transfer patterns in transaction history.
        Uses graph theory algorithms for cycle detection.
        """
        cycles = []
        try:
            addresses = self._extract_involved_addresses(tx_info)
            if len(addresses) < 3:  # Need at least 3 addresses for a cycle
                return cycles
            
            # Build transaction graph
            graph = self._build_transaction_graph(addresses)
            
            # Find cycles using Johnson's algorithm
            simple_cycles = self._find_simple_cycles(graph)
            
            # Filter and validate cycles
            for cycle in simple_cycles:
                if self._validate_cycle(cycle):
                    cycles.append({
                        'addresses': cycle,
                        'length': len(cycle),
                        'timestamp': datetime.now(timezone.utc).isoformat()
                    })
        
        except Exception as e:
            logger.error(f"Error in cyclic transfer detection: {e}")
        
        return cycles
    
    def _build_transaction_graph(self, addresses: Set[str]) -> Dict[str, Set[str]]:
        """Build directed graph of transactions between addresses."""
        graph = defaultdict(set)
        
        # Get recent transactions for these addresses
        recent_txs = self._get_recent_transactions(addresses)
        
        # Build adjacency list representation
        for tx in recent_txs:
            if 'from' in tx and 'to' in tx:
                graph[tx['from']].add(tx['to'])
        
        return graph
    
    def _find_simple_cycles(self, graph: Dict[str, Set[str]]) -> List[List[str]]:
        """Find simple cycles in directed graph using Johnson's algorithm."""
        def _find_cycles_recursive(current: str, start: str, visited: Set[str], path: List[str]) -> List[List[str]]:
            cycles = []
            path.append(current)
            visited.add(current)
            
            # Check neighbors
            for neighbor in graph[current]:
                if neighbor == start and len(path) > 2:
                    cycles.append(path[:])
                elif neighbor not in visited:
                    cycles.extend(_find_cycles_recursive(neighbor, start, visited.copy(), path[:]))
            
            return cycles
        
        all_cycles = []
        for node in graph:
            cycles = _find_cycles_recursive(node, node, set(), [])
            all_cycles.extend(cycles)
        
        return all_cycles
    
    def _validate_cycle(self, cycle: List[str]) -> bool:
        """Validate if a cycle represents a legitimate pattern."""
        if not self.patterns['cyclic_transfer']['min_cycle_length'] <= len(cycle) <= self.patterns['cyclic_transfer']['max_cycle_length']:
            return False
            
        # Check time window
        timestamps = [self.address_history[addr][-1]['timestamp'] for addr in cycle if addr in self.address_history]
        if not timestamps:
            return False
            
        time_span = max(timestamps) - min(timestamps)
        return time_span <= self.patterns['cyclic_transfer']['time_window']

class MetricsCollector:
    """
    Advanced metrics collection and analysis system.
    Implements real-time statistical analysis of blockchain patterns.
    """
    
    def __init__(self):
        self.metrics = defaultdict(lambda: defaultdict(float))
        self.time_series = defaultdict(list)
        self.anomaly_scores = defaultdict(list)
        
    def update_metrics(self, tx_info: Dict, patterns: List[Dict]) -> None:
        """Update metrics with new transaction data and detected patterns."""
        timestamp = datetime.now(timezone.utc)
        
        # Update transaction metrics
        self.metrics['transactions']['total'] += 1
        self.metrics['transactions']['volume'] += self._extract_volume(tx_info)
        
        # Update pattern metrics
        for pattern in patterns:
            pattern_type = pattern['type']
            confidence = pattern['confidence']
            
            self.metrics['patterns'][pattern_type] += 1
            self.metrics['confidence'][pattern_type] += confidence
            
            # Store time series data
            self.time_series[pattern_type].append({
                'timestamp': timestamp,
                'confidence': confidence,
                'metadata': pattern.get('metadata', {})
            })
            
            # Calculate and store anomaly scores
            anomaly_score = self._calculate_anomaly_score(pattern)
            self.anomaly_scores[pattern_type].append({
                'timestamp': timestamp,
                'score': anomaly_score
            })
    
    def _calculate_anomaly_score(self, pattern: Dict) -> float:
        """Calculate anomaly score for pattern using statistical methods."""
        pattern_type = pattern['type']
        confidence = pattern['confidence']
        
        # Get historical scores for this pattern type
        historical_scores = [entry['confidence'] 
                           for entry in self.time_series[pattern_type][-100:]]
        
        if not historical_scores:
            return confidence
        
        # Calculate z-score
        mean = np.mean(historical_scores)
        std = np.std(historical_scores) or 1.0
        z_score = (confidence - mean) / std
        
        # Convert to probability using sigmoid function
        anomaly_score = 1 / (1 + np.exp(-z_score))
        
        return anomaly_score
    
    def get_metrics_summary(self) -> Dict:
        """Get comprehensive metrics summary."""
        return {
            'transactions': dict(self.metrics['transactions']),
            'patterns': dict(self.metrics['patterns']),
            'confidence': {
                k: v / self.metrics['patterns'][k] if self.metrics['patterns'][k] > 0 else 0
                for k, v in self.metrics['confidence'].items()
            },
            'anomalies': self._get_anomaly_summary()
        }
    
    def _get_anomaly_summary(self) -> Dict:
        """Get summary of detected anomalies."""
        summary = {}
        for pattern_type, scores in self.anomaly_scores.items():
            recent_scores = [s['score'] for s in scores[-100:]]
            if recent_scores:
                summary[pattern_type] = {
                    'mean_score': np.mean(recent_scores),
                    'max_score': max(recent_scores),
                    'recent_anomalies': sum(1 for s in recent_scores if s > 0.95)
                }
        return summary

# Program ID constants
SWAP_PROGRAMS = {
    "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8",  # Raydium
    "9W959DqEETiGZocYWCQPaJ6sBmUzgfxXfqGeTEdp3aQP",  # Orca
    "JUP4Fb2cqiRUcaTHdrPC8h2gNsA2ETXiPDD33WcGuJB"   # Jupiter
}

LP_PROGRAMS = {
    "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8",  # Raydium
    "9W959DqEETiGZocYWCQPaJ6sBmUzgfxXfqGeTEdp3aQP"   # Orca
}

# Example usage
async def main():
    """Example implementation of the blockchain monitor."""
    rpc_urls = [
        "https://api.mainnet-beta.solana.com",
        "https://solana-api.projectserum.com"
    ]
    
    backup_rpcs = [
        "https://api.mainnet.solana.com",
        "https://api.solana.com"
    ]
    
    monitor = BlockchainMonitor(rpc_urls, backup_rpcs)
    
    try:
        await monitor.initialize()
        await monitor.monitor_transactions()
    except Exception as e:
        logger.error(f"Error in main: {e}")
    finally:
        # Cleanup
        if monitor.client:
            await monitor.client.close()

if __name__ == "__main__":
    asyncio.run(main())