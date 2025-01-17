"""
Crypto Anomaly Detection Engine System (CADES)
Momentum Tracker Module

This module implements advanced momentum tracking for Solana tokens,
analyzing price action, volume, and market dynamics to identify
strong directional movements and potential trend reversals.

Author: CADES Team
License: Proprietary
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from collections import defaultdict, deque

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class MomentumSignal:
    """Momentum signal detection result"""
    token_address: str
    timestamp: datetime
    signal_type: str  # 'bullish', 'bearish', 'neutral'
    strength: float  # 0-1 scale
    confidence: float
    supporting_metrics: Dict[str, float]
    timeframe: str  # '5m', '15m', '1h', etc.
    warning_signals: List[str] = field(default_factory=list)

class MomentumTracker:
    """
    Advanced momentum tracking system for Solana tokens.
    Implements multiple technical indicators and market dynamics analysis.
    """
    
    def __init__(
        self,
        timeframes: List[str] = ['5m', '15m', '1h', '4h', '1d'],
        rsi_periods: int = 14,
        macd_params: Tuple[int, int, int] = (12, 26, 9),
        volume_ma_periods: int = 20,
        update_interval: int = 60  # seconds
    ):
        """
        Initialize the momentum tracker.
        
        Args:
            timeframes: List of timeframes to analyze
            rsi_periods: Periods for RSI calculation
            macd_params: (fast, slow, signal) periods for MACD
            volume_ma_periods: Periods for volume moving average
            update_interval: Update interval in seconds
        """
        self.timeframes = timeframes
        self.rsi_periods = rsi_periods
        self.macd_fast, self.macd_slow, self.macd_signal = macd_params
        self.volume_ma_periods = volume_ma_periods
        self.update_interval = update_interval
        
        # Data structures
        self.price_history: Dict[str, Dict[str, deque]] = defaultdict(
            lambda: {tf: deque(maxlen=500) for tf in timeframes}
        )
        self.momentum_signals: Dict[str, List[MomentumSignal]] = defaultdict(list)
        
        # Technical indicator history
        self.indicator_history: Dict[str, Dict] = defaultdict(
            lambda: {
                'rsi': defaultdict(list),
                'macd': defaultdict(list),
                'volume_trend': defaultdict(list)
            }
        )
        
        # Baseline statistics
        self.baselines: Dict[str, Dict] = defaultdict(dict)
        
    async def update_momentum(
        self,
        token_address: str,
        current_price: float,
        current_volume: float,
        timestamp: datetime
    ) -> Optional[Dict[str, MomentumSignal]]:
        """
        Update momentum analysis with new price data.
        
        Args:
            token_address: Token address to analyze
            current_price: Current token price
            current_volume: Current trading volume
            timestamp: Current timestamp
            
        Returns:
            Dict of momentum signals per timeframe if significant changes detected
        """
        try:
            # Update price history
            self._update_price_history(
                token_address,
                current_price,
                current_volume,
                timestamp
            )
            
            signals = {}
            for timeframe in self.timeframes:
                # Calculate technical indicators
                indicators = self._calculate_indicators(
                    token_address,
                    timeframe
                )
                
                # Analyze momentum
                signal = self._analyze_momentum(
                    token_address,
                    timeframe,
                    indicators
                )
                
                if signal:
                    signals[timeframe] = signal
                    self.momentum_signals[token_address].append(signal)
            
            # Clean up old signals
            self._cleanup_old_signals(token_address)
            
            return signals if signals else None
            
        except Exception as e:
            logger.error(f"Error updating momentum: {e}")
            return None

    def _calculate_indicators(
        self,
        token_address: str,
        timeframe: str
    ) -> Dict:
        """Calculate technical indicators for momentum analysis."""
        try:
            price_data = list(self.price_history[token_address][timeframe])
            if len(price_data) < self.macd_slow:
                return {}
            
            # Calculate RSI
            prices = [p['price'] for p in price_data]
            rsi = self._calculate_rsi(prices)
            
            # Calculate MACD
            macd, signal, hist = self._calculate_macd(prices)
            
            # Calculate volume trend
            volumes = [p['volume'] for p in price_data]
            volume_trend = self._calculate_volume_trend(volumes)
            
            # Store indicator values
            self.indicator_history[token_address]['rsi'][timeframe].append(rsi)
            self.indicator_history[token_address]['macd'][timeframe].append(
                (macd[-1], signal[-1], hist[-1])
            )
            self.indicator_history[token_address]['volume_trend'][timeframe].append(
                volume_trend
            )
            
            return {
                'rsi': rsi,
                'macd': (macd[-1], signal[-1], hist[-1]),
                'volume_trend': volume_trend,
                'price_trend': self._calculate_price_trend(prices)
            }
            
        except Exception as e:
            logger.error(f"Error calculating indicators: {e}")
            return {}

    def _analyze_momentum(
        self,
        token_address: str,
        timeframe: str,
        indicators: Dict
    ) -> Optional[MomentumSignal]:
        """Analyze momentum using technical indicators and market dynamics."""
        try:
            if not indicators:
                return None
                
            # Extract indicator values
            rsi = indicators['rsi']
            macd, signal, hist = indicators['macd']
            volume_trend = indicators['volume_trend']
            price_trend = indicators['price_trend']
            
            # Calculate momentum strength and direction
            strength, direction = self._calculate_momentum_strength(
                rsi,
                macd,
                signal,
                hist,
                volume_trend,
                price_trend
            )
            
            # Calculate confidence score
            confidence = self._calculate_confidence(
                indicators,
                strength
            )
            
            # Generate warning signals
            warnings = self._generate_warning_signals(
                indicators,
                strength,
                direction
            )
            
            # Create momentum signal if significant
            if strength > 0.3 and confidence > 0.6:
                return MomentumSignal(
                    token_address=token_address,
                    timestamp=datetime.now(),
                    signal_type=direction,
                    strength=strength,
                    confidence=confidence,
                    supporting_metrics=indicators,
                    timeframe=timeframe,
                    warning_signals=warnings
                )
                
            return None
            
        except Exception as e:
            logger.error(f"Error analyzing momentum: {e}")
            return None

    def _calculate_rsi(self, prices: List[float]) -> float:
        """Calculate Relative Strength Index."""
        try:
            if len(prices) < self.rsi_periods + 1:
                return 50.0
                
            # Calculate price changes
            changes = np.diff(prices)
            
            # Separate gains and losses
            gains = np.maximum(changes, 0)
            losses = np.absolute(np.minimum(changes, 0))
            
            # Calculate average gains and losses
            avg_gain = np.mean(gains[-self.rsi_periods:])
            avg_loss = np.mean(losses[-self.rsi_periods:])
            
            if avg_loss == 0:
                return 100.0
                
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            
            return float(rsi)
            
        except Exception as e:
            logger.error(f"Error calculating RSI: {e}")
            return 50.0

    def _calculate_macd(
        self,
        prices: List[float]
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Calculate MACD, Signal line, and Histogram."""
        try:
            prices_array = np.array(prices)
            
            # Calculate EMAs
            ema_fast = self._calculate_ema(prices_array, self.macd_fast)
            ema_slow = self._calculate_ema(prices_array, self.macd_slow)
            
            # Calculate MACD line
            macd_line = ema_fast - ema_slow
            
            # Calculate Signal line
            signal_line = self._calculate_ema(macd_line, self.macd_signal)
            
            # Calculate Histogram
            histogram = macd_line - signal_line
            
            return macd_line, signal_line, histogram
            
        except Exception as e:
            logger.error(f"Error calculating MACD: {e}")
            return np.zeros(3), np.zeros(3), np.zeros(3)

    def _calculate_volume_trend(self, volumes: List[float]) -> float:
        """Calculate volume trend strength."""
        try:
            if len(volumes) < self.volume_ma_periods:
                return 0.0
                
            # Calculate volume moving average
            volume_ma = np.mean(volumes[-self.volume_ma_periods:])
            
            # Calculate recent volume average
            recent_volume = np.mean(volumes[-5:])
            
            # Calculate trend strength
            if volume_ma == 0:
                return 0.0
                
            trend_strength = (recent_volume - volume_ma) / volume_ma
            
            return float(np.clip(trend_strength, -1, 1))
            
        except Exception as e:
            logger.error(f"Error calculating volume trend: {e}")
            return 0.0

    def _calculate_momentum_strength(
        self,
        rsi: float,
        macd: float,
        signal: float,
        hist: float,
        volume_trend: float,
        price_trend: float
    ) -> Tuple[float, str]:
        """Calculate overall momentum strength and direction."""
        try:
            # RSI momentum
            rsi_momentum = (rsi - 50) / 50  # -1 to 1 scale
            
            # MACD momentum
            macd_momentum = np.sign(hist) * min(1.0, abs(hist / signal)) if signal != 0 else 0
            
            # Combine indicators with weights
            strength = abs(
                rsi_momentum * 0.3 +
                macd_momentum * 0.3 +
                volume_trend * 0.2 +
                price_trend * 0.2
            )
            
            # Determine direction
            weighted_direction = (
                rsi_momentum * 0.3 +
                macd_momentum * 0.3 +
                volume_trend * 0.2 +
                price_trend * 0.2
            )
            
            if weighted_direction > 0:
                direction = 'bullish'
            elif weighted_direction < 0:
                direction = 'bearish'
            else:
                direction = 'neutral'
            
            return float(strength), direction
            
        except Exception as e:
            logger.error(f"Error calculating momentum strength: {e}")
            return 0.0, 'neutral'

    @staticmethod
    def _calculate_ema(data: np.ndarray, periods: int) -> np.ndarray:
        """Calculate Exponential Moving Average."""
        if len(data) < periods:
            return np.zeros_like(data)
            
        alpha = 2 / (periods + 1)
        return pd.Series(data).ewm(alpha=alpha, adjust=False).mean().values

    def _calculate_price_trend(self, prices: List[float]) -> float:
        """Calculate price trend strength."""
        try:
            if len(prices) < 2:
                return 0.0
                
            # Calculate log returns
            returns = np.diff(np.log(prices))
            
            # Calculate trend strength using linear regression
            x = np.arange(len(returns))
            slope, _ = np.polyfit(x, returns, 1)
            
            # Normalize trend strength
            trend_strength = np.tanh(slope * 100)
            
            return float(trend_strength)
            
        except Exception as e:
            logger.error(f"Error calculating price trend: {e}")
            return 0.0

    def _calculate_confidence(
        self,
        indicators: Dict,
        momentum_strength: float
    ) -> float:
        """Calculate confidence score for momentum signal."""
        try:
            confidence_factors = []
            
            # Indicator agreement
            rsi = indicators['rsi']
            _, signal, hist = indicators['macd']
            volume_trend = indicators['volume_trend']
            
            # RSI confidence
            rsi_confidence = 1.0 - (abs(rsi - 50) / 50)
            confidence_factors.append(rsi_confidence)
            
            # MACD confidence
            macd_confidence = min(1.0, abs(hist / signal)) if signal != 0 else 0
            confidence_factors.append(macd_confidence)
            
            # Volume confidence
            volume_confidence = abs(volume_trend)
            confidence_factors.append(volume_confidence)
            
            # Momentum strength impact
            confidence_factors.append(momentum_strength)
            
            # Calculate final confidence
            return float(np.mean(confidence_factors))
            
        except Exception as e:
            logger.error(f"Error calculating confidence: {e}")
            return 0.0

    def _generate_warning_signals(
        self,
        indicators: Dict,
        strength: float,
        direction: str
    ) -> List[str]:
        """Generate warning signals based on momentum analysis."""
        warnings = []
        try:
            rsi = indicators['rsi']
            _, _, hist = indicators['macd']
            volume_trend = indicators['volume_trend']
            
            # Overbought/Oversold warnings
            if rsi > 70:
                warnings.append("OVERBOUGHT_CONDITIONS")
            elif rsi < 30:
                warnings.append("OVERSOLD_CONDITIONS")
            
            # Momentum warnings
            if strength > 0.8:
                warnings.append(f"STRONG_{direction.upper()}_MOMENTUM")
            
            # Volume warnings
            if abs(volume_trend) > 0.8:
                warnings.append("UNUSUAL_VOLUME_ACTIVITY")
            
            # MACD warnings
            if abs(hist) > 0.5:
                warnings.append("STRONG_MOMENTUM_DIVERGENCE")
            
            return warnings
            
        except Exception as e:
            logger.error(f"Error generating warning signals: {e}")
            return []

    def _update_price_history(
        self,
        token_address: str,
        price: float,
        volume: float,
        timestamp: datetime
    ) -> None:
        """Update price history for all timeframes."""
        try:
            # Add data point to all timeframes
            for timeframe in self.timeframes:
                self.price_history[token_address][timeframe].append({
                    'price': price,
                    'volume': volume,
                    'timestamp': timestamp
                })
                
        except Exception as e:
            logger.error(f"Error updating price history: {e}")

    def _cleanup_old_signals(self, token_address: str) -> None:
        """Clean up old momentum signals."""
        try:
            # Keep only last 1000 signals
            if len(self.momentum_signals[token_address]) > 1000:
                self.momentum_signals[token_address] = \
                    self.momentum_signals[token_address][-1000:]
                    
        except Exception as e:
            logger.error(f"Error cleaning up signals: {e}")

    def get_momentum_analysis(self, token_address: str) -> Dict:
        """Get comprehensive momentum analysis for a token."""
        try:
            if token_address not in self.momentum_signals:
                return {"error": "No momentum data available"}

            recent_signals = self.momentum_signals[token_address][-100:]
            
            return {
                "current_signals": {
                    tf: self._get_latest_signal(token_address, tf)
                    for tf in self.timeframes
                },
                "momentum_trends": self._analyze_momentum_trends(recent_signals),
                "indicator_trends": self._analyze_indicator_trends(token_address),
                "warning_signals": self._get_active_warnings(recent_signals)
            }
            
        except Exception as e:
            logger.error(f"Error getting momentum analysis: {e}")
            return {"error": str(e)}

    def _get_latest_signal(
        self,
        token_address: str,
        timeframe: str
    ) -> Optional[Dict]:
        """Get latest momentum signal for a specific timeframe."""
        try:
            signals = [
                signal for signal in self.momentum_signals[token_address]
                if signal.timeframe == timeframe
            ]
            
            if not signals:
                return None
                
            latest = signals[-1]
            return {
                "signal_type": latest.signal_type,
                "strength": latest.strength,
                "confidence": latest.confidence,
                "timestamp": latest.timestamp.isoformat(),
                "warnings": latest.warning_signals
            }
            
        except Exception as e:
            logger.error(f"Error getting latest signal: {e}")
            return None

    def _analyze_momentum_trends(
        self,
        signals: List[MomentumSignal]
    ) -> Dict:
        """Analyze trends in momentum signals."""
        try:
            if not signals:
                return {}
                
            strengths = [s.strength for s in signals]
            confidences = [s.confidence for s in signals]
            
            # Analyze strength trend
            strength_trend = np.polyfit(
                range(len(strengths)),
                strengths,
                1
            )[0]
            
            # Analyze stability
            strength_stability = 1 - np.std(strengths)
            
            return {
                "strength_trend": float(strength_trend),
                "strength_stability": float(strength_stability),
                "average_confidence": float(np.mean(confidences)),
                "trend_direction": "increasing" if strength_trend > 0 else "decreasing",
                "trend_strength": float(abs(strength_trend))
            }
            
        except Exception as e:
            logger.error(f"Error analyzing momentum trends: {e}")
            return {}

    def _analyze_indicator_trends(self, token_address: str) -> Dict:
        """Analyze trends in technical indicators."""
        try:
            trends = {}
            
            for timeframe in self.timeframes:
                rsi_values = self.indicator_history[token_address]['rsi'][timeframe]
                macd_values = self.indicator_history[token_address]['macd'][timeframe]
                
                if rsi_values and macd_values:
                    trends[timeframe] = {
                        "rsi_trend": float(np.polyfit(
                            range(len(rsi_values)),
                            rsi_values,
                            1
                        )[0]),
                        "macd_trend": float(np.polyfit(
                            range(len(macd_values)),
                            [m[0] for m in macd_values],
                            1
                        )[0])
                    }
            
            return trends
            
        except Exception as e:
            logger.error(f"Error analyzing indicator trends: {e}")
            return {}

    def _get_active_warnings(self, signals: List[MomentumSignal]) -> Dict[str, int]:
        """Get currently active warning signals and their frequencies."""
        try:
            warning_counts = defaultdict(int)
            recent_signals = signals[-10:]  # Look at last 10 signals
            
            for signal in recent_signals:
                for warning in signal.warning_signals:
                    warning_counts[warning] += 1
            
            return dict(warning_counts)
            
        except Exception as e:
            logger.error(f"Error getting active warnings: {e}")
            return {}

if __name__ == "__main__":
    # Example usage
    async def main():
        # Initialize tracker
        tracker = MomentumTracker(
            timeframes=['5m', '15m', '1h', '4h', '1d'],
            rsi_periods=14,
            macd_params=(12, 26, 9),
            volume_ma_periods=20
        )
        
        # Example data point
        token_address = "ExampleToken123"
        current_price = 100.0
        current_volume = 50000.0
        current_time = datetime.now()
        
        # Update momentum
        signals = await tracker.update_momentum(
            token_address,
            current_price,
            current_volume,
            current_time
        )
        
        if signals:
            for timeframe, signal in signals.items():
                print(f"\nMomentum Signal ({timeframe}):")
                print(f"Type: {signal.signal_type}")
                print(f"Strength: {signal.strength:.2f}")
                print(f"Confidence: {signal.confidence:.2f}")
                print(f"Warnings: {signal.warning_signals}")
        
        # Get analysis
        analysis = tracker.get_momentum_analysis(token_address)
        print("\nMomentum Analysis:")
        print(json.dumps(analysis, indent=2))
        
    import asyncio
    asyncio.run(main())