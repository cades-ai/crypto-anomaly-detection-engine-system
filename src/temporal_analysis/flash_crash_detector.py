"""
Crypto Anomaly Detection Engine System (CADES)
Flash Crash Detector Module

This module implements advanced detection of flash crashes and sudden price movements
in memecoin markets, with real-time monitoring and early warning systems.

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
from scipy.stats import zscore
import warnings
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class FlashCrashAlert:
    """Flash crash detection alert"""
    token_address: str
    timestamp: datetime
    severity: str
    price_change: float
    time_frame: int  # seconds
    volume_surge: float
    liquidity_impact: float
    warning_signals: List[str]
    contributing_factors: Dict[str, float]
    recovery_metrics: Optional[Dict[str, float]] = None

@dataclass
class MarketCondition:
    """Current market condition metrics"""
    price: float
    volume: float
    liquidity: float
    volatility: float
    sentiment_score: float
    timestamp: datetime
    additional_metrics: Dict[str, float] = field(default_factory=dict)

class FlashCrashDetector:
    """
    Advanced flash crash detector for memecoin markets.
    Implements real-time monitoring and early warning system.
    """
    
    def __init__(
        self,
        time_windows: List[int] = [30, 60, 300],  # seconds
        price_thresholds: Dict[str, float] = {
            'critical': -0.3,   # 30% drop
            'severe': -0.2,     # 20% drop
            'warning': -0.1     # 10% drop
        },
        volume_threshold: float = 3.0,  # 3x normal volume
        update_interval: int = 5,       # 5 seconds
        min_data_points: int = 100
    ):
        """
        Initialize the flash crash detector.
        
        Args:
            time_windows: List of monitoring windows in seconds
            price_thresholds: Thresholds for different alert levels
            volume_threshold: Volume surge threshold multiplier
            update_interval: Update interval in seconds
            min_data_points: Minimum data points for analysis
        """
        self.time_windows = time_windows
        self.price_thresholds = price_thresholds
        self.volume_threshold = volume_threshold
        self.update_interval = update_interval
        self.min_data_points = min_data_points
        
        # Data structures
        self.market_conditions: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=10000)
        )
        self.alerts: Dict[str, List[FlashCrashAlert]] = defaultdict(list)
        self.recovery_tracking: Dict[str, Dict] = defaultdict(dict)
        
        # Statistical baselines
        self.price_baselines: Dict[str, Dict] = defaultdict(dict)
        self.volume_baselines: Dict[str, Dict] = defaultdict(dict)
        
        # Feature windows for pattern recognition
        self.pattern_windows: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=1000)
        )

    async def monitor_market(
        self,
        token_address: str,
        current_condition: MarketCondition
    ) -> Optional[FlashCrashAlert]:
        """
        Monitor market for flash crash conditions.
        
        Args:
            token_address: Token contract address
            current_condition: Current market condition
            
        Returns:
            Flash crash alert if detected
        """
        try:
            # Update market conditions
            self._update_market_conditions(token_address, current_condition)
            
            # Check for minimum data points
            if len(self.market_conditions[token_address]) < self.min_data_points:
                return None
            
            # Update baselines
            self._update_baselines(token_address)
            
            # Check for flash crash conditions
            alert = self._check_flash_crash_conditions(token_address)
            
            if alert:
                # Update recovery tracking
                self._update_recovery_tracking(token_address, alert)
                
                # Update alert history
                self.alerts[token_address].append(alert)
                
                return alert
            
            # Update recovery metrics if monitoring recovery
            if token_address in self.recovery_tracking:
                self._monitor_recovery(token_address, current_condition)
            
            return None
            
        except Exception as e:
            logger.error(f"Error monitoring market: {e}")
            return None

    def _check_flash_crash_conditions(
        self,
        token_address: str
    ) -> Optional[FlashCrashAlert]:
        """Check for flash crash conditions across time windows."""
        try:
            conditions = list(self.market_conditions[token_address])
            current_price = conditions[-1].price
            
            for window in self.time_windows:
                # Get window data
                window_data = self._get_window_data(conditions, window)
                if not window_data:
                    continue
                
                # Calculate price change
                start_price = window_data[0].price
                price_change = (current_price - start_price) / start_price
                
                # Check volume surge
                volume_surge = self._calculate_volume_surge(window_data)
                
                # Check liquidity impact
                liquidity_impact = self._calculate_liquidity_impact(window_data)
                
                # Check against thresholds
                severity = self._determine_severity(price_change)
                if severity:
                    # Generate warning signals
                    warnings = self._generate_warning_signals(
                        price_change,
                        volume_surge,
                        liquidity_impact,
                        window_data
                    )
                    
                    # Calculate contributing factors
                    factors = self._analyze_contributing_factors(
                        window_data,
                        price_change,
                        volume_surge
                    )
                    
                    return FlashCrashAlert(
                        token_address=token_address,
                        timestamp=datetime.now(),
                        severity=severity,
                        price_change=price_change,
                        time_frame=window,
                        volume_surge=volume_surge,
                        liquidity_impact=liquidity_impact,
                        warning_signals=warnings,
                        contributing_factors=factors
                    )
            
            return None
            
        except Exception as e:
            logger.error(f"Error checking flash crash conditions: {e}")
            return None

    def _determine_severity(self, price_change: float) -> Optional[str]:
        """Determine severity level of price change."""
        try:
            if price_change <= self.price_thresholds['critical']:
                return 'CRITICAL'
            elif price_change <= self.price_thresholds['severe']:
                return 'SEVERE'
            elif price_change <= self.price_thresholds['warning']:
                return 'WARNING'
            return None
            
        except Exception as e:
            logger.error(f"Error determining severity: {e}")
            return None

    def _calculate_volume_surge(
        self,
        window_data: List[MarketCondition]
    ) -> float:
        """Calculate volume surge multiple."""
        try:
            current_volume = window_data[-1].volume
            baseline_volume = np.mean([d.volume for d in window_data[:-1]])
            
            if baseline_volume == 0:
                return 0.0
                
            return current_volume / baseline_volume
            
        except Exception as e:
            logger.error(f"Error calculating volume surge: {e}")
            return 0.0

    def _calculate_liquidity_impact(
        self,
        window_data: List[MarketCondition]
    ) -> float:
        """Calculate liquidity impact of price movement."""
        try:
            start_liquidity = window_data[0].liquidity
            end_liquidity = window_data[-1].liquidity
            
            if start_liquidity == 0:
                return 0.0
                
            return (end_liquidity - start_liquidity) / start_liquidity
            
        except Exception as e:
            logger.error(f"Error calculating liquidity impact: {e}")
            return 0.0

    def _generate_warning_signals(
        self,
        price_change: float,
        volume_surge: float,
        liquidity_impact: float,
        window_data: List[MarketCondition]
    ) -> List[str]:
        """Generate warning signals based on market conditions."""
        try:
            warnings = []
            
            # Price-based warnings
            if price_change <= -0.5:
                warnings.append("EXTREME_PRICE_DROP")
            elif price_change <= -0.3:
                warnings.append("SEVERE_PRICE_DROP")
                
            # Volume-based warnings
            if volume_surge >= 5.0:
                warnings.append("EXTREME_VOLUME_SURGE")
            elif volume_surge >= 3.0:
                warnings.append("HIGH_VOLUME_SURGE")
                
            # Liquidity-based warnings
            if liquidity_impact <= -0.5:
                warnings.append("SEVERE_LIQUIDITY_LOSS")
            elif liquidity_impact <= -0.3:
                warnings.append("SIGNIFICANT_LIQUIDITY_LOSS")
                
            # Pattern-based warnings
            if self._detect_manipulation_pattern(window_data):
                warnings.append("POTENTIAL_MANIPULATION")
                
            # Sentiment-based warnings
            sentiment_signal = self._analyze_sentiment_signal(window_data)
            if sentiment_signal < -0.7:
                warnings.append("EXTREME_NEGATIVE_SENTIMENT")
            
            return warnings
            
        except Exception as e:
            logger.error(f"Error generating warning signals: {e}")
            return ["ERROR_GENERATING_WARNINGS"]

    def _analyze_contributing_factors(
        self,
        window_data: List[MarketCondition],
        price_change: float,
        volume_surge: float
    ) -> Dict[str, float]:
        """Analyze factors contributing to flash crash."""
        try:
            factors = {}
            
            # Price impact
            factors['price_impact'] = min(1.0, abs(price_change))
            
            # Volume impact
            factors['volume_impact'] = min(1.0, volume_surge / 5.0)
            
            # Liquidity factors
            liquidity_change = (
                window_data[-1].liquidity - window_data[0].liquidity
            ) / window_data[0].liquidity
            factors['liquidity_impact'] = min(1.0, abs(liquidity_change))
            
            # Volatility impact
            volatility_change = (
                window_data[-1].volatility - window_data[0].volatility
            ) / window_data[0].volatility
            factors['volatility_impact'] = min(1.0, abs(volatility_change))
            
            # Sentiment impact
            sentiment_scores = [d.sentiment_score for d in window_data]
            factors['sentiment_impact'] = min(1.0, abs(np.mean(sentiment_scores)))
            
            return factors
            
        except Exception as e:
            logger.error(f"Error analyzing contributing factors: {e}")
            return {}

    def _detect_manipulation_pattern(
        self,
        window_data: List[MarketCondition]
    ) -> bool:
        """Detect potential manipulation patterns."""
        try:
            # Get price and volume sequences
            prices = np.array([d.price for d in window_data])
            volumes = np.array([d.volume for d in window_data])
            
            # Check for pump and dump pattern
            price_changes = np.diff(prices) / prices[:-1]
            volume_changes = np.diff(volumes) / volumes[:-1]
            
            # Detect rapid price movement with volume spike
            if any(abs(price_changes) > 0.1) and any(volume_changes > 2.0):
                return True
            
            # Check for price manipulation pattern
            if self._check_wash_trading_pattern(prices, volumes):
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error detecting manipulation pattern: {e}")
            return False

    def _check_wash_trading_pattern(
        self,
        prices: np.ndarray,
        volumes: np.ndarray
    ) -> bool:
        """Check for wash trading pattern."""
        try:
            if len(prices) < 10:
                return False
            
            # Calculate price and volume correlations
            price_corr = np.corrcoef(prices[:-1], prices[1:])[0, 1]
            volume_corr = np.corrcoef(volumes[:-1], volumes[1:])[0, 1]
            
            # Check for oscillating pattern with high correlation
            if abs(price_corr) > 0.9 and abs(volume_corr) > 0.9:
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking wash trading pattern: {e}")
            return False

    def _analyze_sentiment_signal(
        self,
        window_data: List[MarketCondition]
    ) -> float:
        """Analyze sentiment signal in time window."""
        try:
            sentiment_scores = [d.sentiment_score for d in window_data]
            
            # Calculate sentiment trend
            sentiment_changes = np.diff(sentiment_scores)
            
            # Calculate weighted average of recent sentiment
            weights = np.linspace(0.5, 1.0, len(sentiment_scores))
            weighted_sentiment = np.average(sentiment_scores, weights=weights)
            
            # Combine trend and level
            sentiment_signal = (
                weighted_sentiment * 0.7 +
                np.mean(sentiment_changes) * 0.3
            )
            
            return float(sentiment_signal)
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment signal: {e}")
            return 0.0

    def _update_recovery_tracking(
        self,
        token_address: str,
        alert: FlashCrashAlert
    ) -> None:
        """Update recovery tracking after flash crash."""
        try:
            self.recovery_tracking[token_address] = {
                'alert': alert,
                'start_price': alert.price_change,
                'min_price': alert.price_change,
                'start_time': alert.timestamp,
                'recovery_threshold': alert.price_change * 0.5,  # 50% recovery
                'monitoring': True
            }
            
        except Exception as e:
            logger.error(f"Error updating recovery tracking: {e}")

    def _monitor_recovery(
        self,
        token_address: str,
        current_condition: MarketCondition
    ) -> None:
        """Monitor price recovery after flash crash."""
        try:
            recovery_data = self.recovery_tracking[token_address]
            if not recovery_data['monitoring']:
                return
            
            start_price = recovery_data['start_price']
            current_price = current_condition.price
            
            # Update minimum price if needed
            recovery_data['min_price'] = min(
                recovery_data['min_price'],
                current_price
            )
            
            # Calculate recovery percentage
            recovery_pct = (current_price - recovery_data['min_price']) / abs(recovery_data['min_price'])
            
            # Check if recovered
            if recovery_pct >= abs(recovery_data['recovery_threshold']):
                recovery_metrics = {
                    'recovery_time': (
                        current_condition.timestamp - recovery_data['start_time']
                    ).total_seconds(),
                    'recovery_percentage': float(recovery_pct),
                    'min_price': float(recovery_data['min_price']),
                    'final_price': float(current_price)
                }
                
                # Update alert with recovery metrics
                recovery_data['alert'].recovery_metrics = recovery_metrics
                
                # Stop monitoring
                recovery_data['monitoring'] = False
                
            # Check for timeout (24 hours)
            elif (current_condition.timestamp - recovery_data['start_time']).total_seconds() > 86400:
                recovery_data['monitoring'] = False
            
        except Exception as e:
            logger.error(f"Error monitoring recovery: {e}")

    def _update_market_conditions(
        self,
        token_address: str,
        condition: MarketCondition
    ) -> None:
        """Update market conditions history."""
        try:
            self.market_conditions[token_address].append(condition)
            
            # Update pattern windows
            self._update_pattern_windows(token_address, condition)
            
        except Exception as e:
            logger.error(f"Error updating market conditions: {e}")

    def _update_pattern_windows(
        self,
        token_address: str,
        condition: MarketCondition
    ) -> None:
        """Update pattern recognition windows."""
        try:
            self.pattern_windows[token_address].append({
                'price': condition.price,
                'volume': condition.volume,
                'liquidity': condition.liquidity,
                'timestamp': condition.timestamp
            })
            
        except Exception as e:
            logger.error(f"Error updating pattern windows: {e}")

    def _update_baselines(self, token_address: str) -> None:
        """Update statistical baselines."""
        try:
            conditions = list(self.market_conditions[token_address])
            
            # Update price baselines
            prices = [c.price for c in conditions]
            self.price_baselines[token_address] = {
                'mean': float(np.mean(prices)),
                'std': float(np.std(prices)),
                'median': float(np.median(prices))
            }
            
            # Update volume baselines
            volumes = [c.volume for c in conditions]
            self.volume_baselines[token_address] = {
                'mean': float(np.mean(volumes)),
                'std': float(np.std(volumes)),
                'median': float(np.median(volumes))
            }
            
        except Exception as e:
            logger.error(f"Error updating baselines: {e}")

    def _get_window_data(
        self,
        conditions: List[MarketCondition],
        window: int
    ) -> List[MarketCondition]:
        """Get market conditions for specific time window."""
        try:
            current_time = conditions[-1].timestamp
            window_start = current_time - timedelta(seconds=window)
            
            return [
                c for c in conditions
                if c.timestamp >= window_start
            ]
            
        except Exception as e:
            logger.error(f"Error getting window data: {e}")
            return []

    def get_flash_crash_analysis(self, token_address: str) -> Dict:
        """Get comprehensive flash crash analysis for a token."""
        try:
            if token_address not in self.alerts:
                return {"error": "No alert history available"}

            recent_alerts = self.alerts[token_address][-100:]
            
            return {
                "total_alerts": len(recent_alerts),
                "alert_severity": {
                    "critical": sum(1 for a in recent_alerts if a.severity == "CRITICAL"),
                    "severe": sum(1 for a in recent_alerts if a.severity == "SEVERE"),
                    "warning": sum(1 for a in recent_alerts if a.severity == "WARNING")
                },
                "average_impact": {
                    "price": np.mean([a.price_change for a in recent_alerts]),
                    "volume": np.mean([a.volume_surge for a in recent_alerts]),
                    "liquidity": np.mean([a.liquidity_impact for a in recent_alerts])
                },
                "recovery_stats": self._calculate_recovery_stats(recent_alerts),
                "pattern_analysis": self._analyze_crash_patterns(recent_alerts),
                "current_risk": self._assess_current_risk(token_address)
            }
            
        except Exception as e:
            logger.error(f"Error getting flash crash analysis: {e}")
            return {"error": str(e)}

    def _calculate_recovery_stats(
        self,
        alerts: List[FlashCrashAlert]
    ) -> Dict[str, float]:
        """Calculate recovery statistics from alerts."""
        try:
            recovered_alerts = [
                a for a in alerts
                if a.recovery_metrics is not None
            ]
            
            if not recovered_alerts:
                return {}
                
            recovery_times = [
                a.recovery_metrics['recovery_time']
                for a in recovered_alerts
            ]
            
            recovery_pcts = [
                a.recovery_metrics['recovery_percentage']
                for a in recovered_alerts
            ]
            
            return {
                "average_recovery_time": float(np.mean(recovery_times)),
                "average_recovery_percentage": float(np.mean(recovery_pcts)),
                "recovery_rate": len(recovered_alerts) / len(alerts)
            }
            
        except Exception as e:
            logger.error(f"Error calculating recovery stats: {e}")
            return {}

    def _analyze_crash_patterns(
        self,
        alerts: List[FlashCrashAlert]
    ) -> Dict[str, Union[int, float]]:
        """Analyze patterns in flash crashes."""
        try:
            patterns = {
                "manipulation_frequency": sum(
                    1 for a in alerts
                    if "POTENTIAL_MANIPULATION" in a.warning_signals
                ),
                "sentiment_driven": sum(
                    1 for a in alerts
                    if "EXTREME_NEGATIVE_SENTIMENT" in a.warning_signals
                ),
                "liquidity_driven": sum(
                    1 for a in alerts
                    if "SEVERE_LIQUIDITY_LOSS" in a.warning_signals
                )
            }
            
            # Calculate time-based patterns
            timestamps = [a.timestamp for a in alerts]
            if len(timestamps) > 1:
                time_diffs = np.diff([t.timestamp() for t in timestamps])
                patterns["average_time_between_crashes"] = float(np.mean(time_diffs))
                patterns["crash_frequency_trend"] = float(np.polyfit(
                    range(len(time_diffs)),
                    time_diffs,
                    1
                )[0])
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error analyzing crash patterns: {e}")
            return {}

    def _assess_current_risk(self, token_address: str) -> Dict[str, float]:
        """Assess current flash crash risk."""
        try:
            if len(self.market_conditions[token_address]) < self.min_data_points:
                return {"risk_level": 0.0}
            
            conditions = list(self.market_conditions[token_address])
            current = conditions[-1]
            
            # Calculate volatility risk
            price_volatility = np.std([c.price for c in conditions[-20:]])
            vol_risk = min(1.0, price_volatility / current.price)
            
            # Calculate volume risk
            volume_mean = np.mean([c.volume for c in conditions[-20:]])
            volume_risk = min(1.0, current.volume / volume_mean) if volume_mean > 0 else 0.0
            
            # Calculate liquidity risk
            liquidity_change = (
                current.liquidity - conditions[-20].liquidity
            ) / conditions[-20].liquidity
            liquidity_risk = min(1.0, abs(liquidity_change))
            
            # Calculate sentiment risk
            sentiment_risk = min(1.0, abs(current.sentiment_score))
            
            # Combine risks
            risk_level = np.mean([
                vol_risk * 0.4,
                volume_risk * 0.2,
                liquidity_risk * 0.2,
                sentiment_risk * 0.2
            ])
            
            return {
                "risk_level": float(risk_level),
                "volatility_risk": float(vol_risk),
                "volume_risk": float(volume_risk),
                "liquidity_risk": float(liquidity_risk),
                "sentiment_risk": float(sentiment_risk)
            }
            
        except Exception as e:
            logger.error(f"Error assessing current risk: {e}")
            return {"risk_level": 0.0}

if __name__ == "__main__":
    # Example usage
    async def main():
        # Initialize detector
        detector = FlashCrashDetector(
            time_windows=[30, 60, 300],
            price_thresholds={
                'critical': -0.3,
                'severe': -0.2,
                'warning': -0.1
            }
        )
        
        # Example market condition
        condition = MarketCondition(
            price=100.0,
            volume=1000000.0,
            liquidity=500000.0,
            volatility=0.2,
            sentiment_score=-0.5,
            timestamp=datetime.now(),
            additional_metrics={
                'buy_pressure': 0.7,
                'sell_pressure': 0.3
            }
        )
        
        # Monitor market
        alert = await detector.monitor_market(
            "ExampleToken123",
            condition
        )
        
        if alert:
            print("\nFlash Crash Alert:")
            print(f"Severity: {alert.severity}")
            print(f"Price Change: {alert.price_change:.2%}")
            print(f"Volume Surge: {alert.volume_surge:.2f}x")
            print(f"Warning Signals: {alert.warning_signals}")
        
        # Get analysis
        analysis = detector.get_flash_crash_analysis("ExampleToken123")
        print("\nFlash Crash Analysis:")
        print(json.dumps(analysis, indent=2))
        
    import asyncio
    asyncio.run(main())