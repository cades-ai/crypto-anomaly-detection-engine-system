""" Crypto Anomaly Detection Engine System (CADES)

Score Aggregator Test Suite

This module implements testing for the final scoring system that combines
on-chain, sentiment, temporal, and whale signals into comprehensive risk metrics.

Author: CADES
Team License: Proprietary """

import unittest
from unittest.mock import Mock, patch
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.score_aggregator.metric_calculator import MetricCalculator
from src.score_aggregator.risk_scorer import RiskScorer
from src.score_aggregator.index_generator import IndexGenerator, IndexComponent, IndexState


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
            max_components=10,
            rebalance_interval=3600,  # 1 hour
            risk_threshold=0.7
        )
        self.historical_data = pd.DataFrame({
            'timestamp': pd.date_range(start='2024-01-01', periods=1000, freq='5min'),
            'composite_risk': np.random.random(1000),
            'trading_volume': np.random.random(1000) * 1000000,
            'price_changes': np.random.random(1000) * 0.1 - 0.05
        })

    async def test_generate_index(self):
        # Sample data
        token_data = {
            "token1": {"price": 100, "volume": 50000},
            "token2": {"price": 200, "volume": 75000}
        }
        metrics = {
            "token1": {"liquidity": 500000, "volatility": 0.3},
            "token2": {"liquidity": 750000, "volatility": 0.2}
        }
        risk_scores = {
            "token1": 0.4,
            "token2": 0.3
        }

        index = await self.generator.generate_index(
            "TestIndex",
            token_data,
            metrics,
            risk_scores
        )
        
        self.assertIsInstance(index, IndexState)
        self.assertEqual(len(index.components), 2)
        self.assertTrue(0 <= index.total_value)

    def test_calculate_weights(self):
        components = ["token1", "token2", "token3"]
        weights = self.generator._calculate_weights(components)
        
        self.assertEqual(len(weights), len(components))
        self.assertAlmostEqual(sum(weights.values()), 1.0)
        self.assertTrue(all(0 <= w <= 1 for w in weights.values()))

    def test_select_components(self):
        token_data = {
            "token1": {"volume": 50000},
            "token2": {"volume": 75000},
            "token3": {"volume": 25000}
        }
        metrics = {
            "token1": {"liquidity": 500000, "volatility": 0.3},
            "token2": {"liquidity": 750000, "volatility": 0.2},
            "token3": {"liquidity": 250000, "volatility": 0.4}
        }
        risk_scores = {
            "token1": 0.4,
            "token2": 0.3,
            "token3": 0.8  # Above risk threshold
        }

        components = self.generator._select_components(token_data, metrics, risk_scores)
        
        self.assertIn("token1", components)
        self.assertIn("token2", components)
        self.assertNotIn("token3", components)  # Should be excluded due to high risk

    def test_calculate_inclusion_score(self):
        metrics = {
            "liquidity": 500000,
            "volatility": 0.3
        }
        token_data = {
            "volume": 50000
        }

        score = self.generator._calculate_inclusion_score(metrics, token_data)
        self.assertTrue(0 <= score <= 1)

    def test_needs_rebalancing(self):
        # Test new index
        self.assertTrue(self.generator._needs_rebalancing("new_index"))

        # Test recently rebalanced index
        self.generator.last_rebalance["test_index"] = datetime.now()
        self.assertFalse(self.generator._needs_rebalancing("test_index"))

        # Test index needing rebalance
        self.generator.last_rebalance["old_index"] = datetime.now() - timedelta(hours=2)
        self.assertTrue(self.generator._needs_rebalancing("old_index"))

    def test_calculate_performance(self):
        index_name = "test_index"
        current_value = 1000.0

        # Empty history
        perf_metrics = self.generator._calculate_performance(index_name, current_value)
        self.assertEqual(perf_metrics['current_value'], current_value)

        # With history
        self.generator.performance_history[index_name] = [
            {'value': 900, 'timestamp': datetime.now() - timedelta(hours=2)},
            {'value': 950, 'timestamp': datetime.now() - timedelta(hours=1)}
        ]
        
        perf_metrics = self.generator._calculate_performance(index_name, current_value)
        self.assertIn('returns_mean', perf_metrics)
        self.assertIn('returns_std', perf_metrics)
        self.assertIn('total_return', perf_metrics)

    def test_calculate_index_risk(self):
        components = [
            IndexComponent(
                token_address=f"token{i}",
                weight=0.25,
                risk_score=0.3 + (i * 0.1),
                metrics={},
                last_updated=datetime.now()
            )
            for i in range(4)
        ]

        risk_metrics = self.generator._calculate_index_risk(components)
        
        self.assertIn('total_risk', risk_metrics)
        self.assertIn('max_component_risk', risk_metrics)
        self.assertIn('risk_std', risk_metrics)
        self.assertTrue(all(0 <= v <= 1 for v in risk_metrics.values()))


if __name__ == '__main__':
    unittest.main()