"""
Crypto Anomaly Detection Engine Systen (CADES)
Volatility Calculator Module

This module implements advanced volatility calculations for Solana memecoins,
incorporating on-chain data, sentiment metrics, and liquidity patterns.

Author: CADES Team
License: Proprietary
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union
import logging
from collections import defaultdict, deque
from scipy.stats import norm
import warnings
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class VolatilityMetrics:
    """Container for volatility calculation results"""
    token_address: str
    timestamp: datetime
    realized_volatility: float
    implied_volatility: float
    historical_volatility: float
    relative_volatility: float
    volatility_indicators: Dict[str, float]
    risk_metrics: Dict[str, float]
    confidence_score: float
    warning_signals: List[str] = field(default_factory=list)

class VolatilityCalculator:
    """
    Advanced volatility calculator for Solana memecoins.
    Implements multiple volatility calculation methods and risk assessment.
    """
    
    def __init__(
        self,
        window_sizes: List[int] = [5, 15, 30, 60, 120],  # minutes
        vol_threshold: float = 0.5,
        update_interval: int = 60,  # seconds
        min_data_points: int = 30
    ):
        """
        Initialize the volatility calculator.
        
        Args:
            window_sizes: List of time windows for volatility calculation
            vol_threshold: Threshold for volatility warnings
            update_interval: Update interval in seconds
            min_data_points: Minimum points required for calculation
        """
        self.window_sizes = window_sizes
        self.vol_threshold = vol_threshold
        self.update_interval = update_interval
        self.min_data_points = min_data_points
        
        # Data structures
        self.price_history: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=10000)
        )
        self.volatility_history: Dict[str, List[VolatilityMetrics]] = defaultdict(list)
        
        # Tracking metrics
        self.metrics = defaultdict(list)
        self.alerts = defaultdict(list)
        
        # Statistical parameters
        self.ewm_spans = {
            'short': 12,   # 1 hour for 5-min data
            'medium': 72,  # 6 hours
            'long': 288    # 24 hours
        }

    def calculate_volatility(
        self,
        token_address: str,
        current_price: float,
        timestamp: datetime,
        volume: Optional[float] = None,
        liquidity_data: Optional[Dict] = None,
        sentiment_data: Optional[Dict] = None
    ) -> VolatilityMetrics:
        """
        Calculate comprehensive volatility metrics.
        
        Args:
            token_address: Token contract address
            current_price: Current token price
            timestamp: Current timestamp
            volume: Trading volume (optional)
            liquidity_data: Liquidity pool data (optional)
            sentiment_data: Sentiment metrics (optional)
            
        Returns:
            VolatilityMetrics containing calculation results
        """
        try:
            # Update price history
            self._update_price_history(token_address, current_price, timestamp)
            
            # Check minimum data points
            if len(self.price_history[token_address]) < self.min_data_points:
                logger.warning(f"Insufficient data points for {token_address}")
                return self._generate_default_metrics(token_address, timestamp)
            
            # Calculate basic volatility metrics
            realized_vol = self._calculate_realized_volatility(token_address)
            historical_vol = self._calculate_historical_volatility(token_address)
            implied_vol = self._calculate_implied_volatility(
                token_address,
                volume,
                liquidity_data
            )
            
            # Calculate relative volatility
            relative_vol = self._calculate_relative_volatility(
                realized_vol,
                historical_vol
            )
            
            # Calculate additional indicators
            volatility_indicators = self._calculate_volatility_indicators(
                token_address,
                volume,
                liquidity_data,
                sentiment_data
            )
            
            # Calculate risk metrics
            risk_metrics = self._calculate_risk_metrics(
                realized_vol,
                implied_vol,
                volatility_indicators
            )
            
            # Generate warning signals
            warnings = self._generate_warning_signals(
                realized_vol,
                volatility_indicators,
                risk_metrics
            )
            
            # Calculate confidence score
            confidence = self._calculate_confidence_score(
                len(self.price_history[token_address]),
                volume,
                liquidity_data
            )
            
            # Create result
            metrics = VolatilityMetrics(
                token_address=token_address,
                timestamp=timestamp,
                realized_volatility=realized_vol,
                implied_volatility=implied_vol,
                historical_volatility=historical_vol,
                relative_volatility=relative_vol,
                volatility_indicators=volatility_indicators,
                risk_metrics=risk_metrics,
                confidence_score=confidence,
                warning_signals=warnings
            )
            
            # Update history
            self.volatility_history[token_address].append(metrics)
            
            # Update tracking metrics
            self._update_metrics(metrics)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating volatility: {e}")
            return self._generate_default_metrics(token_address, timestamp)

    def _calculate_realized_volatility(self, token_address: str) -> float:
        """Calculate realized volatility using returns standard deviation."""
        try:
            # Get price data
            prices = np.array([p['price'] for p in self.price_history[token_address]])
            
            # Calculate returns
            returns = np.diff(np.log(prices))
            
            # Calculate annualized volatility
            volatility = np.std(returns) * np.sqrt(365 * 24 * 60)
            
            return float(volatility)
            
        except Exception as e:
            logger.error(f"Error calculating realized volatility: {e}")
            return 0.0

    def _calculate_historical_volatility(self, token_address: str) -> float:
        """Calculate historical volatility using Parkinson's High-Low range."""
        try:
            # Get high-low data for each window
            highs = []
            lows = []
            
            for window in self.window_sizes:
                window_data = list(self.price_history[token_address])[-window:]
                if window_data:
                    prices = [d['price'] for d in window_data]
                    highs.append(max(prices))
                    lows.append(min(prices))
            
            if not highs or not lows:
                return 0.0
            
            # Calculate Parkinson's volatility
            ranges = np.log(np.array(highs) / np.array(lows))
            volatility = np.sqrt(
                1 / (4 * np.log(2)) * np.mean(ranges ** 2)
            ) * np.sqrt(365 * 24 * 60)
            
            return float(volatility)
            
        except Exception as e:
            logger.error(f"Error calculating historical volatility: {e}")
            return 0.0

    def _calculate_implied_volatility(
        self,
        token_address: str,
        volume: Optional[float],
        liquidity_data: Optional[Dict]
    ) -> float:
        """Calculate implied volatility using market data."""
        try:
            # Base volatility from price movement
            base_vol = self._calculate_realized_volatility(token_address)
            
            # Adjust for volume if available
            if volume is not None:
                vol_impact = min(1.0, volume / 1_000_000)  # Normalize to 1M USD
                base_vol *= (1 + vol_impact)
            
            # Adjust for liquidity if available
            if liquidity_data:
                liquidity = liquidity_data.get('total_liquidity', 0)
                depth = liquidity_data.get('depth', 0)
                
                # Calculate liquidity impact
                liq_impact = 1 - min(1.0, liquidity / 1_000_000)  # Less liquidity = higher vol
                depth_impact = 1 - min(1.0, depth / 100_000)      # Less depth = higher vol
                
                base_vol *= (1 + (liq_impact + depth_impact) / 2)
            
            return float(base_vol)
            
        except Exception as e:
            logger.error(f"Error calculating implied volatility: {e}")
            return 0.0

    def _calculate_volatility_indicators(
        self,
        token_address: str,
        volume: Optional[float],
        liquidity_data: Optional[Dict],
        sentiment_data: Optional[Dict]
    ) -> Dict[str, float]:
        """Calculate additional volatility indicators."""
        try:
            indicators = {}
            
            # Calculate price momentum
            momentum = self._calculate_price_momentum(token_address)
            indicators['price_momentum'] = momentum
            
            # Calculate volume volatility if volume data available
            if volume is not None:
                vol_vol = self._calculate_volume_volatility(token_address, volume)
                indicators['volume_volatility'] = vol_vol
            
            # Calculate liquidity volatility if data available
            if liquidity_data:
                liq_vol = self._calculate_liquidity_volatility(liquidity_data)
                indicators['liquidity_volatility'] = liq_vol
            
            # Incorporate sentiment volatility if available
            if sentiment_data:
                sent_vol = self._calculate_sentiment_volatility(sentiment_data)
                indicators['sentiment_volatility'] = sent_vol
            
            # Calculate trend strength
            trend = self._calculate_trend_strength(token_address)
            indicators['trend_strength'] = trend
            
            return indicators
            
        except Exception as e:
            logger.error(f"Error calculating volatility indicators: {e}")
            return {}

    def _calculate_risk_metrics(
        self,
        realized_vol: float,
        implied_vol: float,
        indicators: Dict[str, float]
    ) -> Dict[str, float]:
        """Calculate volatility-based risk metrics."""
        try:
            risk_metrics = {}
            
            # Volatility risk
            vol_risk = max(realized_vol, implied_vol) / self.vol_threshold
            risk_metrics['volatility_risk'] = min(1.0, vol_risk)
            
            # Momentum risk
            momentum = indicators.get('price_momentum', 0)
            risk_metrics['momentum_risk'] = min(1.0, abs(momentum))
            
            # Volume risk
            if 'volume_volatility' in indicators:
                vol_vol = indicators['volume_volatility']
                risk_metrics['volume_risk'] = min(1.0, vol_vol)
            
            # Liquidity risk
            if 'liquidity_volatility' in indicators:
                liq_vol = indicators['liquidity_volatility']
                risk_metrics['liquidity_risk'] = min(1.0, liq_vol)
            
            # Calculate combined risk
            weights = {
                'volatility_risk': 0.4,
                'momentum_risk': 0.3,
                'volume_risk': 0.2,
                'liquidity_risk': 0.1
            }
            
            combined_risk = sum(
                risk_metrics.get(metric, 0) * weight
                for metric, weight in weights.items()
                if metric in risk_metrics
            )
            
            risk_metrics['combined_risk'] = combined_risk
            
            return risk_metrics
            
        except Exception as e:
            logger.error(f"Error calculating risk metrics: {e}")
            return {}

    def _calculate_relative_volatility(
        self,
        realized_vol: float,
        historical_vol: float
    ) -> float:
        """Calculate relative volatility compared to historical."""
        try:
            if historical_vol == 0:
                return 0.0
            
            return realized_vol / historical_vol
            
        except Exception as e:
            logger.error(f"Error calculating relative volatility: {e}")
            return 0.0

    def _calculate_confidence_score(
        self,
        data_points: int,
        volume: Optional[float],
        liquidity_data: Optional[Dict]
    ) -> float:
        """Calculate confidence score for volatility metrics."""
        try:
            factors = []
            
            # Data quantity factor
            data_factor = min(1.0, data_points / self.min_data_points)
            factors.append(data_factor)
            
            # Volume factor
            if volume is not None:
                vol_factor = min(1.0, volume / 100_000)
                factors.append(vol_factor)
            
            # Liquidity factor
            if liquidity_data:
                liquidity = liquidity_data.get('total_liquidity', 0)
                liq_factor = min(1.0, liquidity / 1_000_000)
                factors.append(liq_factor)
            
            # Calculate combined confidence
            return float(np.mean(factors))
            
        except Exception as e:
            logger.error(f"Error calculating confidence score: {e}")
            return 0.0

    def _generate_warning_signals(
        self,
        realized_vol: float,
        indicators: Dict[str, float],
        risk_metrics: Dict[str, float]
    ) -> List[str]:
        """Generate warning signals based on volatility metrics."""
        try:
            warnings = []
            
            # Volatility warnings
            if realized_vol > self.vol_threshold * 2:
                warnings.append("CRITICAL_VOLATILITY")
            elif realized_vol > self.vol_threshold:
                warnings.append("HIGH_VOLATILITY")
            
            # Momentum warnings
            if abs(indicators.get('price_momentum', 0)) > 0.8:
                warnings.append("EXTREME_MOMENTUM")
            
            # Volume warnings
            if indicators.get('volume_volatility', 0) > 0.8:
                warnings.append("ABNORMAL_VOLUME")
            
            # Liquidity warnings
            if indicators.get('liquidity_volatility', 0) > 0.8:
                warnings.append("LIQUIDITY_RISK")
            
            # Combined risk warning
            if risk_metrics.get('combined_risk', 0) > 0.8:
                warnings.append("HIGH_RISK_LEVEL")
            
            return warnings
            
        except Exception as e:
            logger.error(f"Error generating warning signals: {e}")
            return []

    def _calculate_price_momentum(self, token_address: str) -> float:
        """Calculate price momentum indicator."""
        try:
            prices = [p['price'] for p in self.price_history[token_address]]
            if len(prices) < 2:
                return 0.0

            # Calculate returns
            returns = np.diff(np.log(prices))
            
            # Calculate exponential weights for different time spans
            weights = {
                'short': pd.Series(returns).ewm(span=self.ewm_spans['short']).mean().iloc[-1],
                'medium': pd.Series(returns).ewm(span=self.ewm_spans['medium']).mean().iloc[-1],
                'long': pd.Series(returns).ewm(span=self.ewm_spans['long']).mean().iloc[-1]
            }
            
            # Combine weighted momentum
            momentum = (
                weights['short'] * 0.5 +
                weights['medium'] * 0.3 +
                weights['long'] * 0.2
            )
            
            return float(momentum)
            
        except Exception as e:
            logger.error(f"Error calculating price momentum: {e}")
            return 0.0

    def _calculate_volume_volatility(
        self,
        token_address: str,
        current_volume: float
    ) -> float:
        """Calculate volume volatility."""
        try:
            # Get recent volumes
            volumes = [
                current_volume,
                *[entry.get('volume', 0) for entry in self.price_history[token_address]]
            ]
            
            if len(volumes) < 2:
                return 0.0

            # Calculate log changes
            vol_changes = np.diff(np.log(np.array(volumes) + 1))
            
            # Calculate volatility
            return float(np.std(vol_changes))
            
        except Exception as e:
            logger.error(f"Error calculating volume volatility: {e}")
            return 0.0

    def _calculate_liquidity_volatility(self, liquidity_data: Dict) -> float:
        """Calculate liquidity pool volatility."""
        try:
            # Extract liquidity history
            history = liquidity_data.get('history', [])
            if not history:
                return 0.0

            # Calculate liquidity changes
            liquidity_values = [entry['value'] for entry in history]
            changes = np.diff(np.array(liquidity_values))
            
            # Calculate normalized volatility
            mean_liquidity = np.mean(liquidity_values)
            if mean_liquidity == 0:
                return 0.0
                
            return float(np.std(changes) / mean_liquidity)
            
        except Exception as e:
            logger.error(f"Error calculating liquidity volatility: {e}")
            return 0.0

    def _calculate_sentiment_volatility(self, sentiment_data: Dict) -> float:
        """Calculate sentiment score volatility."""
        try:
            # Extract sentiment history
            history = sentiment_data.get('history', [])
            if not history:
                return 0.0

            # Calculate sentiment changes
            sentiment_scores = [entry['score'] for entry in history]
            changes = np.diff(sentiment_scores)
            
            return float(np.std(changes))
            
        except Exception as e:
            logger.error(f"Error calculating sentiment volatility: {e}")
            return 0.0

    def _calculate_trend_strength(self, token_address: str) -> float:
        """Calculate trend strength indicator."""
        try:
            prices = [p['price'] for p in self.price_history[token_address]]
            if len(prices) < self.min_data_points:
                return 0.0

            # Calculate price changes
            changes = np.diff(prices)
            
            # Calculate directional consistency
            positive_changes = np.sum(changes > 0)
            negative_changes = np.sum(changes < 0)
            total_changes = len(changes)
            
            if total_changes == 0:
                return 0.0
            
            # Calculate trend consistency
            consistency = max(positive_changes, negative_changes) / total_changes
            
            # Calculate trend magnitude
            magnitude = abs(prices[-1] - prices[0]) / prices[0]
            
            # Combine metrics
            trend_strength = (consistency * 0.7 + magnitude * 0.3)
            
            return float(min(1.0, trend_strength))
            
        except Exception as e:
            logger.error(f"Error calculating trend strength: {e}")
            return 0.0

    def get_volatility_analysis(self, token_address: str) -> Dict:
        """Get comprehensive volatility analysis for a token."""
        try:
            if token_address not in self.volatility_history:
                return {"error": "No volatility data available"}

            recent_metrics = self.volatility_history[token_address][-100:]
            
            return {
                "current_metrics": recent_metrics[-1].__dict__,
                "volatility_trend": self._analyze_volatility_trend(recent_metrics),
                "risk_metrics": {
                    "current_risk": recent_metrics[-1].risk_metrics,
                    "risk_trend": self._analyze_risk_trend(recent_metrics)
                },
                "warning_signals": self._get_active_warnings(recent_metrics),
                "confidence_metrics": {
                    "data_quality": self._calculate_data_quality(token_address),
                    "metric_stability": self._calculate_metric_stability(recent_metrics)
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting volatility analysis: {e}")
            return {"error": str(e)}

    def _analyze_volatility_trend(
        self,
        metrics: List[VolatilityMetrics]
    ) -> Dict[str, float]:
        """Analyze trend in volatility metrics."""
        try:
            realized_vols = [m.realized_volatility for m in metrics]
            implied_vols = [m.implied_volatility for m in metrics]
            
            return {
                "realized_trend": np.polyfit(range(len(realized_vols)), realized_vols, 1)[0],
                "implied_trend": np.polyfit(range(len(implied_vols)), implied_vols, 1)[0],
                "volatility_acceleration": np.diff(realized_vols, 2).mean(),
                "trend_direction": "increasing" if realized_vols[-1] > realized_vols[0] else "decreasing"
            }
            
        except Exception as e:
            logger.error(f"Error analyzing volatility trend: {e}")
            return {}

    def _analyze_risk_trend(self, metrics: List[VolatilityMetrics]) -> Dict[str, float]:
        """Analyze trend in risk metrics."""
        try:
            combined_risks = [
                m.risk_metrics.get('combined_risk', 0)
                for m in metrics
            ]
            
            return {
                "risk_trend": np.polyfit(range(len(combined_risks)), combined_risks, 1)[0],
                "risk_acceleration": np.diff(combined_risks, 2).mean(),
                "max_risk": max(combined_risks),
                "trend_stability": 1 - np.std(combined_risks)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing risk trend: {e}")
            return {}

    def _get_active_warnings(self, metrics: List[VolatilityMetrics]) -> Dict[str, int]:
        """Get currently active warning signals and their frequencies."""
        try:
            warning_counts = defaultdict(int)
            recent_metrics = metrics[-10:]  # Look at last 10 data points
            
            for metric in recent_metrics:
                for warning in metric.warning_signals:
                    warning_counts[warning] += 1
            
            return dict(warning_counts)
            
        except Exception as e:
            logger.error(f"Error getting active warnings: {e}")
            return {}

    def _calculate_data_quality(self, token_address: str) -> float:
        """Calculate quality score for available data."""
        try:
            # Check data quantity
            data_points = len(self.price_history[token_address])
            quantity_score = min(1.0, data_points / self.min_data_points)
            
            # Check data consistency
            timestamps = [p['timestamp'] for p in self.price_history[token_address]]
            if len(timestamps) < 2:
                return quantity_score
                
            time_diffs = np.diff([t.timestamp() for t in timestamps])
            consistency_score = 1 - min(1.0, np.std(time_diffs) / np.mean(time_diffs))
            
            return float((quantity_score + consistency_score) / 2)
            
        except Exception as e:
            logger.error(f"Error calculating data quality: {e}")
            return 0.0

    def _calculate_metric_stability(
        self,
        metrics: List[VolatilityMetrics]
    ) -> float:
        """Calculate stability of volatility metrics."""
        try:
            if not metrics:
                return 0.0
                
            # Calculate stability for each metric
            realized_stability = 1 - np.std([m.realized_volatility for m in metrics])
            implied_stability = 1 - np.std([m.implied_volatility for m in metrics])
            risk_stability = 1 - np.std([
                m.risk_metrics.get('combined_risk', 0)
                for m in metrics
            ])
            
            return float((realized_stability + implied_stability + risk_stability) / 3)
            
        except Exception as e:
            logger.error(f"Error calculating metric stability: {e}")
            return 0.0

    def _generate_default_metrics(
        self,
        token_address: str,
        timestamp: datetime
    ) -> VolatilityMetrics:
        """Generate default metrics when calculation fails."""
        return VolatilityMetrics(
            token_address=token_address,
            timestamp=timestamp,
            realized_volatility=0.0,
            implied_volatility=0.0,
            historical_volatility=0.0,
            relative_volatility=0.0,
            volatility_indicators={},
            risk_metrics={'combined_risk': 0.0},
            confidence_score=0.0,
            warning_signals=["INSUFFICIENT_DATA"]
        )

    def _update_price_history(
        self,
        token_address: str,
        price: float,
        timestamp: datetime
    ) -> None:
        """Update price history for a token."""
        try:
            self.price_history[token_address].append({
                'price': price,
                'timestamp': timestamp
            })
        except Exception as e:
            logger.error(f"Error updating price history: {e}")

    def _update_metrics(self, metrics: VolatilityMetrics) -> None:
        """Update tracking metrics."""
        try:
            self.metrics['calculation_times'].append(datetime.now())
            self.metrics['confidence_scores'].append(metrics.confidence_score)
            
            if metrics.warning_signals:
                self.alerts[metrics.token_address].extend(metrics.warning_signals)
        except Exception as e:
            logger.error(f"Error updating metrics: {e}")

if __name__ == "__main__":
    # Example usage
    def main():
        # Initialize calculator
        calculator = VolatilityCalculator(
            window_sizes=[5, 15, 30, 60, 120],
            vol_threshold=0.5
        )
        
        # Example token data
        token_address = "ExampleToken123"
        current_price = 100.0
        current_time = datetime.now()
        
        # Example market data
        liquidity_data = {
            'total_liquidity': 500000,
            'depth': 50000,
            'history': [
                {'value': 480000, 'timestamp': current_time - timedelta(hours=1)},
                {'value': 500000, 'timestamp': current_time}
            ]
        }
        
        sentiment_data = {
            'history': [
                {'score': 0.6, 'timestamp': current_time - timedelta(hours=1)},
                {'score': 0.8, 'timestamp': current_time}
            ]
        }
        
        # Calculate volatility
        metrics = calculator.calculate_volatility(
            token_address=token_address,
            current_price=current_price,
            timestamp=current_time,
            volume=1000000,
            liquidity_data=liquidity_data,
            sentiment_data=sentiment_data
        )
        
        print(f"\nVolatility Metrics:")
        print(f"Realized Volatility: {metrics.realized_volatility:.4f}")
        print(f"Implied Volatility: {metrics.implied_volatility:.4f}")
        print(f"Risk Score: {metrics.risk_metrics.get('combined_risk', 0):.4f}")
        print(f"Warning Signals: {metrics.warning_signals}")
        
        # Get analysis
        analysis = calculator.get_volatility_analysis(token_address)
        print("\nVolatility Analysis:")
        print(json.dumps(analysis, indent=2))
        
    main()