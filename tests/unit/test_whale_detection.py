""" Crypto Anomaly Detection Engine System (CADES)

Whale Detection Test Suite

This module implements testing for whale activity monitoring components,
including wallet tracking, accumulation patterns, and coordinated movement detection.

Author: CADES
Team License: Proprietary """

import unittest
from unittest.mock import Mock, patch
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.whale_detection.whale_tracker import WhaleTracker
from src.whale_detection.accumulation_analyzer import AccumulationAnalyzer
from src.whale_detection.market_acceleration_analyzer import MarketAccelerationAnalyzer

class TestWhaleTracker(unittest.TestCase):
    def setUp(self):
        self.tracker = WhaleTracker(
            min_holding_threshold=1000000,  # $1M USD minimum for whale classification
            monitoring_period='7d'
        )
        self.sample_transactions = pd.DataFrame({
            'timestamp': pd.date_range(start='2024-01-01', periods=100, freq='H'),
            'wallet_address': ['0x' + ''.join([str(i)]*40) for i in range(100)],
            'amount': np.random.random(100) * 2000000,
            'token_price': np.random.random(100) * 10
        })

    def test_identify_whale_wallets(self):
        whale_wallets = self.tracker.identify_whale_wallets(self.sample_transactions)
        self.assertIsInstance(whale_wallets, list)
        self.assertTrue(all(isinstance(w, dict) for w in whale_wallets))
        for wallet in whale_wallets:
            self.assertGreaterEqual(
                wallet['total_holdings'],
                self.tracker.min_holding_threshold
            )

    def test_track_position_changes(self):
        wallet = '0x' + '0'*40
        position_changes = self.tracker.track_position_changes(
            wallet,
            self.sample_transactions
        )
        self.assertIn('net_position_change', position_changes)
        self.assertIn('transaction_frequency', position_changes)
        self.assertIn('average_transaction_size', position_changes)

    def test_detect_coordinated_movements(self):
        movements = self.tracker.detect_coordinated_movements(
            self.sample_transactions,
            time_window='1h'
        )
        self.assertIsInstance(movements, dict)
        self.assertIn('coordinated_wallets', movements)
        self.assertIn('confidence_score', movements)

class TestAccumulationAnalyzer(unittest.TestCase):
    def setUp(self):
        self.analyzer = AccumulationAnalyzer(
            accumulation_threshold=0.1,  # 10% increase in position
            stealth_detection_window='48h'
        )
        self.wallet_history = pd.DataFrame({
            'timestamp': pd.date_range(start='2024-01-01', periods=200, freq='30min'),
            'position_size': np.cumsum(np.random.random(200) * 1000),
            'transaction_count': np.random.randint(1, 10, 200),
            'average_size': np.random.random(200) * 5000
        })

    def test_detect_stealth_accumulation(self):
        patterns = self.analyzer.detect_stealth_accumulation(self.wallet_history)
        self.assertIsInstance(patterns, dict)
        self.assertIn('accumulation_detected', patterns)
        self.assertIn('pattern_strength', patterns)
        self.assertIn('time_period', patterns)

    def test_analyze_buying_patterns(self):
        patterns = self.analyzer.analyze_buying_patterns(
            self.wallet_history,
            time_window='24h'
        )
        self.assertTrue(all(k in patterns for k in [
            'frequent_small_buys',
            'gradual_accumulation',
            'timing_analysis'
        ]))

    def test_calculate_position_velocity(self):
        velocity = self.analyzer.calculate_position_velocity(self.wallet_history)
        self.assertIsInstance(velocity, pd.Series)
        self.assertEqual(len(velocity), len(self.wallet_history) - 1)
