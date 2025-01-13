"""Crypto Anomaly Detection Engine System (CADES)

Score Aggregator Module

This module implements the final risk scoring and index generation system,
combining signals from all other modules into actionable metrics.

Author: CADES Team
License: Proprietary"""

from .metric_calculator import MetricCalculator
from .risk_scorer import RiskScorer
from .index_generator import IndexGenerator

__version__ = '1.0.0'
__author__ = 'CADES Team'
__email__ = 'contact@cades.io'

__all__ = [
    'MetricCalculator',
    'RiskScorer',
    'IndexGenerator',
]

# Scoring weights configuration
WEIGHT_CONFIG = {
    'chain_analysis': 0.30,
    'sentiment': 0.25,
    'temporal': 0.25,
    'whale': 0.20,
}

# Risk thresholds
RISK_LEVELS = {
    'low': 0.25,
    'medium': 0.50,
    'high': 0.75,
    'critical': 0.90
}

# Index calculation settings
INDEX_CONFIG = {
    'update_interval': 300,  # 5 minutes
    'smoothing_factor': 0.1,
    'history_length': 1440  # 24 hours of 1-minute data points
}
