""" Crypto Anomaly Detection Engine (CADE)

Score Aggregator Test Suite

This module implements testing for the final scoring system that combines
on-chain, sentiment, temporal, and whale signals into comprehensive risk metrics.

Author: CADE
Team License: Proprietary """

import unittest
from unittest.mock import Mock, patch
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.score_aggregator.metric_calculator import MetricCalculator
from src.score_aggregator.risk_scorer import RiskScorer


class TestMetricCalculator(unittest.TestCase):
    def setUp(self):
        self.calculator = MetricCalculator(
            weights={
                'chain_signals': 0.3,
                'sentiment_signals': 0.2,
                'temporal_signals': 0.25,
                'whale_signals': 0.25
            }
        )
        self.sample_data = {
            'chain_signals': {
                'wash_trading_score': 0.7,
                'liquidity_risk': 0.5,
                'transaction_anomaly': 0.3
            },
            'sentiment_signals': {
                'overall_sentiment': 0.8,
                'manipulation_score': 0.4,
                'trend_strength': 0.6
            },
            'temporal_signals': {
                'volatility_score': 0.5,
                'flash_crash_probability': 0.2,
                'price_momentum': 0.7
            },
            'whale_signals': {
                'accumulation_score': 0.6,
                'distribution_score': 0.3,
                'coordination_level': 0.4
            }
        }

    def test_calculate_composite_metrics(self):
        metrics = self.calculator.calculate_composite_metrics(self.sample_data)
        self.assertIsInstance(metrics, dict)
        self.assertIn('composite_risk_score', metrics)
        self.assertIn('signal_breakdown', metrics)
        self.assertTrue(0 <= metrics['composite_risk_score'] <= 1)

    def test_normalize_signals(self):
        normalized = self.calculator.normalize_signals(self.sample_data)
        for category in normalized.values():
            for score in category.values():
                self.assertTrue(0 <= score <= 1)

    def test_detect_signal_conflicts(self):
        conflicts = self.calculator.detect_signal_conflicts(self.sample_data)
        self.assertIsInstance(conflicts, list)
        for conflict in conflicts:
            self.assertIn('signal_pair', conflict)
            self.assertIn('conflict_severity', conflict)
            self.assertIn('recommendation', conflict)

class TestRiskScorer(unittest.TestCase):
    def setUp(self):
        self.scorer = RiskScorer(
            risk_thresholds={
                'low': 0.3,
                'medium': 0.6,
                'high': 0.8
            }
        )
        self.test_metrics = {
            'composite_risk_score': 0.75,
            'signal_breakdown': {
                'chain_risk': 0.8,
                'sentiment_risk': 0.7,
                'temporal_risk': 0.6,
                'whale_risk': 0.9
            }
        }

    def test_calculate_risk_level(self):
        risk_assessment = self.scorer.calculate_risk_level(self.test_metrics)
        self.assertIn('risk_level', risk_assessment)
        self.assertIn('confidence_score', risk_assessment)
        self.assertIn('contributing_factors', risk_assessment)

    def test_generate_risk_breakdown(self):
        breakdown = self.scorer.generate_risk_breakdown(self.test_metrics)
        self.assertIsInstance(breakdown, dict)
        self.assertTrue(all(k in breakdown for k in [
            'primary_risk_factors',
            'secondary_risk_factors',
            'risk_trend'
        ]))

    def test_validate_risk_assessment(self):
        historical_assessments = [
            {'risk_level': 'medium', 'timestamp': datetime.now() - timedelta(hours=i)}
            for i in range(24)
        ]
        validation = self.scorer.validate_risk_assessment(
            self.test_metrics,
            historical_assessments
        )
        self.assertIn('is_valid', validation)
        self.assertIn('confidence_level', validation)
        self.assertIn('validation_metrics', validation)


if __name__ == '__main__':
    unittest.main()