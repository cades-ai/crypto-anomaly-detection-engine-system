"""Crypto Anomaly Detection Engine System (CADES)

Unit Test Configuration

This module contains configuration and fixtures for unit testing individual components.

Author: CADES Team
License: Proprietary"""

import pytest
import os

# Unit test configuration
UNIT_TEST_CONFIG = {
    'use_mock_data': True,
    'mock_data_path': os.path.join(os.path.dirname(__file__), 'mock_data'),
    'bypass_blockchain': True,
    'bypass_external_apis': True,
}

@pytest.fixture(scope='session')
def test_config():
    """Basic configuration for unit tests"""
    return UNIT_TEST_CONFIG

@pytest.fixture(scope='function')
def mock_blockchain_data():
    """Mock blockchain data for testing"""
    return {
        'transactions': [],
        'blocks': [],
        'timestamps': []
    }

@pytest.fixture(scope='function')
def mock_sentiment_data():
    """Mock social media data for testing"""
    return {
        'tweets': [],
        'telegram_messages': [],
        'reddit_posts': []
    }
