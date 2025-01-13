"""
Crypto Anomaly Detection Engine System (CADES)
Metric Calculator Module

This module aggregates and calculates metrics from various analysis modules.
Implements core metric calculation and normalization.

Author: CADES Team
License: Proprietary
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import numpy as np
import logging
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class AggregatedMetrics:
    """Container for aggregated metrics"""
    token_address: str
    timestamp: datetime
    chain_metrics: Dict[str, float]
    sentiment_metrics: Dict[str, float]
    market_metrics: Dict[str, float]
    composite_score: float
    confidence: float

class MetricCalculator:
    """Aggregates and calculates metrics from various analysis modules."""
    
    def __init__(
        self,
        update_interval: int = 60,
        metric_weights: Optional[Dict[str, float]] = None
    ):
        """Initialize the metric calculator."""
        self.update_interval = update_interval
        self.metric_weights = metric_weights or {
            'chain': 0.4,
            'sentiment': 0.3,
            'market': 0.3
        }
        
        # Tracking
        self.metric_history = defaultdict(list)

    async def calculate_metrics(
        self,
        token_address: str,
        chain_data: Dict,
        sentiment_data: Dict,
        market_data: Dict
    ) -> AggregatedMetrics:
        """Calculate aggregated metrics."""
        try:
            # Calculate individual metrics
            chain_metrics = self._calculate_chain_metrics(chain_data)
            sentiment_metrics = self._calculate_sentiment_metrics(sentiment_data)
            market_metrics = self._calculate_market_metrics(market_data)
            
            # Calculate composite score
            composite_score = self._calculate_composite_score(
                chain_metrics,
                sentiment_metrics,
                market_metrics
            )
            
            # Calculate confidence
            confidence = self._calculate_confidence(
                chain_data,
                sentiment_data,
                market_data
            )
            
            # Create result
            metrics = AggregatedMetrics(
                token_address=token_address,
                timestamp=datetime.now(),
                chain_metrics=chain_metrics,
                sentiment_metrics=sentiment_metrics,
                market_metrics=market_metrics,
                composite_score=composite_score,
                confidence=confidence
            )
            
            # Update history
            self._update_history(token_address, metrics)
            
            return metrics
        
        except Exception as e:
            logger.error(f"Error calculating metrics: {e}")
            raise

    def _calculate_chain_metrics(self, chain_data: Dict) -> Dict[str, float]:
        """Calculate on-chain metrics."""
        try:
            metrics = {}
            
            # Transaction metrics
            metrics['transaction_volume'] = min(
                1.0,
                chain_data.get('transaction_volume', 0) / 1_000_000
            )
            
            # Wallet metrics
            metrics['whale_activity'] = min(
                1.0,
                chain_data.get('whale_activity', 0)
            )
            
            # Liquidity metrics
            metrics['liquidity_score'] = min(
                1.0,
                chain_data.get('liquidity', 0) / 500_000
            )
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating chain metrics: {e}")
            return {}

    def _calculate_sentiment_metrics(self, sentiment_data: Dict) -> Dict[str, float]:
        """Calculate sentiment metrics."""
        try:
            metrics = {}
            
            # Overall sentiment
            metrics['sentiment_score'] = sentiment_data.get('sentiment_score', 0)
            
            # Social volume
            metrics['social_volume'] = min(
                1.0,
                sentiment_data.get('social_volume', 0) / 1000
            )
            
            # Sentiment momentum
            metrics['sentiment_change'] = sentiment_data.get('sentiment_change', 0)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating sentiment metrics: {e}")
            return {}

    def _calculate_market_metrics(self, market_data: Dict) -> Dict[str, float]:
        """Calculate market metrics."""
        try:
            metrics = {}
            
            # Volatility
            metrics['volatility'] = min(
                1.0,
                market_data.get('volatility', 0)
            )
            
            # Price momentum
            metrics['price_momentum'] = market_data.get('price_momentum', 0)
            
            # Volume profile
            metrics['volume_profile'] = min(
                1.0,
                market_data.get('volume_profile', 0)
            )
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating market metrics: {e}")
            return {}

    def _calculate_composite_score(
        self,
        chain_metrics: Dict[str, float],
        sentiment_metrics: Dict[str, float],
        market_metrics: Dict[str, float]
    ) -> float:
        """Calculate composite score from all metrics."""
        try:
            scores = {
                'chain': np.mean(list(chain_metrics.values())),
                'sentiment': np.mean(list(sentiment_metrics.values())),
                'market': np.mean(list(market_metrics.values()))
            }
            
            composite = sum(
                scores[key] * self.metric_weights[key]
                for key in scores
            )
            
            return float(composite)
            
        except Exception as e:
            logger.error(f"Error calculating composite score: {e}")
            return 0.0

    def _calculate_confidence(
        self,
        chain_data: Dict,
        sentiment_data: Dict,
        market_data: Dict
    ) -> float:
        """Calculate confidence score for metrics."""
        try:
            confidences = []
            
            # Chain data confidence
            if chain_data.get('data_points', 0) > 0:
                confidences.append(
                    min(1.0, chain_data['data_points'] / 100)
                )
            
            # Sentiment confidence
            if 'confidence' in sentiment_data:
                confidences.append(sentiment_data['confidence'])
            
            # Market confidence
            if 'data_quality' in market_data:
                confidences.append(market_data['data_quality'])
            
            return float(np.mean(confidences)) if confidences else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating confidence: {e}")
            return 0.0

    def _update_history(
        self,
        token_address: str,
        metrics: AggregatedMetrics
    ) -> None:
        """Update metric history."""
        try:
            self.metric_history[token_address].append(metrics)
            
            # Keep last 1000 entries
            if len(self.metric_history[token_address]) > 1000:
                self.metric_history[token_address] = \
                    self.metric_history[token_address][-1000:]
                    
        except Exception as e:
            logger.error(f"Error updating history: {e}")

if __name__ == "__main__":
    async def main():
        calculator = MetricCalculator()
        
        # Example data
        chain_data = {
            'transaction_volume': 500000,
            'whale_activity': 0.7,
            'liquidity': 300000,
            'data_points': 150
        }
        
        sentiment_data = {
            'sentiment_score': 0.8,
            'social_volume': 500,
            'sentiment_change': 0.2,
            'confidence': 0.9
        }
        
        market_data = {
            'volatility': 0.4,
            'price_momentum': 0.6,
            'volume_profile': 0.7,
            'data_quality': 0.85
        }
        
        metrics = await calculator.calculate_metrics(
            "ExampleToken123",
            chain_data,
            sentiment_data,
            market_data
        )
        
        print(f"Composite Score: {metrics.composite_score:.2f}")
        print(f"Confidence: {metrics.confidence:.2f}")
        
    import asyncio
    asyncio.run(main())