class TestMarketAccelerationAnalyzer(unittest.TestCase):
    def setUp(self):
        self.analyzer = MarketAccelerationAnalyzer(
            min_velocity_threshold=0.05,  # 5% minimum velocity
            analysis_window=3600,  # 1 hour analysis window
            update_interval=60     # 1 minute updates
        )
        
        # Create sample market data
        self.sample_data = pd.DataFrame({
            'timestamp': pd.date_range(start='2024-01-01', periods=100, freq='1min'),
            'price': np.random.random(100) * 100,
            'volume': np.random.random(100) * 1000000,
            'liquidity': np.random.random(100) * 500000,
            'velocity': np.random.random(100) * 0.2 - 0.1
        })

    def test_calculate_market_velocity(self):
        """Test market velocity calculation."""
        velocity = self.analyzer.calculate_market_velocity(self.sample_data)
        self.assertIsInstance(velocity, float)
        self.assertTrue(-1.0 <= velocity <= 1.0)

    def test_detect_acceleration_pattern(self):
        """Test acceleration pattern detection."""
        patterns = self.analyzer.detect_acceleration_pattern(
            self.sample_data,
            lookback_period='30min'
        )
        self.assertIsInstance(patterns, dict)
        self.assertIn('pattern_type', patterns)
        self.assertIn('confidence_score', patterns)
        self.assertIn('momentum_indicators', patterns)

    def test_analyze_volume_correlation(self):
        """Test volume-price correlation analysis."""
        correlation = self.analyzer.analyze_volume_correlation(
            self.sample_data['price'],
            self.sample_data['volume'],
            window='10min'
        )
        self.assertIsInstance(correlation, float)
        self.assertTrue(-1.0 <= correlation <= 1.0)

    def test_calculate_momentum_signals(self):
        """Test momentum signal generation."""
        signals = self.analyzer.calculate_momentum_signals(
            self.sample_data,
            threshold=0.1
        )
        self.assertIsInstance(signals, dict)
        self.assertIn('momentum_score', signals)
        self.assertIn('signal_strength', signals)
        self.assertIn('trend_direction', signals)

    def test_detect_velocity_breakout(self):
        """Test velocity breakout detection."""
        breakout = self.analyzer.detect_velocity_breakout(
            self.sample_data['velocity'],
            std_threshold=2.0
        )
        self.assertIsInstance(breakout, dict)
        self.assertIn('breakout_detected', breakout)
        self.assertIn('magnitude', breakout)
        self.assertIn('confidence', breakout)

    def test_validate_acceleration_signal(self):
        """Test acceleration signal validation."""
        signal = {
            'momentum_score': 0.8,
            'velocity': 0.15,
            'volume_correlation': 0.7
        }
        validation = self.analyzer.validate_acceleration_signal(signal)
        self.assertIsInstance(validation, dict)
        self.assertIn('is_valid', validation)
        self.assertIn('confidence_level', validation)
        self.assertIn('validation_metrics', validation)

    def test_calculate_market_impact(self):
        """Test market impact calculation."""
        impact = self.analyzer.calculate_market_impact(
            price_change=0.1,
            volume_surge=2.0,
            liquidity_change=-0.2
        )
        self.assertIsInstance(impact, float)
        self.assertTrue(0 <= impact <= 1)

    def test_analyze_acceleration_components(self):
        """Test acceleration component analysis."""
        components = self.analyzer.analyze_acceleration_components(self.sample_data)
        self.assertIsInstance(components, dict)
        self.assertTrue(all(k in components for k in [
            'price_acceleration',
            'volume_acceleration',
            'momentum_factor',
            'composite_score'
        ]))

    def test_detect_deceleration_patterns(self):
        """Test deceleration pattern detection."""
        patterns = self.analyzer.detect_deceleration_patterns(
            self.sample_data,
            window='15min'
        )
        self.assertIsInstance(patterns, list)
        for pattern in patterns:
            self.assertIn('pattern_type', pattern)
            self.assertIn('severity', pattern)
            self.assertIn('duration', pattern)

    def test_calculate_statistical_significance(self):
        """Test statistical significance calculation."""
        stats = self.analyzer.calculate_statistical_significance(
            self.sample_data['velocity'],
            null_hypothesis_mean=0.0
        )
        self.assertIsInstance(stats, dict)
        self.assertIn('p_value', stats)
        self.assertIn('t_statistic', stats)
        self.assertIn('is_significant', stats)

    def test_generate_acceleration_metrics(self):
        """Test acceleration metrics generation."""
        metrics = self.analyzer.generate_acceleration_metrics(
            velocity=0.15,
            momentum=0.8,
            volume_correlation=0.7,
            market_impact=0.5
        )
        self.assertIsInstance(metrics, dict)
        self.assertTrue(all(k in metrics for k in [
            'acceleration_score',
            'confidence_score',
            'risk_level',
            'signal_quality'
        ]))

    def test_validate_market_conditions(self):
        """Test market condition validation."""
        conditions = self.analyzer.validate_market_conditions(
            self.sample_data,
            min_liquidity=100000,
            min_volume=50000
        )
        self.assertIsInstance(conditions, dict)
        self.assertIn('conditions_met', conditions)
        self.assertIn('failing_conditions', conditions)
        self.assertIn('market_health', conditions)

if __name__ == '__main__':
    unittest.main()