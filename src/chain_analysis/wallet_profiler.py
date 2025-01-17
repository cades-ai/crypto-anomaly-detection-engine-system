"""
Crypto Anomaly Detection Engine System (CADES)
Wallet Profiler Module

This module implements wallet behavior profiling and analysis,
focusing on identifying trading patterns, risk assessment,
and relationship mapping between wallets.

Author: CADES Team
License: Proprietary
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple
import numpy as np
import logging
from collections import defaultdict, deque

from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class WalletProfile:
    """Detailed wallet profile information"""
    address: str
    total_volume_usd: float
    transaction_count: int
    unique_tokens: Set[str]
    average_position_size: float
    average_holding_time: float
    profit_loss: float
    risk_score: float
    activity_score: float
    first_seen: datetime
    last_active: datetime
    known_associates: Set[str]
    behavior_tags: Set[str]
    
@dataclass
class WalletActivity:
    """Recent wallet activity metrics"""
    timestamp: datetime
    token_address: Optional[str]
    transaction_type: str
    amount_usd: float
    counterparty: Optional[str]
    profit_loss: Optional[float]
    risk_indicators: Dict[str, float]

class WalletProfiler:
    """
    Advanced wallet behavior analysis system.
    Tracks and analyzes trading patterns, relationships, and risk factors.
    """
    
    def __init__(
        self,
        rpc_client: AsyncClient,
        min_volume_usd: float = 1000,  # Minimum volume for analysis
        analysis_window: int = 30 * 24 * 3600,  # 30 days
        update_interval: int = 300,  # 5 minutes
        min_confidence: float = 0.7
    ):
        """
        Initialize the wallet profiler.
        
        Args:
            rpc_client: Solana RPC client
            min_volume_usd: Minimum USD volume for analysis
            analysis_window: Time window for analysis in seconds
            update_interval: Update interval in seconds
            min_confidence: Minimum confidence for pattern detection
        """
        self.rpc_client = rpc_client
        self.min_volume_usd = min_volume_usd
        self.analysis_window = analysis_window
        self.update_interval = update_interval
        self.min_confidence = min_confidence
        
        # Data structures
        self.wallet_profiles: Dict[str, WalletProfile] = {}
        self.activity_history: Dict[str, List[WalletActivity]] = defaultdict(list)
        self.relationship_graph: Dict[str, Dict[str, float]] = defaultdict(dict)
        
        # Pattern detection thresholds
        self.thresholds = {
            'high_frequency_trading': {
                'min_daily_trades': 20,
                'max_holding_time': 3600  # 1 hour
            },
            'whale_activity': {
                'min_position_size': 100000,  # $100k USD
                'min_total_volume': 1000000   # $1M USD
            },
            'wash_trading': {
                'cycle_length': 3,
                'time_window': 3600,  # 1 hour
                'min_volume': 10000   # $10k USD
            }
        }

    async def profile_wallet(self, wallet_address: str) -> Optional[Dict]:
        """
        Generate comprehensive wallet profile and analysis.
        
        Args:
            wallet_address: Wallet address to analyze
            
        Returns:
            Analysis results if sufficient data available
        """
        try:
            # Get wallet transaction history
            transactions = await self._fetch_wallet_transactions(wallet_address)
            if not await self._meets_analysis_criteria(transactions):
                return None
                
            # Calculate base metrics
            base_metrics = await self._calculate_base_metrics(transactions)
            
            # Analyze trading patterns
            patterns = await self._analyze_trading_patterns(transactions)
            
            # Calculate risk metrics
            risk_metrics = self._calculate_risk_metrics(base_metrics, patterns)
            
            # Create wallet profile
            profile = self._create_wallet_profile(
                wallet_address,
                base_metrics,
                patterns,
                risk_metrics
            )
            
            # Store profile
            self.wallet_profiles[wallet_address] = profile
            
            return {
                "profile": profile.__dict__,
                "patterns": patterns,
                "risk_metrics": risk_metrics,
                "recommendations": self._generate_recommendations(profile)
            }
            
        except Exception as e:
            logger.error(f"Error profiling wallet {wallet_address}: {e}")
            return None

    async def _fetch_wallet_transactions(
        self,
        wallet_address: str
    ) -> List[Dict]:
        """Fetch all relevant transactions for a wallet."""
        try:
            # Calculate start time
            start_time = int((datetime.now() - 
                            timedelta(seconds=self.analysis_window)).timestamp())
            
            # Get transaction signatures
            signatures = await self.rpc_client.get_signatures_for_address(
                Pubkey.from_string(wallet_address),
                until=str(start_time)
            )
            
            transactions = []
            for sig_info in signatures.value:
                tx = await self.rpc_client.get_transaction(sig_info.signature)
                if self._is_relevant_transaction(tx):
                    transactions.append(tx)
                    
            return transactions
            
        except Exception as e:
            logger.error(f"Error fetching transactions: {e}")
            return []

    async def _meets_analysis_criteria(self, transactions: List[Dict]) -> bool:
        """Check if wallet meets minimum analysis criteria."""
        try:
            if not transactions:
                return False
                
            total_volume = sum(
                self._calculate_transaction_volume(tx)
                for tx in transactions
            )
            
            return total_volume >= self.min_volume_usd
            
        except Exception as e:
            logger.error(f"Error checking analysis criteria: {e}")
            return False

    async def _calculate_base_metrics(self, transactions: List[Dict]) -> Dict:
        """Calculate base wallet metrics."""
        try:
            metrics = {
                'total_volume_usd': 0.0,
                'transaction_count': len(transactions),
                'unique_tokens': set(),
                'average_position_size': 0.0,
                'holding_periods': [],
                'profit_loss': 0.0,
                'first_seen': None,
                'last_active': None
            }
            
            positions = defaultdict(float)
            entry_prices = {}
            
            for tx in sorted(transactions, key=lambda x: x['timestamp']):
                # Update volume
                volume = self._calculate_transaction_volume(tx)
                metrics['total_volume_usd'] += volume
                
                # Track tokens
                token = self._extract_token_address(tx)
                if token:
                    metrics['unique_tokens'].add(token)
                    
                # Track positions and P&L
                if self._is_buy_transaction(tx):
                    token_amount = self._extract_token_amount(tx)
                    positions[token] += token_amount
                    entry_prices[token] = self._extract_token_price(tx)
                elif self._is_sell_transaction(tx):
                    token_amount = self._extract_token_amount(tx)
                    if token in positions:
                        # Calculate P&L
                        exit_price = self._extract_token_price(tx)
                        entry_price = entry_prices[token]
                        metrics['profit_loss'] += (
                            token_amount * (exit_price - entry_price)
                        )
                        positions[token] -= token_amount
                        
                # Update timestamps
                tx_time = self._extract_timestamp(tx)
                if metrics['first_seen'] is None:
                    metrics['first_seen'] = tx_time
                metrics['last_active'] = tx_time
                
            # Calculate average position size
            if metrics['transaction_count'] > 0:
                metrics['average_position_size'] = (
                    metrics['total_volume_usd'] / metrics['transaction_count']
                )
                
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating base metrics: {e}")
            return {}

    async def _analyze_trading_patterns(self, transactions: List[Dict]) -> List[Dict]:
        """Analyze trading patterns in transaction history."""
        try:
            patterns = []
            
            # Check for high frequency trading
            if self._detect_hft_pattern(transactions):
                patterns.append({
                    'type': 'high_frequency_trading',
                    'confidence': self._calculate_hft_confidence(transactions),
                    'metrics': self._calculate_hft_metrics(transactions)
                })
            
            # Check for whale activity
            if self._detect_whale_pattern(transactions):
                patterns.append({
                    'type': 'whale_activity',
                    'confidence': self._calculate_whale_confidence(transactions),
                    'metrics': self._calculate_whale_metrics(transactions)
                })
            
            # Check for wash trading
            if self._detect_wash_trading(transactions):
                patterns.append({
                    'type': 'wash_trading',
                    'confidence': self._calculate_wash_confidence(transactions),
                    'metrics': self._calculate_wash_metrics(transactions)
                })
                
            return patterns
            
        except Exception as e:
            logger.error(f"Error analyzing trading patterns: {e}")
            return []

    def _calculate_risk_metrics(
        self,
        base_metrics: Dict,
        patterns: List[Dict]
    ) -> Dict:
        """Calculate comprehensive risk metrics."""
        try:
            # Calculate base risk factors
            volume_risk = min(1.0, base_metrics['total_volume_usd'] / 1_000_000)
            frequency_risk = min(1.0, base_metrics['transaction_count'] / 1000)
            
            # Calculate pattern-based risk
            pattern_risk = 0.0
            if patterns:
                pattern_risks = {
                    'high_frequency_trading': 0.6,
                    'whale_activity': 0.7,
                    'wash_trading': 0.9
                }
                pattern_risk = max(
                    pattern_risks.get(p['type'], 0) * p['confidence']
                    for p in patterns
                )
            
            # Calculate holding time risk
            holding_time_risk = 0.0
            if base_metrics['holding_periods']:
                avg_holding_time = np.mean(base_metrics['holding_periods'])
                holding_time_risk = max(0, 1 - (avg_holding_time / (24 * 3600)))
            
            # Calculate profit/loss risk
            pnl_risk = min(1.0, abs(base_metrics['profit_loss']) / 100_000)
            
            # Combine risk factors
            total_risk = (
                volume_risk * 0.3 +
                frequency_risk * 0.2 +
                pattern_risk * 0.2 +
                holding_time_risk * 0.15 +
                pnl_risk * 0.15
            )
            
            return {
                'total_risk': total_risk,
                'volume_risk': volume_risk,
                'frequency_risk': frequency_risk,
                'pattern_risk': pattern_risk,
                'holding_time_risk': holding_time_risk,
                'pnl_risk': pnl_risk,
                'risk_level': self._get_risk_level(total_risk)
            }
            
        except Exception as e:
            logger.error(f"Error calculating risk metrics: {e}")
            return {}

    def _create_wallet_profile(
        self,
        wallet_address: str,
        base_metrics: Dict,
        patterns: List[Dict],
        risk_metrics: Dict
    ) -> WalletProfile:
        """Create wallet profile from analysis results."""
        try:
            return WalletProfile(
                address=wallet_address,
                total_volume_usd=base_metrics['total_volume_usd'],
                transaction_count=base_metrics['transaction_count'],
                unique_tokens=base_metrics['unique_tokens'],
                average_position_size=base_metrics['average_position_size'],
                average_holding_time=np.mean(base_metrics['holding_periods'])
                    if base_metrics['holding_periods'] else 0,
                profit_loss=base_metrics['profit_loss'],
                risk_score=risk_metrics['total_risk'],
                activity_score=self._calculate_activity_score(base_metrics),
                first_seen=base_metrics['first_seen'],
                last_active=base_metrics['last_active'],
                known_associates=self._find_known_associates(wallet_address),
                behavior_tags=self._generate_behavior_tags(patterns)
            )
            
        except Exception as e:
            logger.error(f"Error creating wallet profile: {e}")
            raise

    def _get_risk_level(self, risk_score: float) -> str:
        """Convert risk score to risk level."""
        if risk_score >= 0.8:
            return "CRITICAL"
        elif risk_score >= 0.6:
            return "HIGH"
        elif risk_score >= 0.4:
            return "MEDIUM"
        return "LOW"

    def _find_known_associates(self, wallet_address: str) -> Set[str]:
        """Find wallets frequently interacting with this wallet."""
        try:
            associates = set()
            
            for counterparty, strength in self.relationship_graph[wallet_address].items():
                if strength >= 0.5:  # Strong relationship threshold
                    associates.add(counterparty)
                    
            return associates
            
        except Exception as e:
            logger.error(f"Error finding known associates: {e}")
            return set()

    def _generate_behavior_tags(self, patterns: List[Dict]) -> Set[str]:
        """Generate behavior tags based on detected patterns."""
        try:
            tags = set()
            
            for pattern in patterns:
                if pattern['type'] == 'high_frequency_trading':
                    tags.add('hft_trader')
                elif pattern['type'] == 'whale_activity':
                    tags.add('whale')
                elif pattern['type'] == 'wash_trading':
                    tags.add('wash_trader')
                    
            return tags
            
        except Exception as e:
            logger.error(f"Error generating behavior tags: {e}")
            return set()

    def _generate_recommendations(self, profile: WalletProfile) -> List[str]:
        """Generate recommendations based on wallet profile."""
        try:
            recommendations = []
            
            # Risk-based recommendations
            if profile.risk_score >= 0.8:
                recommendations.append("HIGH_RISK_MONITOR_CLOSELY")
            elif profile.risk_score >= 0.6:
                recommendations.append("ELEVATED_RISK_INCREASED_MONITORING")
                
            # Pattern-based recommendations
            if 'hft_trader' in profile.behavior_tags:
                recommendations.append("MONITOR_HFT_IMPACT_ON_MARKETS")
            if 'whale' in profile.behavior_tags:
                recommendations.append("TRACK_LARGE_POSITION_MOVEMENTS")
            if 'wash_trader' in profile.behavior_tags:
                recommendations.append("INVESTIGATE_TRADING_PATTERNS")

            # Activity-based recommendations
            if profile.activity_score > 0.8:
                recommendations.append("HIGH_ACTIVITY_ADDITIONAL_SCRUTINY")
            if len(profile.known_associates) > 10:
                recommendations.append("ANALYZE_WALLET_NETWORK")

            return recommendations

        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return []

    def _calculate_activity_score(self, base_metrics: Dict) -> float:
        """Calculate overall activity score."""
        try:
            if not base_metrics:
                return 0.0

            # Calculate recency factor
            time_since_last = (datetime.now() - base_metrics['last_active']).total_seconds()
            recency_factor = np.exp(-time_since_last / (7 * 24 * 3600))  # 7-day scale

            # Calculate volume factor
            volume_factor = min(1.0, base_metrics['total_volume_usd'] / 1_000_000)

            # Calculate frequency factor
            frequency_factor = min(1.0, base_metrics['transaction_count'] / 1000)

            # Combine factors
            activity_score = (
                recency_factor * 0.4 +
                volume_factor * 0.3 +
                frequency_factor * 0.3
            )

            return float(activity_score)

        except Exception as e:
            logger.error(f"Error calculating activity score: {e}")
            return 0.0

    def _detect_hft_pattern(self, transactions: List[Dict]) -> bool:
        """Detect high-frequency trading patterns."""
        try:
            thresholds = self.thresholds['high_frequency_trading']
            
            # Group transactions by day
            daily_counts = defaultdict(int)
            for tx in transactions:
                day = self._extract_timestamp(tx).date()
                daily_counts[day] += 1

            # Check daily trade counts
            high_frequency_days = sum(
                1 for count in daily_counts.values()
                if count >= thresholds['min_daily_trades']
            )

            # Check average holding time
            holding_times = self._calculate_holding_times(transactions)
            avg_holding_time = np.mean(holding_times) if holding_times else float('inf')

            return (high_frequency_days >= 3 and  # At least 3 days of high activity
                    avg_holding_time <= thresholds['max_holding_time'])

        except Exception as e:
            logger.error(f"Error detecting HFT pattern: {e}")
            return False

    def _detect_whale_pattern(self, transactions: List[Dict]) -> bool:
        """Detect whale trading patterns."""
        try:
            thresholds = self.thresholds['whale_activity']
            
            # Calculate total volume
            total_volume = sum(
                self._calculate_transaction_volume(tx)
                for tx in transactions
            )

            # Get maximum position size
            max_position = max(
                self._calculate_transaction_volume(tx)
                for tx in transactions
            )

            return (total_volume >= thresholds['min_total_volume'] and
                    max_position >= thresholds['min_position_size'])

        except Exception as e:
            logger.error(f"Error detecting whale pattern: {e}")
            return False

    def _detect_wash_trading(self, transactions: List[Dict]) -> bool:
        """Detect wash trading patterns."""
        try:
            thresholds = self.thresholds['wash_trading']
            
            # Build transaction graph
            graph = defaultdict(list)
            for tx in transactions:
                sender = self._extract_sender(tx)
                receiver = self._extract_receiver(tx)
                if sender and receiver:
                    graph[sender].append((receiver, tx))

            # Look for cycles
            for start_address in graph:
                if self._find_trading_cycle(graph, start_address, thresholds):
                    return True

            return False

        except Exception as e:
            logger.error(f"Error detecting wash trading: {e}")
            return False

    def get_wallet_analysis(self, wallet_address: str) -> Dict:
        """Get comprehensive analysis for a wallet."""
        try:
            if wallet_address not in self.wallet_profiles:
                return {"error": "No profile available"}

            profile = self.wallet_profiles[wallet_address]
            
            return {
                "profile": profile.__dict__,
                "risk_metrics": {
                    "risk_level": self._get_risk_level(profile.risk_score),
                    "risk_score": profile.risk_score,
                    "activity_score": profile.activity_score
                },
                "patterns": [
                    {"type": tag, "confidence": 1.0}
                    for tag in profile.behavior_tags
                ],
                "network_analysis": {
                    "known_associates": len(profile.known_associates),
                    "relationship_strength": self._calculate_relationship_strength(
                        wallet_address,
                        profile.known_associates
                    )
                },
                "recommendations": self._generate_recommendations(profile)
            }

        except Exception as e:
            logger.error(f"Error getting wallet analysis: {e}")
            return {"error": str(e)}

if __name__ == "__main__":
    # Example usage
    async def main():
        # Initialize RPC client
        client = AsyncClient("https://api.mainnet-beta.solana.com")
        
        # Create profiler instance
        profiler = WalletProfiler(
            rpc_client=client,
            min_volume_usd=1000,
            analysis_window=30 * 24 * 3600
        )
        
        # Example wallet analysis
        wallet_address = "ExampleWallet123"
        analysis = await profiler.profile_wallet(wallet_address)
        
        if analysis:
            print("\nWallet Profile:")
            print(f"Risk Level: {analysis['risk_metrics']['risk_level']}")
            print(f"Activity Score: {analysis['profile']['activity_score']:.2f}")
            print("\nBehavior Tags:")
            for tag in analysis['profile']['behavior_tags']:
                print(f"- {tag}")
            print("\nRecommendations:")
            for rec in analysis['recommendations']:
                print(f"- {rec}")

    asyncio.run(main())