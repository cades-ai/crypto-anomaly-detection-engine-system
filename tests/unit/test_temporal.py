""" Crypto Anomaly Detection Engine System(CADES)

Temporal Analysis Test Suite

This module implements testing for time-based analysis components,
including LSTM predictions, volatility calculations, and flash crash detection.

Author: CADES
Team License: Proprietary """

import unittest
from unittest.mock import Mock, patch
import pytest
import numpy as np
import pandas as pd
from src.temporal_analysis.lstm_predictor import LSTMPredictor
from src.temporal_analysis.volatility_calculator import VolatilityCalculator

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


if __name__ == '__main__':
    unittest.main()