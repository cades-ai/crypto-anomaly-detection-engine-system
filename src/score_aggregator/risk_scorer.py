"""
Crypto Anomaly Detection Engine System (CADES)
Risk Scorer Module

This module calculates risk scores based on aggregated metrics and patterns.
Implements risk assessment and warning generation.

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
class RiskAssessment:
    """Risk assessment result"""
    token_address: str
    timestamp: datetime
    risk_scores: Dict[str, float]
    overall_risk: float
    warning_signals: List[str]
    risk_factors: Dict[str, float]
    confidence: float

class RiskScorer:
    """Assesses risks based on aggregated metrics."""
    
    def __init__(
        self,
        risk_thresholds: Optional[Dict[str, float]] = None,
        risk_weights: Optional[Dict[str, float]] = None
    ):
        """Initialize the risk scorer."""
        self.risk_thresholds = risk_thresholds or {
            'high': 0.8,
            'medium': 0.6,
            'low': 0.4
        }
        
        self.risk_weights = risk_weights or {
            'volatility': 0.3,
            'liquidity': 0.2,
            'sentiment': 0.2,
            'whale': 0.2,
            'technical': 0.1
        }
        
        # Risk history tracking
        self.risk_history = defaultdict(list)

    async def assess_risk(
        self,
        token_address: str,
        metrics: Dict,
        market_state: Optional[Dict] = None
    ) -> RiskAssessment:
        """Calculate comprehensive risk assessment."""
        try:
            # Calculate individual risk scores
            risk_scores = self._calculate_risk_scores(metrics)
            
            # Calculate overall risk
            overall_risk = self._calculate_overall_risk(risk_scores)
            
            # Generate warning signals
            warnings = self._generate_warnings(
                risk_scores,
                overall_risk,
                market_state
            )
            
            # Identify risk factors
            risk_factors = self._identify_risk_factors(
                metrics,
                risk_scores
            )
            
            # Calculate confidence
            confidence = self._calculate_confidence(
                metrics,
                market_state
            )
            
            # Create assessment
            assessment = RiskAssessment(
                token_address=token_address,
                timestamp=datetime.now(),
                risk_scores=risk_scores,
                overall_risk=overall_risk,
                warning_signals=warnings,
                risk_factors=risk_factors,
                confidence=confidence
            )
            
            # Update history
            self._update_history(token_address, assessment)
            
            return assessment
            
        except Exception as e:
            logger.error(f"Error assessing risk: {e}")
            raise

    def _calculate_risk_scores(self, metrics: Dict) -> Dict[str, float]:
        """Calculate individual risk scores."""
        try:
            scores = {}
            
            # Volatility risk
            scores['volatility_risk'] = self._calculate_volatility_risk(
                metrics.get('market_metrics', {})
            )
            
            # Liquidity risk
            scores['liquidity_risk'] = self._calculate_liquidity_risk(
                metrics.get('chain_metrics', {})
            )
            
            # Sentiment risk
            scores['sentiment_risk'] = self._calculate_sentiment_risk(
                metrics.get('sentiment_metrics', {})
            )
            
            # Whale activity risk
            scores['whale_risk'] = self._calculate_whale_risk(
                metrics.get('chain_metrics', {})
            )
            
            # Technical risk
            scores['technical_risk'] = self._calculate_technical_risk(
                metrics.get('market_metrics', {})
            )
            
            return scores
            
        except Exception as e:
            logger.error(f"Error calculating risk scores: {e}")
            return {}

    def _calculate_overall_risk(self, risk_scores: Dict[str, float]) -> float:
        """Calculate overall risk score."""
        try:
            weighted_risks = [
                risk_scores.get(risk_type, 0) * weight
                for risk_type, weight in self.risk_weights.items()
            ]
            
            return float(np.sum(weighted_risks))
            
        except Exception as e:
            logger.error(f"Error calculating overall risk: {e}")
            return 0.0

    def _generate_warnings(
        self,
        risk_scores: Dict[str, float],
        overall_risk: float,
        market_state: Optional[Dict]
    ) -> List[str]:
        """Generate warning signals based on risks."""
        try:
            warnings = []
            
            # Overall risk warnings
            if overall_risk >= self.risk_thresholds['high']:
                warnings.append("CRITICAL_RISK_LEVEL")
            elif overall_risk >= self.risk_thresholds['medium']:
                warnings.append("HIGH_RISK_LEVEL")
            
            # Specific risk warnings
            if risk_scores.get('volatility_risk', 0) >= self.risk_thresholds['high']:
                warnings.append("HIGH_VOLATILITY_RISK")
                
            if risk_scores.get('liquidity_risk', 0) >= self.risk_thresholds['high']:
                warnings.append("LIQUIDITY_RISK")
                
            if risk_scores.get('whale_risk', 0) >= self.risk_thresholds['high']:
                warnings.append("WHALE_ACTIVITY_RISK")
            
            return warnings
            
        except Exception as e:
            logger.error(f"Error generating warnings: {e}")
            return []

    def _calculate_confidence(
        self,
        metrics: Dict,
        market_state: Optional[Dict]
    ) -> float:
        """Calculate confidence in risk assessment."""
        try:
            confidence_factors = []
            
            # Metric quality
            if 'confidence' in metrics:
                confidence_factors.append(metrics['confidence'])
            
            # Data completeness
            completeness = sum(
                1 for v in metrics.values()
                if isinstance(v, dict) and v
            ) / 3  # Expecting 3 metric types
            confidence_factors.append(completeness)
            
            # Market state confidence
            if market_state and 'data_quality' in market_state:
                confidence_factors.append(market_state['data_quality'])
            
            return float(np.mean(confidence_factors)) if confidence_factors else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating confidence: {e}")
            return 0.0

    def _identify_risk_factors(
        self,
        metrics: Dict,
        risk_scores: Dict[str, float]
    ) -> Dict[str, float]:
        """Identify contributing risk factors."""
        try:
            factors = {}
            
            # High risk factors
            for risk_type, score in risk_scores.items():
                if score >= self.risk_thresholds['medium']:
                    factors[risk_type] = score
            
            # Additional metric-based factors
            market_metrics = metrics.get('market_metrics', {})
            if market_metrics.get('price_momentum', 0) > 0.7:
                factors['price_momentum'] = market_metrics['price_momentum']
            
            sentiment_metrics = metrics.get('sentiment_metrics', {})
            if abs(sentiment_metrics.get('sentiment_change', 0)) > 0.5:
                factors['sentiment_change'] = abs(
                    sentiment_metrics['sentiment_change']
                )
            
            return factors
            
        except Exception as e:
            logger.error(f"Error identifying risk factors: {e}")
            return {}

    def _update_history(self, token_address: str, assessment: RiskAssessment) -> None:
        """Update risk assessment history."""
        try:
            self.risk_history[token_address].append(assessment)
            
            # Keep last 1000 entries
            if len(self.risk_history[token_address]) > 1000:
                self.risk_history[token_address] = \
                    self.risk_history[token_address][-1000:]
                    
        except Exception as e:
            logger.error(f"Error updating history: {e}")

if __name__ == "__main__":
    async def main():
        scorer = RiskScorer()
        
        # Example metrics
        metrics = {
            'market_metrics': {
                'volatility': 0.7,
                'price_momentum': 0.8
            },
            'chain_metrics': {
                'whale_activity': 0.6,
                'liquidity': 0.5
            },
            'sentiment_metrics': {
                'sentiment_score': -0.3,
                'sentiment_change': -0.6
            },
            'confidence': 0.85
        }
        
        assessment = await scorer.assess_risk(
            "ExampleToken123",
            metrics
        )
        
        print(f"Overall Risk: {assessment.overall_risk:.2f}")
        print(f"Warning Signals: {assessment.warning_signals}")
        print(f"Risk Factors: {assessment.risk_factors}")
        
    import asyncio
    asyncio.run(main())