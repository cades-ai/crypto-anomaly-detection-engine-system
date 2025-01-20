"""
Crypto Anomaly Detection Engine System (CADES)
Transaction Analysis Module

This module implements advanced transaction pattern analysis for Solana memecoin trading,
focusing on detecting wash trading, cyclic transactions, and suspicious trading patterns.

Author: CADES Team
License: Proprietary
"""

import asyncio
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Set, Optional, Tuple
import numpy as np
from scipy.stats import zscore 
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class TransactionPattern:
    """Dataclass for storing identified transaction patterns"""
    pattern_type: str
    confidence_score: float
    involved_addresses: List[str]
    transaction_hashes: List[str]
    first_seen: datetime
    last_seen: datetime
    total_volume: float
    risk_score: float

class TransactionAnalyzer:
    """
    Advanced transaction pattern analyzer for Solana memecoin trading.
    Implements various detection algorithms for suspicious trading patterns.
    """

    def __init__(
        self,
        look_back_period: int = 3600,  # 1 hour default
        min_pattern_confidence: float = 0.75,
        max_patterns_per_token: int = 1000,
        wash_trade_threshold: float = 0.85
    ):
        """
        Initialize the transaction analyzer with configuration parameters.

        Args:
            look_back_period: Period in seconds to maintain transaction history
            min_pattern_confidence: Minimum confidence score for pattern reporting
            max_patterns_per_token: Maximum patterns to track per token
            wash_trade_threshold: Similarity threshold for wash trade detection
        """
        self.look_back_period = look_back_period
        self.min_pattern_confidence = min_pattern_confidence
        self.max_patterns_per_token = max_patterns_per_token
        self.wash_trade_threshold = wash_trade_threshold

        # Data structures for pattern analysis
        self.transaction_history: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=10000)  # Per-token transaction history
        )
        self.address_activity: Dict[str, Dict] = defaultdict(
            lambda: {
                'volume': 0.0,
                'last_seen': None,
                'transaction_count': 0,
                'counterparties': set()
            }
        )
        self.identified_patterns: Dict[str, List[TransactionPattern]] = defaultdict(list)
        
        # Statistical baselines
        self.volume_baselines: Dict[str, List[float]] = defaultdict(list)
        self.transaction_rate_baselines: Dict[str, List[float]] = defaultdict(list)

    async def process_transaction(self, transaction_data: Dict) -> Optional[List[TransactionPattern]]:
        """
        Process a new transaction and identify any suspicious patterns.

        Args:
            transaction_data: Decoded transaction data from blockchain listener

        Returns:
            List of identified patterns if any are found
        """
        try:
            # Extract key transaction details
            token_address = self._extract_token_address(transaction_data)
            if not token_address:
                return None

            # Update transaction history
            self.transaction_history[token_address].append({
                'timestamp': datetime.now(),
                'data': transaction_data
            })

            # Update address activity
            self._update_address_activity(transaction_data, token_address)

            # Run pattern detection algorithms
            patterns = await asyncio.gather(
                self._detect_wash_trading(token_address),
                self._detect_cyclic_transactions(token_address),
                self._detect_price_manipulation(token_address),
                self._detect_layered_transactions(token_address)
            )

            # Filter and score identified patterns
            significant_patterns = self._filter_significant_patterns(patterns)
            
            if significant_patterns:
                self.identified_patterns[token_address].extend(significant_patterns)
                # Maintain pattern limit per token
                self.identified_patterns[token_address] = \
                    self.identified_patterns[token_address][-self.max_patterns_per_token:]
                
            return significant_patterns

        except Exception as e:
            logger.error(f"Error processing transaction for analysis: {e}")
            return None

    async def _detect_wash_trading(self, token_address: str) -> Optional[TransactionPattern]:
        """
        Detect wash trading patterns using graph analysis and volume profiles.
        
        Args:
            token_address: Token contract address to analyze

        Returns:
            TransactionPattern if wash trading is detected
        """
        try:
            recent_transactions = self.transaction_history[token_address]
            if len(recent_transactions) < 5:  # Need minimum history
                return None

            # Build transaction graph
            graph = defaultdict(lambda: defaultdict(float))
            volumes = defaultdict(float)
            
            for tx in recent_transactions:
                sender = self._extract_sender(tx['data'])
                receiver = self._extract_receiver(tx['data'])
                volume = self._extract_volume(tx['data'])
                
                if all([sender, receiver, volume]):
                    graph[sender][receiver] += volume
                    volumes[sender] += volume
                    volumes[receiver] += volume

            # Analyze for circular patterns
            circular_trades = self._find_circular_patterns(graph)
            if not circular_trades:
                return None

            # Calculate wash trading confidence score
            volume_concentration = self._calculate_volume_concentration(volumes)
            temporal_density = self._calculate_temporal_density(recent_transactions)
            
            confidence_score = (volume_concentration + temporal_density) / 2
            
            if confidence_score >= self.wash_trade_threshold:
                return TransactionPattern(
                    pattern_type="wash_trading",
                    confidence_score=confidence_score,
                    involved_addresses=list(circular_trades),
                    transaction_hashes=[tx['data'].get('signature') for tx in recent_transactions],
                    first_seen=recent_transactions[0]['timestamp'],
                    last_seen=recent_transactions[-1]['timestamp'],
                    total_volume=sum(volumes.values()),
                    risk_score=self._calculate_risk_score(confidence_score, volumes)
                )

        except Exception as e:
            logger.error(f"Error in wash trading detection: {e}")
            
        return None

    async def _detect_cyclic_transactions(self, token_address: str) -> Optional[TransactionPattern]:
        """
        Detect cyclic transaction patterns indicating potential market manipulation.
        
        Args:
            token_address: Token contract address to analyze

        Returns:
            TransactionPattern if cyclic pattern is detected
        """
        try:
            recent_transactions = self.transaction_history[token_address]
            if len(recent_transactions) < 3:
                return None

            # Group transactions by time windows
            time_windows = self._group_by_time_windows(recent_transactions, window_size=300)  # 5 min windows
            
            patterns = []
            for window in time_windows:
                cycle = self._find_transaction_cycle(window)
                if cycle:
                    patterns.append(cycle)

            if not patterns:
                return None

            # Score the pattern
            pattern_strength = self._calculate_pattern_strength(patterns)
            if pattern_strength >= self.min_pattern_confidence:
                return TransactionPattern(
                    pattern_type="cyclic_trading",
                    confidence_score=pattern_strength,
                    involved_addresses=list(set(addr for pattern in patterns for addr in pattern)),
                    transaction_hashes=[tx['data'].get('signature') for tx in recent_transactions],
                    first_seen=recent_transactions[0]['timestamp'],
                    last_seen=recent_transactions[-1]['timestamp'],
                    total_volume=self._calculate_total_volume(patterns),
                    risk_score=self._calculate_risk_score(pattern_strength, None)
                )

        except Exception as e:
            logger.error(f"Error in cyclic transaction detection: {e}")
            
        return None

    async def _detect_price_manipulation(self, token_address: str) -> Optional[TransactionPattern]:
        """
        Detect potential price manipulation through transaction pattern analysis.
        
        Args:
            token_address: Token contract address to analyze

        Returns:
            TransactionPattern if price manipulation is detected
        """
        try:
            recent_transactions = self.transaction_history[token_address]
            if len(recent_transactions) < 10:
                return None

            # Extract price and volume data
            price_volume_data = self._extract_price_volume_data(recent_transactions)
            if not price_volume_data:
                return None

            # Detect price anomalies
            price_anomalies = self._detect_price_anomalies(price_volume_data)
            if not price_anomalies:
                return None

            # Calculate manipulation confidence
            confidence_score = self._calculate_manipulation_confidence(price_anomalies)
            
            if confidence_score >= self.min_pattern_confidence:
                return TransactionPattern(
                    pattern_type="price_manipulation",
                    confidence_score=confidence_score,
                    involved_addresses=self._get_involved_addresses(price_anomalies),
                    transaction_hashes=[tx['data'].get('signature') for tx in recent_transactions],
                    first_seen=recent_transactions[0]['timestamp'],
                    last_seen=recent_transactions[-1]['timestamp'],
                    total_volume=sum(pv['volume'] for pv in price_volume_data),
                    risk_score=self._calculate_risk_score(confidence_score, price_volume_data)
                )

        except Exception as e:
            logger.error(f"Error in price manipulation detection: {e}")
            
        return None

    def _calculate_risk_score(self, confidence_score: float, additional_data: Optional[Dict]) -> float:
        """Calculate final risk score based on pattern confidence and additional metrics."""
        base_score = confidence_score * 0.7  # Base weight for confidence

        if additional_data:
            # Add volume-based risk factor
            volume_factor = min(1.0, sum(additional_data.values()) / 1_000_000) * 0.15
            
            # Add time-based risk factor
            time_factor = 0.15
            
            return min(1.0, base_score + volume_factor + time_factor)
        
        return base_score

    def _filter_significant_patterns(self, patterns: List[Optional[TransactionPattern]]) -> List[TransactionPattern]:
        """Filter out insignificant or low-confidence patterns."""
        return [
            pattern for pattern in patterns
            if pattern and pattern.confidence_score >= self.min_pattern_confidence
        ]

    def get_token_analysis(self, token_address: str) -> Dict:
        """
        Get comprehensive analysis for a specific token.

        Args:
            token_address: Token contract address

        Returns:
            Dict containing token analysis data
        """
        return {
            'identified_patterns': [
                pattern.__dict__ for pattern in self.identified_patterns[token_address]
            ],
            'address_activity': self.address_activity,
            'transaction_count': len(self.transaction_history[token_address]),
            'risk_assessment': self._calculate_token_risk(token_address)
        }

    def _calculate_token_risk(self, token_address: str) -> Dict:
        """Calculate overall risk metrics for a token."""
        patterns = self.identified_patterns[token_address]
        if not patterns:
            return {'risk_level': 'low', 'confidence': 0.0}

        risk_scores = [pattern.risk_score for pattern in patterns]
        return {
            'risk_level': self._categorize_risk(np.mean(risk_scores)),
            'confidence': np.mean([pattern.confidence_score for pattern in patterns]),
            'pattern_frequency': len(patterns) / self.look_back_period
        }

    @staticmethod
    def _categorize_risk(risk_score: float) -> str:
        """Categorize risk level based on risk score."""
        if risk_score >= 0.8:
            return 'critical'
        elif risk_score >= 0.6:
            return 'high'
        elif risk_score >= 0.4:
            return 'medium'
        return 'low'

if __name__ == "__main__":
    # Example usage
    async def main():
        analyzer = TransactionAnalyzer()
        
        # Example transaction data
        sample_transaction = {
            'signature': 'example_signature',
            'slot': 123456789,
            'instructions': [
                {
                    'program_id': 'TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA',
                    'accounts': ['account1', 'account2'],
                    'data': 'base58_encoded_data'
                }
            ]
        }
        
        patterns = await analyzer.process_transaction(sample_transaction)
        if patterns:
            print("Detected patterns:", patterns)
        
    asyncio.run(main())