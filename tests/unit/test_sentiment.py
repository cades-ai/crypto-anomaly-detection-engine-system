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