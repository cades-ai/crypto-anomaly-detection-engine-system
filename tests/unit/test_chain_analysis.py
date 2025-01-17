""" Crypto Anomaly Detection Engine System (CADES)

Chain Analysis Test Suite

This module implements comprehensive testing for blockchain data analysis components,
including transaction patterns, liquidity tracking, wallet profiling, and memecoin detection.

Author: CADES Team
License: Proprietary """

import unittest
from unittest.mock import Mock, patch
import pytest
import json
from datetime import datetime, timedelta

from src.chain_analysis.blockchain_listener import BlockchainListener
from src.chain_analysis.transaction_analyzer import TransactionAnalyzer
from src.chain_analysis.liquidity_tracker import LiquidityTracker
from src.chain_analysis.wallet_profiler import WalletProfiler
from src.chain_analysis.memecoin_detector import MemecoinDetector


class TestBlockchainListener(unittest.TestCase):
    def setUp(self):
        self.mock_client = Mock()
        self.listener = BlockchainListener(rpc_endpoint="mock_url")
        self.listener.client = self.mock_client

    @patch('solana.rpc.api.Client.get_block')
    def test_process_new_block(self, mock_get_block):
        mock_block = {
            'blockHeight': 12345,
            'transactions': [
                {
                    'transaction': {
                        'signatures': ['5KtPn1...'],
                        'message': {
                            'accountKeys': ['Address1', 'Address2'],
                            'instructions': [{'programId': 'Program1'}]
                        }
                    }
                }
            ],
            'blockTime': 1678901234
        }
        mock_get_block.return_value = mock_block
        
        result = self.listener.process_new_block(12345)
        self.assertEqual(len(result['transactions']), 1)
        self.assertEqual(result['block_height'], 12345)

    def test_filter_mempool_transactions(self):
        mock_txs = [
            {
                'signature': '5KtPn1...',
                'meta': {
                    'fee': 5000,
                    'preBalances': [1000000, 2000000],
                    'postBalances': [990000, 2010000]
                }
            },
            {
                'signature': '6LuQm2...',
                'meta': {
                    'fee': 5000,
                    'preBalances': [500000, 1000000],
                    'postBalances': [495000, 1005000]
                }
            }
        ]
        filtered = self.listener.filter_mempool_transactions(mock_txs)
        self.assertTrue(len(filtered) > 0)


class TestTransactionAnalyzer(unittest.TestCase):
    def setUp(self):
        self.analyzer = TransactionAnalyzer()
        with open('tests/fixtures/mock_blockchain_data.json', 'r') as f:
            self.mock_data = json.load(f)
        self.sample_tx = self.mock_data['test_transactions'][0]

    def test_detect_wash_trading(self):
        transactions = [self.sample_tx] * 5
        result = self.analyzer.analyze_transaction(self.sample_tx)
        self.assertIsInstance(result, dict)
        self.assertIn('risk_score', result)

    def test_analyze_cyclic_transactions(self):
        tx_with_cycle = {
            'meta': {
                'innerInstructions': [
                    {
                        'instructions': [
                            {'accounts': ['A', 'B']},
                            {'accounts': ['B', 'C']},
                            {'accounts': ['C', 'A']}
                        ]
                    }
                ]
            }
        }
        result = self.analyzer.analyze_transaction(tx_with_cycle)
        self.assertTrue('cyclic' in result['detected_patterns'])


class TestLiquidityTracker(unittest.TestCase):
    def setUp(self):
        self.tracker = LiquidityTracker()
        
    def test_calculate_liquidity_impact(self):
        pool_data = {
            'token_a_reserve': 1000000,
            'token_b_reserve': 1000000,
            'pool_token_supply': 2000000,
            'mint': 'PoolTokenMint123'
        }
        impact = self.tracker.calculate_liquidity_impact(100000, pool_data)
        self.assertIsInstance(impact, float)
        self.assertTrue(0 <= impact <= 1)

    def test_detect_liquidity_removal(self):
        events = [
            {
                'signature': '5KtPn1...',
                'meta': {
                    'preTokenBalances': [{'uiAmount': 1000}],
                    'postTokenBalances': [{'uiAmount': 0}]
                }
            },
            {
                'signature': '6LuQm2...',
                'meta': {
                    'preTokenBalances': [{'uiAmount': 2000}],
                    'postTokenBalances': [{'uiAmount': 0}]
                }
            }
        ]
        threshold = 0.1
        is_suspicious = self.tracker.detect_liquidity_removal(events, threshold)
        self.assertIsInstance(is_suspicious, bool)


