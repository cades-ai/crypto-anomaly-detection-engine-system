"""
Crypto Anomaly Detection Engine System (CADES)
Social Momentum Analysis Module

This module implements advanced detection and analysis of social momentum patterns
around tokens, focusing on social velocity, acceleration, and coordinated activity.
Provides quantitative metrics for social impact and market perception.

Author: CADES Team
License: Proprietary
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple, Union
import numpy as np
from collections import defaultdict, deque
import logging
from enum import Enum
from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MomentumType(Enum):
    """Classification of social momentum patterns"""
    ORGANIC_ACCELERATION = "organic_acceleration"
    COORDINATED_CAMPAIGN = "coordinated_campaign"
    AUTOMATED_AMPLIFICATION = "automated_amplification"
    INFLUENCER_CATALYST = "influencer_catalyst"
    VIRAL_ACCELERATION = "viral_acceleration"
    ARTIFICIAL_AMPLIFICATION = "artificial_amplification"

@dataclass
class MomentumMetrics:
    """Container for social momentum analysis metrics"""
    token_address: str
    timestamp: datetime
    momentum_score: float
    momentum_type: MomentumType
    velocity: float
    acceleration: float
    organic_ratio: float
    amplification_factor: float
    sentiment_velocity: float
    key_drivers: List[str] = field(default_factory=list)
    active_channels: Set[str] = field(default_factory=set)
    automation_coefficient: float = 0.0
    risk_indicators: List[str] = field(default_factory=list)
    
class SocialMomentumAnalyzer:
    """
    Advanced social momentum analyzer for token markets.
    Implements multi-channel analysis of social velocity and market perception.
    """
    
    def __init__(
        self,
        embedding_model,
        rpc_url: str = "https://api.mainnet-beta.solana.com",
        min_momentum_threshold: int = 100,
        analysis_window: int = 24 * 3600,
        update_interval: int = 300,
        organic_threshold: float = 0.7
    ):
        self.embedding_model = embedding_model
        self.solana_client = AsyncClient(rpc_url)
        self.min_momentum_threshold = min_momentum_threshold
        self.analysis_window = analysis_window
        self.update_interval = update_interval
        self.organic_threshold = organic_threshold
        
        # Initialize data structures
        self.velocity_history = defaultdict(lambda: deque(maxlen=1000))
        self.channel_profiles = {}
        self.momentum_metrics = defaultdict(list)
        
        # Analysis thresholds
        self.thresholds = {
            'velocity': 2.0,
            'coordination': 0.8,
            'automation': 0.7,
            'sentiment_velocity': 3.0
        }
        
        # Platform-specific settings
        self.platforms = {
            'twitter': {'weight': 0.4, 'min_activity': 50},
            'telegram': {'weight': 0.3, 'min_activity': 30},
            'discord': {'weight': 0.3, 'min_activity': 20}
        }

    async def analyze_social_momentum(
        self,
        token_address: str,
        social_data: Dict,
        market_data: Optional[Dict] = None
    ) -> Optional[MomentumMetrics]:
        """Analyze social momentum for a token."""
        try:
            if not self._meets_momentum_threshold(social_data):
                return None

            # Get on-chain data
            chain_data = await self._get_chain_data(token_address)
            
            # Calculate base metrics
            velocity_metrics = self._calculate_velocity_metrics(social_data)
            organic_metrics = self._analyze_organic_activity(social_data)
            sentiment_metrics = self._analyze_sentiment_velocity(social_data)
            
            # Calculate momentum score
            momentum_score = self._calculate_momentum_score(
                velocity_metrics,
                organic_metrics,
                sentiment_metrics,
                chain_data
            )
            
            # Determine momentum type
            momentum_type = self._classify_momentum_type(
                velocity_metrics,
                organic_metrics,
                sentiment_metrics
            )
            
            # Generate metrics
            metrics = MomentumMetrics(
                token_address=token_address,
                timestamp=datetime.now(),
                momentum_score=momentum_score,
                momentum_type=momentum_type,
                velocity=velocity_metrics['velocity'],
                acceleration=velocity_metrics['acceleration'],
                organic_ratio=organic_metrics['organic_ratio'],
                amplification_factor=organic_metrics['amplification'],
                sentiment_velocity=sentiment_metrics['velocity'],
                key_drivers=self._identify_key_drivers(social_data),
                active_channels=self._get_active_channels(social_data),
                automation_coefficient=organic_metrics['automation_coefficient'],
                risk_indicators=self._generate_risk_indicators(
                    momentum_score,
                    organic_metrics,
                    velocity_metrics
                )
            )
            
            # Update history
            self.momentum_metrics[token_address].append(metrics)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error in social momentum analysis: {e}")
            return None

    async def _get_chain_data(self, token_address: str) -> Dict:
        """Get relevant on-chain data."""
        try:
            supply_info = await self.solana_client.get_token_supply(
                Pubkey.from_string(token_address)
            )
            
            signatures = await self.solana_client.get_signatures_for_address(
                Pubkey.from_string(token_address),
                limit=100
            )
            
            return {
                'supply': supply_info.value.amount,
                'recent_transactions': len(signatures.value),
                'signatures': signatures.value
            }
        except Exception as e:
            logger.error(f"Error fetching chain data: {e}")
            return {}

    def _calculate_velocity_metrics(self, social_data: Dict) -> Dict:
        """Calculate social velocity metrics."""
        try:
            metrics = {}
            
            # Calculate activity velocity
            current_velocity = self._calculate_current_velocity(social_data)
            baseline_velocity = self._get_baseline_velocity(social_data)
            
            # Calculate acceleration
            acceleration = self._calculate_acceleration(current_velocity, baseline_velocity)
            
            # Calculate momentum components
            metrics['velocity'] = current_velocity
            metrics['normalized_velocity'] = current_velocity / baseline_velocity if baseline_velocity > 0 else 1.0
            metrics['acceleration'] = acceleration
            metrics['momentum'] = current_velocity * acceleration
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating velocity metrics: {e}")
            return {'velocity': 0.0, 'acceleration': 0.0, 'momentum': 0.0}

    def _analyze_organic_activity(self, social_data: Dict) -> Dict:
        """Analyze organic vs artificial activity."""
        try:
            # Extract account features
            account_ages = self._extract_account_ages(social_data)
            activity_patterns = self._analyze_activity_patterns(social_data)
            content_diversity = self._calculate_content_diversity(social_data)
            
            # Calculate organic ratio
            organic_ratio = self._calculate_organic_ratio(
                account_ages,
                activity_patterns,
                content_diversity
            )
            
            # Detect automation
            automation_coefficient = self._detect_automation(social_data)
            
            return {
                'organic_ratio': organic_ratio,
                'automation_coefficient': automation_coefficient,
                'amplification': 1.0 - organic_ratio,
                'account_trust_score': np.mean(account_ages) if account_ages else 0.0,
                'content_authenticity': content_diversity
            }
            
        except Exception as e:
            logger.error(f"Error analyzing organic activity: {e}")
            return {'organic_ratio': 0.0, 'automation_coefficient': 1.0}

    def _analyze_sentiment_velocity(self, social_data: Dict) -> Dict:
        """Analyze sentiment velocity and acceleration."""
        try:
            sentiment_scores = social_data.get('sentiment_scores', [])
            if not sentiment_scores:
                return {'velocity': 0.0, 'acceleration': 0.0}
            
            # Calculate sentiment velocity
            current_sentiment = np.mean(sentiment_scores[-10:])
            baseline_sentiment = np.mean(sentiment_scores[:-10]) if len(sentiment_scores) > 10 else current_sentiment
            
            sentiment_velocity = (current_sentiment - baseline_sentiment) / self.update_interval
            
            # Calculate sentiment acceleration
            sentiment_acceleration = self._calculate_sentiment_acceleration(sentiment_scores)
            
            return {
                'velocity': sentiment_velocity,
                'acceleration': sentiment_acceleration,
                'current_sentiment': current_sentiment,
                'sentiment_momentum': sentiment_velocity * sentiment_acceleration
            }
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment velocity: {e}")
            return {'velocity': 0.0, 'acceleration': 0.0}

    def _calculate_momentum_score(
        self,
        velocity_metrics: Dict,
        organic_metrics: Dict,
        sentiment_metrics: Dict,
        chain_data: Dict
    ) -> float:
        """Calculate overall momentum score."""
        try:
            # Weight components
            velocity_score = velocity_metrics['momentum'] * 0.4
            organic_score = organic_metrics['organic_ratio'] * 0.3
            sentiment_score = sentiment_metrics['sentiment_momentum'] * 0.2
            
            # Add on-chain component
            chain_score = self._calculate_chain_score(chain_data) * 0.1
            
            # Combine scores
            momentum_score = (
                velocity_score +
                organic_score +
                sentiment_score +
                chain_score
            )
            
            return min(1.0, momentum_score)
            
        except Exception as e:
            logger.error(f"Error calculating momentum score: {e}")
            return 0.0

    def _classify_momentum_type(
        self,
        velocity_metrics: Dict,
        organic_metrics: Dict,
        sentiment_metrics: Dict
    ) -> MomentumType:
        """Classify the type of momentum pattern."""
        try:
            # Check for automated amplification
            if organic_metrics['automation_coefficient'] > self.thresholds['automation']:
                return MomentumType.AUTOMATED_AMPLIFICATION
            
            # Check for coordinated campaign
            if velocity_metrics['acceleration'] > self.thresholds['velocity']:
                if organic_metrics['organic_ratio'] < self.organic_threshold:
                    return MomentumType.COORDINATED_CAMPAIGN
                    
            # Check for viral acceleration
            if sentiment_metrics['velocity'] > self.thresholds['sentiment_velocity']:
                return MomentumType.VIRAL_ACCELERATION
                
            # Check for organic growth
            if organic_metrics['organic_ratio'] > self.organic_threshold:
                return MomentumType.ORGANIC_ACCELERATION
                
            return MomentumType.ARTIFICIAL_AMPLIFICATION
            
        except Exception as e:
            logger.error(f"Error classifying momentum type: {e}")
            return MomentumType.ARTIFICIAL_AMPLIFICATION

    def _generate_risk_indicators(
        self,
        momentum_score: float,
        organic_metrics: Dict,
        velocity_metrics: Dict
    ) -> List[str]:
        """Generate risk indicators based on metrics."""
        try:
            indicators = []
            
            # Check automation risk
            if organic_metrics['automation_coefficient'] > self.thresholds['automation']:
                indicators.append("HIGH_AUTOMATION_DETECTED")
                
            # Check velocity anomalies
            if velocity_metrics['acceleration'] > self.thresholds['velocity'] * 2:
                indicators.append("ABNORMAL_ACCELERATION")
                
            # Check organic ratio
            if organic_metrics['organic_ratio'] < self.organic_threshold / 2:
                indicators.append("LOW_ORGANIC_ACTIVITY")
                
            # Check overall momentum
            if momentum_score > 0.8:
                indicators.append("EXCESSIVE_MOMENTUM")
                
            return indicators
            
        except Exception as e:
            logger.error(f"Error generating risk indicators: {e}")
            return ["ERROR_GENERATING_INDICATORS"]

    async def get_momentum_analysis(self, token_address: str) -> Dict:
        """Get comprehensive momentum analysis for a token."""
        try:
            metrics = self.momentum_metrics.get(token_address, [])
            if not metrics:
                return {"status": "No momentum data available"}
            
            recent_metrics = [m for m in metrics if 
                (datetime.now() - m.timestamp).total_seconds() < self.analysis_window]
            
            return {
                "current_metrics": recent_metrics[-1] if recent_metrics else None,
                "momentum_trend": self._analyze_momentum_trend(recent_metrics),
                "organic_trend": self._analyze_organic_trend(recent_metrics),
                "risk_summary": self._summarize_risks(recent_metrics),
                "market_impact": await self._analyze_market_impact(token_address)
            }
            
        except Exception as e:
            logger.error(f"Error getting momentum analysis: {e}")
            return {"error": str(e)}

if __name__ == "__main__":
    async def main():
        # Initialize with mock embedding model
        class MockEmbeddingModel:
            def get_embeddings(self, texts):
                return np.random.rand(len(texts), 128)
                
        analyzer = SocialMomentumAnalyzer(
            embedding_model=MockEmbeddingModel(),
            min_momentum_threshold=100,
            analysis_window=24 * 3600
        )
        
        # Example data
        social_data = {
            "messages": ["Moon soon! 🚀"] * 10,
            "sentiment_scores": [0.8] * 10,
            "accounts": ["user1"] * 10
        }
        
        metrics = await analyzer.analyze_social_momentum(
            "TokenXYZ",
            social_data
        )
        
        if metrics:
            print(f"Momentum Score: {metrics.momentum_score:.2f}")
            print(f"Momentum Type: {metrics.momentum_type}")
            print(f"Organic Ratio: {metrics.organic_ratio:.2f}")
            print(f"Risk Indicators: {metrics.risk_indicators}")
            
    asyncio.run(main())