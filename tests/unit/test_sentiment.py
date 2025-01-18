""" Crypto Anomaly Detection Engine System (CADES)

Sentiment Analysis Test Suite

This module implements testing for social sentiment analysis components,
including social media scraping, NLP processing, and cross-platform sentiment aggregation.

Author: CADES
Team License: Proprietary """

import unittest
from unittest.mock import Mock, patch
import pytest
import numpy as np
from src.sentiment_analysis.social_scraper import SocialScraper
from src.sentiment_analysis.nlp_processor import NLPProcessor
from src.sentiment_analysis.sentiment_scorer import SentimentScorer
from src.sentiment_analysis.embedding_models import CryptoEmbeddingModel
from src.sentiment_analysis.social_momentum_analyzer import SocialMomentumAnalyzer

class TestSocialScraper(unittest.TestCase):
    def setUp(self):
        self.scraper = SocialScraper(
            twitter_api_key="mock_key",
            telegram_token="mock_token",
            discord_token="mock_token"
        )
        
    @patch('tweepy.Client')
    def test_fetch_twitter_mentions(self, mock_client):
        mock_tweets = [
            {'id': '1', 'text': 'Bullish on $TOKEN', 'public_metrics': {'retweet_count': 100}},
            {'id': '2', 'text': 'Bearish signals for $TOKEN', 'public_metrics': {'retweet_count': 50}}
        ]
        mock_client.return_value.search_recent_tweets.return_value = Mock(data=mock_tweets)
        
        results = self.scraper.fetch_twitter_mentions('$TOKEN')
        self.assertEqual(len(results), 2)
        self.assertTrue(all('sentiment_weight' in tweet for tweet in results))

    @patch('telethon.TelegramClient')
    def test_monitor_telegram_groups(self, mock_client):
        mock_messages = [
            {'id': 1, 'message': 'Token launch soon!', 'views': 1000},
            {'id': 2, 'message': 'Price prediction thread', 'views': 500}
        ]
        mock_client.return_value.get_messages.return_value = mock_messages
        
        messages = self.scraper.monitor_telegram_groups(['group1', 'group2'])
        self.assertTrue(len(messages) > 0)
        self.assertTrue(all('timestamp' in msg for msg in messages))


class TestNLPProcessor(unittest.TestCase):
    def setUp(self):
        self.processor = NLPProcessor()
        self.sample_texts = [
            "Super bullish on this project!🚀🚀🚀",
            "Looks like a scam, be careful",
            "Normal market movements, nothing special"
        ]

    def test_preprocess_text(self):
        processed = self.processor.preprocess_text(self.sample_texts[0])
        self.assertIsInstance(processed, str)
        self.assertNotIn('🚀', processed)  # Emoji should be removed
        
    def test_extract_features(self):
        features = self.processor.extract_features(self.sample_texts)
        self.assertEqual(len(features), len(self.sample_texts))
        self.assertTrue(all(isinstance(f, dict) for f in features))

    def test_detect_manipulation_patterns(self):
        suspicious_text = "100x guaranteed! Buy now before moon! Not financial advice!"
        score = self.processor.detect_manipulation_patterns(suspicious_text)
        self.assertTrue(0 <= score <= 1)
        self.assertGreater(score, 0.5)  # Should detect suspicious patterns


class TestEmbeddingModel(unittest.TestCase):
    def setUp(self):
        self.model = CryptoEmbeddingModel()
        self.test_sentence = "Major announcement coming for $TOKEN"

    def test_generate_embeddings(self):
        embedding = self.model.get_embedding(self.test_sentence)
        self.assertIsInstance(embedding.embedding, np.ndarray)
        self.assertEqual(embedding.embedding.shape[0], self.model.embedding_dim)

    def test_calculate_similarity(self):
        text1 = "Bullish on this project"
        text2 = "Very optimistic about the token"
        similarity = self.model.calculate_similarity(
            self.model.get_embedding(text1), 
            self.model.get_embedding(text2)
        )
        self.assertTrue(0 <= similarity <= 1)

    @patch('transformers.pipeline')
    def test_bert_classification(self, mock_pipeline):
        mock_pipeline.return_value = lambda x: [{'label': 'POSITIVE', 'score': 0.9}]
        result = self.model.get_embedding("Great project with solid fundamentals")
        self.assertIsNotNone(result)
        self.assertIsInstance(result.metadata, dict)

    def test_batch_processing(self):
        texts = ["Text 1", "Text 2", "Text 3"]
        embeddings = self.model.get_batch_embeddings(texts)
        self.assertEqual(len(embeddings), len(texts))
        self.assertTrue(all(e.embedding.shape[0] == self.model.embedding_dim for e in embeddings))

    def test_crypto_vocabulary_weighting(self):
        crypto_text = "bullish on solana defi ecosystem"
        normal_text = "regular text without crypto terms"
        
        crypto_embedding = self.model.get_embedding(crypto_text)
        normal_embedding = self.model.get_embedding(normal_text)
        
        self.assertIsNotNone(crypto_embedding)
        self.assertIsNotNone(normal_embedding)

