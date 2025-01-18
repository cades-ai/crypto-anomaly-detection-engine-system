"""
Crypto Anomaly Detection Engine System (CADES)
Pump Detection Module

This module implements advanced detection of potential pump signals and coordinated
price manipulation attempts in token trading patterns.

Author: CADES Team
License: Proprietary
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple
import numpy as np
from collections import defaultdict, deque
import logging
from enum import Enum

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PumpSignalType(Enum):
    """Classification of pump signal types"""
    VOLUME_SPIKE = "volume_spike"
    PRICE_ACCELERATION = "price_acceleration"
    SOCIAL_COORDINATION = "social_coordination"
    WHALE_ACCUMULATION = "whale_accumulation"
    LIQUIDITY_MANIPULATION = "liquidity_manipulation"

@dataclass
class PumpSignal:
    """Detected pump signal data structure"""
    token_address: str
    signal_type: PumpSignalType
    timestamp: datetime
    confidence_score: float
    severity: float
    indicators: Dict[str, float]
    supporting_data: Dict[str, any]
    coordinated_addresses: Optional[Set[str]] = None
    warning_signals: List[str] = field(default_factory=list)

class PumpDetector:
    """
    Advanced pump pattern detector for token markets.
    Implements multi-factor analysis to identify potential pump setups.
    """
    
    def __init__(
        self,
        min_volume_threshold: float = 10000,  # Minimum USD volume
        analysis_window: int = 3600,  # 1 hour default
        confidence_threshold: float = 0.7,
        update_interval: int = 60  # 1 minute default
    ):
        """
        Initialize the pump detector.
        
        Args:
            min_volume_threshold: Minimum volume in USD to consider
            analysis_window: Time window for analysis in seconds
            confidence_threshold: Minimum confidence for signal reporting
            update_interval: Update interval in seconds
        """
        self.min_volume_threshold = min_volume_threshold
        self.analysis_window = analysis_window
        self.confidence_threshold = confidence_threshold
        self.update_interval = update_interval
        
        # Data structures
        self.price_history: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=1000)
        )
        self.volume_history: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=1000)
        )
        self.detected_signals: Dict[str, List[PumpSignal]] = defaultdict(list)
        self.active_warnings: Dict[str, Set[str]] = defaultdict(set)
        
        # Threshold configurations
        self.thresholds = {
            'volume_spike': 3.0,  # 3x normal volume
            'price_acceleration': 0.1,  # 10% acceleration
            'social_intensity': 2.0,  # 2x normal activity
            'whale_concentration': 0.7,  # 70% holder concentration
        }

    async def analyze_token(
        self,
        token_address: str,
        price_data: Dict,
        volume_data: Dict,
        social_data: Optional[Dict] = None,
        whale_data: Optional[Dict] = None
    ) -> Optional[PumpSignal]:
        """
        Analyze token data for pump signals.
        
        Args:
            token_address: Token address to analyze
            price_data: Price-related metrics
            volume_data: Volume-related metrics
            social_data: Optional social media metrics
            whale_data: Optional whale activity data
            
        Returns:
            PumpSignal if pump pattern detected, None otherwise
        """
        try:
            # Update historical data
            self._update_historical_data(
                token_address,
                price_data,
                volume_data
            )
            
            # Check for minimum activity
            if not self._meets_minimum_requirements(token_address):
                return None
            
            # Analyze individual components
            volume_signal = self._analyze_volume_pattern(token_address, volume_data)
            price_signal = self._analyze_price_pattern(token_address, price_data)
            social_signal = self._analyze_social_signals(token_address, social_data)
            whale_signal = self._analyze_whale_activity(token_address, whale_data)
            
            # Combine signals
            combined_signal = self._combine_signals(
                volume_signal,
                price_signal,
                social_signal,
                whale_signal
            )
            
            if combined_signal >= self.confidence_threshold:
                signal = self._generate_pump_signal(
                    token_address,
                    combined_signal,
                    {
                        'volume': volume_signal,
                        'price': price_signal,
                        'social': social_signal,
                        'whale': whale_signal
                    }
                )
                
                # Update detection history
                self.detected_signals[token_address].append(signal)
                return signal
                
            return None
            
        except Exception as e:
            logger.error(f"Error analyzing token {token_address}: {e}")
            return None

    def _analyze_volume_pattern(
        self,
        token_address: str,
        volume_data: Dict
    ) -> float:
        """Analyze volume patterns for pump signals."""
        try:
            if len(self.volume_history[token_address]) < 10:
                return 0.0
                
            # Calculate volume metrics
            recent_volume = np.mean([v['volume'] for v in volume_data['recent']])
            baseline_volume = np.mean([
                v['volume'] 
                for v in self.volume_history[token_address]
            ])
            
            if baseline_volume == 0:
                return 0.0
                
            volume_ratio = recent_volume / baseline_volume
            
            # Calculate additional factors
            buy_pressure = self._calculate_buy_pressure(volume_data)
            volume_concentration = self._calculate_volume_concentration(volume_data)
            
            # Combine metrics
            volume_signal = (
                min(1.0, volume_ratio / self.thresholds['volume_spike']) * 0.5 +
                buy_pressure * 0.3 +
                volume_concentration * 0.2
            )
            
            return volume_signal
            
        except Exception as e:
            logger.error(f"Error analyzing volume pattern: {e}")
            return 0.0

    def _analyze_price_pattern(
        self,
        token_address: str,
        price_data: Dict
    ) -> float:
        """Analyze price patterns for pump signals."""
        try:
            if len(self.price_history[token_address]) < 10:
                return 0.0
                
            # Calculate price metrics
            recent_prices = [p['price'] for p in price_data['recent']]
            price_changes = np.diff(recent_prices) / recent_prices[:-1]
            
            # Calculate acceleration
            acceleration = np.diff(price_changes)
            max_acceleration = max(acceleration) if len(acceleration) > 0 else 0
            
            # Calculate momentum
            momentum = self._calculate_price_momentum(recent_prices)
            
            # Calculate volatility
            volatility = np.std(price_changes)
            
            # Combine metrics
            price_signal = (
                min(1.0, max_acceleration / self.thresholds['price_acceleration']) * 0.4 +
                min(1.0, momentum) * 0.4 +
                min(1.0, volatility) * 0.2
            )
            
            return price_signal
            
        except Exception as e:
            logger.error(f"Error analyzing price pattern: {e}")
            return 0.0

    def _analyze_social_signals(
        self,
        token_address: str,
        social_data: Optional[Dict]
    ) -> float:
        """Analyze social media signals for pump indicators."""
        try:
            if not social_data:
                return 0.0
                
            # Calculate social metrics
            mention_intensity = social_data.get('mention_intensity', 0)
            sentiment_score = social_data.get('sentiment_score', 0)
            coordination_signals = social_data.get('coordination_signals', 0)
            
            # Normalize metrics
            normalized_intensity = min(
                1.0,
                mention_intensity / self.thresholds['social_intensity']
            )
            normalized_sentiment = (sentiment_score + 1) / 2  # Convert to 0-1 range
            
            # Combine metrics
            social_signal = (
                normalized_intensity * 0.4 +
                normalized_sentiment * 0.3 +
                coordination_signals * 0.3
            )
            
            return social_signal
            
        except Exception as e:
            logger.error(f"Error analyzing social signals: {e}")
            return 0.0

    def _analyze_whale_activity(
        self,
        token_address: str,
        whale_data: Optional[Dict]
    ) -> float:
        """Analyze whale activity for pump coordination."""
        try:
            if not whale_data:
                return 0.0
                
            # Calculate whale metrics
            holder_concentration = whale_data.get('holder_concentration', 0)
            accumulation_score = whale_data.get('accumulation_score', 0)
            coordination_score = whale_data.get('coordination_score', 0)
            
            # Normalize metrics
            normalized_concentration = min(
                1.0,
                holder_concentration / self.thresholds['whale_concentration']
            )
            
            # Combine metrics
            whale_signal = (
                normalized_concentration * 0.4 +
                accumulation_score * 0.3 +
                coordination_score * 0.3
            )
            
            return whale_signal
            
        except Exception as e:
            logger.error(f"Error analyzing whale activity: {e}")
            return 0.0

    def _combine_signals(
        self,
        volume_signal: float,
        price_signal: float,
        social_signal: float,
        whale_signal: float
    ) -> float:
        """Combine different signals into overall pump signal."""
        try:
            # Weight the signals
            weighted_signals = [
                (volume_signal, 0.3),
                (price_signal, 0.3),
                (social_signal, 0.2),
                (whale_signal, 0.2)
            ]
            
            # Calculate weighted sum
            combined_signal = sum(
                signal * weight
                for signal, weight in weighted_signals
            )
            
            return combined_signal
            
        except Exception as e:
            logger.error(f"Error combining signals: {e}")
            return 0.0

    def _generate_pump_signal(
        self,
        token_address: str,
        confidence_score: float,
        indicators: Dict[str, float]
    ) -> PumpSignal:
        """Generate pump signal with supporting data."""
        try:
            # Determine signal type
            signal_type = self._determine_signal_type(indicators)
            
            # Calculate severity
            severity = self._calculate_severity(indicators)
            
            # Generate warning signals
            warnings = self._generate_warning_signals(
                indicators,
                severity
            )
            
            return PumpSignal(
                token_address=token_address,
                signal_type=signal_type,
                timestamp=datetime.now(),
                confidence_score=confidence_score,
                severity=severity,
                indicators=indicators,
                supporting_data=self._gather_supporting_data(token_address),
                warning_signals=warnings
            )
            
        except Exception as e:
            logger.error(f"Error generating pump signal: {e}")
            raise

    def get_token_analysis(self, token_address: str) -> Dict:
        """Get comprehensive pump analysis for a token."""
        try:
            signals = self.detected_signals.get(token_address, [])
            if not signals:
                return {"status": "No signals detected"}
            
            recent_signals = [s for s in signals if 
                (datetime.now() - s.timestamp).total_seconds() < self.analysis_window]
            
            return {
                "recent_signals": len(recent_signals),
                "confidence_trend": self._calculate_confidence_trend(recent_signals),
                "severity_trend": self._calculate_severity_trend(recent_signals),
                "active_warnings": list(self.active_warnings[token_address]),
                "latest_signal": recent_signals[-1] if recent_signals else None
            }
            
        except Exception as e:
            logger.error(f"Error getting token analysis: {e}")
            return {"error": str(e)}

if __name__ == "__main__":
    # Example usage
    async def main():
        detector = PumpDetector(
            min_volume_threshold=10000,
            analysis_window=3600,
            confidence_threshold=0.7
        )
        
        # Example data
        token_address = "TokenXYZ"
        price_data = {
            "recent": [{"price": 100 + i} for i in range(10)]
        }
        volume_data = {
            "recent": [{"volume": 1000 * (1.1 ** i)} for i in range(10)]
        }
        
        signal = await detector.analyze_token(
            token_address,
            price_data,
            volume_data
        )
        
        if signal:
            print(f"Pump signal detected: {signal.signal_type}")
            print(f"Confidence: {signal.confidence_score:.2f}")
            print(f"Severity: {signal.severity:.2f}")
            
    asyncio.run(main())