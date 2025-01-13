"""Crypto Anomaly Detection Engine System (CADES)

Whale Detection Module

This module implements detection and analysis of large holder behavior,
including accumulation patterns and whale wallet profiling.

Author: CADES Team
License: Proprietary"""

from .whale_tracker import WhaleTracker
from .accumulation_analyzer import AccumulationAnalyzer
from .pattern_recognizer import PatternRecognizer

__version__ = '1.0.0'
__author__ = 'CADES Team'
__email__ = 'contact@cades.io'

__all__ = [
    'WhaleTracker',
    'AccumulationAnalyzer',
    'PatternRecognizer',
]

# Whale detection configuration
WHALE_THRESHOLDS = {
    'min_balance': 1_000_000,  # Minimum balance to be considered a whale
    'min_transaction': 100_000,  # Minimum transaction size to track
    'accumulation_window': 72,  # Hours to analyze for accumulation
    'distribution_window': 24,  # Hours to analyze for distribution
}

# Pattern recognition settings
PATTERN_CONFIG = {
    'min_confidence': 0.85,
    'timeframe_minutes': 60,
    'pattern_types': [
        'accumulation',
        'distribution',
        'wash_trading',
        'price_manipulation'
    ]
}
