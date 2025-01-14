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
from src.score_aggregator.index_generator import IndexGenerator

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

class TestIndexGenerator(unittest.TestCase):
    def setUp(self):
        self.generator = IndexGenerator(
            smoothing_window='6h',
            update_frequency='5min'
        )
        self.historical_data = pd.DataFrame({
            'timestamp': pd.date_range(start='2024-01-01', periods=1000, freq='5min'),
            'composite_risk': np.random.random(1000),
            'trading_volume': np.random.random(1000) * 1000000,
            'price_changes': np.random.random(1000) * 0.1 - 0.05
        })

    def test_generate_risk_index(self):
        risk_index = self.generator.generate_risk_index(self.historical_data)
        self.assertIsInstance(risk_index, pd.Series)
        self.assertEqual(len(risk_index), len(self.historical_data))
        self.assertTrue(risk_index.between(0, 1).all())

    def test_calculate_trend_strength(self):
        trend = self.generator.calculate_trend_strength(
            self.historical_data,
            window='1h'
        )
        self.assertIsInstance(trend, dict)
        self.assertIn('trend_direction', trend)
        self.assertIn('strength_score', trend)
        self.assertIn('momentum_indicators', trend)

    def test_detect_index_anomalies(self):
        anomalies = self.generator.detect_index_anomalies(
            self.historical_data['composite_risk']
        )
        self.assertIsInstance(anomalies, list)
        for anomaly in anomalies:
            self.assertIn('timestamp', anomaly)
            self.assertIn('severity', anomaly)
            self.assertIn('contributing_factors', anomaly)

    def test_validate_index_integrity(self):
        integrity = self.generator.validate_index_integrity(
            self.historical_data['composite_risk'],
            check_window='24h'
        )
        self.assertIsInstance(integrity, dict)
        self.assertIn('is_valid', integrity)
        self.assertIn('data_quality_score', integrity)
        self.assertIn('anomaly_count', integrity)

if __name__ == '__main__':
    unittest.main()