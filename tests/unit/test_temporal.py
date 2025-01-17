""" Crypto Anomaly Detection Engine System (CADES)

Temporal Analysis Test Suite

This module implements testing for time-based analysis components,
including LSTM predictions, volatility calculations, flash crash detection,
and momentum tracking.

Author: CADES Team
License: Proprietary """

import unittest
from unittest.mock import Mock, patch
import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

from src.temporal_analysis.lstm_predictor import LSTMPredictor
from src.temporal_analysis.volatility_calculator import VolatilityCalculator
from src.temporal_analysis.flash_crash_detector import FlashCrashDetector
from src.temporal_analysis.momentum_tracker import MomentumTracker


class TestLSTMPredictor(unittest.TestCase):
    def setUp(self):
        self.predictor = LSTMPredictor(
            lookback_period=24,
            forecast_horizon=6,
            hidden_layers=[64, 32]
        )
        self.sample_data = pd.DataFrame({
            'timestamp': pd.date_range(start='2024-01-01', periods=100, freq='H'),
            'price': np.random.random(100) * 100,
            'volume': np.random.random(100) * 1000
        })

    def test_prepare_sequences(self):
        X, y = self.predictor.prepare_sequences(self.sample_data)
        self.assertEqual(X.shape[1], self.predictor.lookback_period)
        self.assertEqual(y.shape[1], self.predictor.forecast_horizon)

    def test_normalize_features(self):
        normalized = self.predictor.normalize_features(self.sample_data)
        self.assertTrue(normalized['price'].between(-1, 1).all())
        self.assertTrue(normalized['volume'].between(-1, 1).all())

    @patch('tensorflow.keras.models.Sequential')
    def test_train_model(self, mock_model):
        mock_model.return_value.fit.return_value = Mock(history={'loss': [0.1, 0.05]})
        history = self.predictor.train_model(self.sample_data)
        self.assertIn('loss', history)
        self.assertTrue(len(history['loss']) > 0)


class TestVolatilityCalculator(unittest.TestCase):
    def setUp(self):
        self.calculator = VolatilityCalculator(
            window_size=20,
            scaling_factor=252
        )
        self.price_data = pd.Series(np.random.random(100) * 100)

    def test_calculate_historical_volatility(self):
        volatility = self.calculator.calculate_historical_volatility(self.price_data)
        self.assertIsInstance(volatility, float)
        self.assertTrue(volatility >= 0)

    def test_detect_volatility_regime_change(self):
        historical_vol = pd.Series(np.random.random(50) * 0.2)
        regime_change = self.calculator.detect_volatility_regime_change(historical_vol)
        self.assertIsInstance(regime_change, dict)
        self.assertIn('change_detected', regime_change)
        self.assertIn('confidence_score', regime_change)

    def test_calculate_realized_volatility(self):
        high_prices = pd.Series(np.random.random(100) * 110)
        low_prices = pd.Series(np.random.random(100) * 90)
        realized_vol = self.calculator.calculate_realized_volatility(
            high_prices, low_prices
        )
        self.assertTrue(realized_vol.between(0, 1).all())


class TestFlashCrashDetector(unittest.TestCase):
    def setUp(self):
        self.detector = FlashCrashDetector(
            price_threshold=0.1,
            time_window='5min',
            volume_multiplier=3
        )
        self.test_data = pd.DataFrame({
            'timestamp': pd.date_range(start='2024-01-01', periods=1000, freq='1min'),
            'price': np.random.random(1000) * 100,
            'volume': np.random.random(1000) * 1000
        })

    def test_detect_sudden_price_drops(self):
        # Inject a flash crash pattern
        self.test_data.loc[500:505, 'price'] *= 0.7  # 30% drop
        self.test_data.loc[500:505, 'volume'] *= 5   # 5x volume spike
        
        alerts = self.detector.detect_sudden_price_drops(self.test_data)
        self.assertTrue(len(alerts) > 0)
        self.assertTrue(all(isinstance(alert, dict) for alert in alerts))

    def test_calculate_liquidity_impact(self):
        impact = self.detector.calculate_liquidity_impact(
            price_change=-0.15,
            volume_change=2.5,
            baseline_liquidity=1000000
        )
        self.assertTrue(0 <= impact <= 1)
        self.assertIsInstance(impact, float)

    def test_generate_early_warning(self):
        warning = self.detector.generate_early_warning({
            'price_drop': 0.12,
            'volume_spike': 3.5,
            'liquidity_impact': 0.8
        })
        self.assertIn('warning_level', warning)
        self.assertIn('confidence_score', warning)
        self.assertIn('recommended_actions', warning)

    def test_validate_flash_crash(self):
        crash_pattern = {
            'price_movement': -0.25,
            'volume_change': 4.0,
            'recovery_time': '10min',
            'affected_tokens': ['TOKEN1', 'TOKEN2']
        }
        validation = self.detector.validate_flash_crash(crash_pattern)
        self.assertIsInstance(validation, dict)
        self.assertIn('is_valid_crash', validation)
        self.assertIn('severity_score', validation)


class TestMomentumTracker(unittest.TestCase):
    def setUp(self):
        self.tracker = MomentumTracker(
            timeframes=['5m', '15m', '1h', '4h', '1d'],
            rsi_periods=14,
            macd_params=(12, 26, 9),
            volume_ma_periods=20
        )
        self.test_data = {
            'token_address': 'TEST_TOKEN',
            'price': 100.0,
            'volume': 50000.0,
            'timestamp': datetime.now()
        }

    async def test_update_momentum(self):
        signals = await self.tracker.update_momentum(
            self.test_data['token_address'],
            self.test_data['price'],
            self.test_data['volume'],
            self.test_data['timestamp']
        )
        if signals:
            self.assertIsInstance(signals, dict)
            for timeframe, signal in signals.items():
                self.assertIn('signal_type', signal.__dict__)
                self.assertIn('strength', signal.__dict__)
                self.assertIn('confidence', signal.__dict__)

    def test_calculate_indicators(self):
        # Add some historical data
        for i in range(30):
            self.tracker._update_price_history(
                self.test_data['token_address'],
                self.test_data['price'] * (1 + np.random.normal(0, 0.02)),
                self.test_data['volume'] * (1 + np.random.normal(0, 0.1)),
                self.test_data['timestamp'] - timedelta(minutes=i*5)
            )

        indicators = self.tracker._calculate_indicators(
            self.test_data['token_address'],
            '1h'
        )
        self.assertIn('rsi', indicators)
        self.assertIn('macd', indicators)
        self.assertIn('volume_trend', indicators)

    def test_calculate_momentum_strength(self):
        strength, direction = self.tracker._calculate_momentum_strength(
            rsi=65.0,
            macd=0.5,
            signal=0.3,
            hist=0.2,
            volume_trend=0.4,
            price_trend=0.3
        )
        self.assertTrue(0 <= strength <= 1)
        self.assertIn(direction, ['bullish', 'bearish', 'neutral'])

    def test_generate_warning_signals(self):
        indicators = {
            'rsi': 75.0,
            'macd': (0.5, 0.3, 0.2),
            'volume_trend': 0.8
        }
        warnings = self.tracker._generate_warning_signals(
            indicators,
            strength=0.8,
            direction='bullish'
        )
        self.assertIsInstance(warnings, list)
        self.assertTrue(all(isinstance(w, str) for w in warnings))

if __name__ == '__main__':
    unittest.main()