"""Crypto Anomaly Detection Engine System (CADES)

Temporal Analysis Module

This module implements time series analysis and prediction capabilities,
including LSTM-based prediction and flash crash detection.

Author: CADES Team
License: Proprietary"""

from .lstm_predictor import LSTMPredictor
from .volatility_calculator import VolatilityCalculator
from .flash_crash_detector import FlashCrashDetector

__version__ = '1.0.0'
__author__ = 'CADES Team'
__email__ = 'contact@cades.io'

__all__ = [
    'LSTMPredictor',
    'VolatilityCalculator',
    'FlashCrashDetector',
]

# Model configuration
LSTM_CONFIG = {
    'sequence_length': 100,
    'hidden_layers': 3,
    'hidden_size': 128,
    'dropout': 0.2,
    'learning_rate': 0.001,
}

# Detection thresholds
FLASH_CRASH_THRESHOLDS = {
    'price_drop': 0.15,  # 15% drop
    'time_window': 300,  # 5 minutes
    'volume_spike': 2.5,  # 2.5x average volume
}