class TestSocialMomentumAnalyzer(unittest.TestCase):
    def setUp(self):
        self.mock_embedding_model = Mock()
        self.analyzer = SocialMomentumAnalyzer(
            embedding_model=self.mock_embedding_model,
            min_momentum_threshold=100,
            analysis_window=3600
        )
        
        # Sample test data
        self.test_social_data = {
            "messages": ["Test message"] * 10,
            "sentiment_scores": [0.8] * 10,
            "engagement_metrics": {
                "likes": 100,
                "shares": 50,
                "comments": 25
            }
        }

    async def test_analyze_social_momentum(self):
        momentum_metrics = await self.analyzer.analyze_social_momentum(
            "test_token",
            self.test_social_data
        )
        self.assertIsNotNone(momentum_metrics)
        self.assertTrue(0 <= momentum_metrics.momentum_score <= 1)
        self.assertIsInstance(momentum_metrics.timestamp, datetime)

    def test_analyze_velocity_components(self):
        velocity_metrics = self.analyzer._analyze_velocity_components(
            "test_token",
            self.test_social_data
        )
        self.assertIsInstance(velocity_metrics, dict)
        self.assertIn('velocity', velocity_metrics)
        self.assertIn('acceleration', velocity_metrics)

    def test_analyze_organic_ratio(self):
        organic_metrics = self.analyzer._analyze_organic_ratio(self.test_social_data)
        self.assertIsInstance(organic_metrics, dict)
        self.assertIn('organic_ratio', organic_metrics)
        self.assertTrue(0 <= organic_metrics['organic_ratio'] <= 1)

    def test_analyze_amplification(self):
        amplification_metrics = self.analyzer._analyze_amplification(self.test_social_data)
        self.assertIsInstance(amplification_metrics, dict)
        self.assertIn('amplification_factor', amplification_metrics)

    def test_analyze_sentiment_velocity(self):
        sentiment_velocity = self.analyzer._analyze_sentiment_velocity(self.test_social_data)
        self.assertIsInstance(sentiment_velocity, dict)
        self.assertIn('velocity', sentiment_velocity)

    def test_identify_key_drivers(self):
        drivers = self.analyzer._identify_key_drivers(self.test_social_data)
        self.assertIsInstance(drivers, list)
        self.assertTrue(all(isinstance(d, str) for d in drivers))

    @patch('datetime.datetime')
    def test_momentum_thresholds(self, mock_datetime):
        mock_datetime.now.return_value = datetime(2024, 1, 1)
        
        # Test below threshold
        low_activity_data = {
            "messages": ["Test"] * 5,  # Below min_momentum_threshold
            "sentiment_scores": [0.5] * 5
        }
        result = self.analyzer._meets_momentum_threshold(low_activity_data)
        self.assertFalse(result)
        
        # Test above threshold
        high_activity_data = {
            "messages": ["Test"] * 200,  # Above min_momentum_threshold
            "sentiment_scores": [0.5] * 200
        }
        result = self.analyzer._meets_momentum_threshold(high_activity_data)
        self.assertTrue(result)

    def test_generate_risk_indicators(self):
        momentum_metrics = {
            'momentum_score': 0.9,
            'velocity': 0.8,
            'organic_ratio': 0.3
        }
        indicators = self.analyzer._generate_risk_indicators(momentum_metrics)
        self.assertIsInstance(indicators, list)
        self.assertTrue(len(indicators) > 0)

class TestSentimentScorer(unittest.TestCase):
    def setUp(self):
        self.scorer = SentimentScorer()
        self.sample_data = {
            'text': "Extremely bullish signals for $TOKEN",
            'metrics': {
                'likes': 100,
                'retweets': 50,
                'replies': 25
            }
        }

    def test_calculate_engagement_weight(self):
        weight = self.scorer.calculate_engagement_weight(self.sample_data['metrics'])
        self.assertTrue(0 <= weight <= 1)
        
    def test_analyze_sentiment_trend(self):
        historical_data = [
            {'sentiment': 0.8, 'timestamp': '2024-01-01'},
            {'sentiment': 0.6, 'timestamp': '2024-01-02'},
            {'sentiment': 0.9, 'timestamp': '2024-01-03'}
        ]
        trend = self.scorer.analyze_sentiment_trend(historical_data)
        self.assertIn('trend_direction', trend)
        self.assertIn('volatility', trend)

    def test_detect_sentiment_manipulation(self):
        sudden_changes = [
            {'sentiment': 0.2, 'timestamp': '2024-01-01T00:00:00'},
            {'sentiment': 0.9, 'timestamp': '2024-01-01T00:05:00'},  # Suspicious rapid change
            {'sentiment': 0.85, 'timestamp': '2024-01-01T00:10:00'}
        ]
        manipulation_score = self.scorer.detect_sentiment_manipulation(sudden_changes)
        self.assertGreater(manipulation_score, 0.5)  # Should detect manipulation

    def test_aggregate_cross_platform_sentiment(self):
        platform_data = {
            'twitter': {'sentiment': 0.8, 'confidence': 0.9},
            'telegram': {'sentiment': 0.7, 'confidence': 0.8},
            'discord': {'sentiment': 0.6, 'confidence': 0.7}
        }
        aggregate = self.scorer.aggregate_cross_platform_sentiment(platform_data)
        self.assertIn('overall_sentiment', aggregate)
        self.assertIn('confidence_score', aggregate)
        self.assertTrue(0 <= aggregate['overall_sentiment'] <= 1)

if __name__ == '__main__':
    unittest.main()