class TestWalletProfiler(unittest.TestCase):
    def setUp(self):
        self.mock_client = Mock()
        self.profiler = WalletProfiler(
            rpc_client=self.mock_client,
            min_volume_usd=1000,
            analysis_window=24 * 3600
        )
        self.sample_wallet = 'TestWalletAddress123'

    @patch('src.chain_analysis.wallet_profiler.WalletProfiler._fetch_wallet_transactions')
    async def test_profile_wallet(self, mock_fetch):
        # Mock transaction data
        mock_transactions = [
            {
                'signature': 'tx1',
                'timestamp': datetime.now() - timedelta(hours=1),
                'amount': 5000,
                'type': 'buy',
                'token_address': 'token1'
            },
            {
                'signature': 'tx2',
                'timestamp': datetime.now(),
                'amount': 3000,
                'type': 'sell',
                'token_address': 'token1'
            }
        ]
        mock_fetch.return_value = mock_transactions

        profile = await self.profiler.profile_wallet(self.sample_wallet)
        self.assertIsNotNone(profile)
        self.assertIn('profile', profile)
        self.assertIn('risk_metrics', profile)

    def test_calculate_risk_metrics(self):
        base_metrics = {
            'total_volume_usd': 100000,
            'transaction_count': 50,
            'holding_periods': [3600, 7200, 1800],
            'profit_loss': 5000
        }
        patterns = [
            {
                'type': 'high_frequency_trading',
                'confidence': 0.8
            }
        ]

        risk_metrics = self.profiler._calculate_risk_metrics(base_metrics, patterns)
        self.assertIn('total_risk', risk_metrics)
        self.assertIn('risk_level', risk_metrics)
        self.assertTrue(0 <= risk_metrics['total_risk'] <= 1)

    def test_detect_hft_pattern(self):
        transactions = [
            {
                'signature': f'tx{i}',
                'timestamp': datetime.now() - timedelta(minutes=i),
                'amount': 1000
            }
            for i in range(50)
        ]
        is_hft = self.profiler._detect_hft_pattern(transactions)
        self.assertIsInstance(is_hft, bool)


class TestMemecoinDetector(unittest.TestCase):
    def setUp(self):
        self.mock_client = Mock()
        self.detector = MemecoinDetector(
            rpc_client=self.mock_client,
            min_liquidity_usd=10000,
            social_signal_threshold=0.6
        )
        self.sample_token = 'TestTokenAddress123'

    @patch('src.chain_analysis.memecoin_detector.MemecoinDetector._get_token_metadata')
    async def test_analyze_token(self, mock_metadata):
        # Mock token metadata
        mock_metadata.return_value = {
            'name': 'Test Meme Token',
            'symbol': 'MEME',
            'supply': 1000000000
        }

        analysis = await self.detector.analyze_token(self.sample_token)
        self.assertIsNotNone(analysis)
        self.assertIn('token_info', analysis)
        self.assertIn('metrics', analysis)
        self.assertIn('risk_assessment', analysis)

    def test_detect_pump_and_dump(self):
        price_history = [1.0, 1.2, 1.5, 3.0, 2.5, 1.8, 1.2]
        volume_data = {
            'normal_volume': 10000,
            'spike_volume': 50000
        }
        
        is_pump = self.detector._detect_pump_and_dump(
            self.sample_token,
            price_history,
            volume_data
        )
        self.assertIsInstance(is_pump, bool)

    def test_detect_social_manipulation(self):
        social_data = {
            'signal_strength': 0.85,
            'bot_activity': 0.7,
            'coordination_level': 0.8
        }
        
        is_manipulated = self.detector._detect_social_manipulation(
            self.sample_token,
            social_data
        )
        self.assertIsInstance(is_manipulated, bool)

    def test_assess_risk(self):
        metrics = {
            'holder_count': 1000,
            'total_supply': 1000000000,
            'liquidity_usd': 50000,
            'price_change': 2.5
        }
        patterns = [
            {
                'pattern_type': 'pump_and_dump',
                'confidence': 0.9
            }
        ]
        
        risk_assessment = self.detector._assess_risk(metrics, patterns)
        self.assertIn('risk_level', risk_assessment)
        self.assertIn('risk_scores', risk_assessment)
        self.assertIn('warning_signals', risk_assessment)


if __name__ == '__main__':
    unittest.main()