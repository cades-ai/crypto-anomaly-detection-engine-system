"""
Crypto Anomaly Detection Engine System (CADES)
Sentiment Scorer Module

This module implements advanced sentiment scoring for crypto social media content,
focusing on memecoin-specific sentiment patterns and market indicators.

Author: CADES Team
License: Proprietary
"""

import numpy as np
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Union
import logging
from collections import defaultdict, deque
import json
import torch
import torch.nn as nn
from scipy.special import softmax
from sklearn.preprocessing import MinMaxScaler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class SentimentScore:
    """Comprehensive sentiment scoring result"""
    text: str
    timestamp: datetime
    compound_score: float
    sentiment_scores: Dict[str, float]
    confidence: float
    context_features: Dict[str, float]
    token_scores: Dict[str, float]
    metadata: Dict
    risk_flags: List[str] = field(default_factory=list)

class CryptoSentimentScorer:
    """
    Advanced sentiment scorer for crypto social media content.
    Implements context-aware scoring with market feedback integration.
    """
    
    def __init__(
        self,
        embedding_model,
        min_confidence: float = 0.7,
        context_window: int = 24 * 3600,  # 24 hours
        max_cache_size: int = 10000
    ):
        """
        Initialize the sentiment scorer.
        
        Args:
            embedding_model: Text embedding model instance
            min_confidence: Minimum confidence threshold for scoring
            context_window: Time window for context analysis in seconds
            max_cache_size: Maximum size of scoring cache
        """
        self.embedding_model = embedding_model
        self.min_confidence = min_confidence
        self.context_window = context_window
        
        # Initialize scoring components
        self.sentiment_classifier = self._init_sentiment_classifier()
        self.context_analyzer = self._init_context_analyzer()
        
        # Sentiment lexicons
        self.crypto_lexicon = self._load_crypto_lexicon()
        self.emoji_lexicon = self._load_emoji_lexicon()
        
        # Data structures
        self.score_cache = deque(maxlen=max_cache_size)
        self.token_stats = defaultdict(lambda: {
            'sentiment_history': deque(maxlen=1000),
            'price_correlation': 0.0,
            'volatility_impact': 0.0
        })
        
        # Scalers
        self.feature_scaler = MinMaxScaler()
        self.sentiment_scaler = MinMaxScaler()
        
        # Performance tracking
        self.metrics = defaultdict(list)

    def score_text(
        self,
        text: str,
        context: Optional[Dict] = None,
        market_data: Optional[Dict] = None
    ) -> SentimentScore:
        """
        Generate comprehensive sentiment score for text.
        
        Args:
            text: Text to analyze
            context: Additional context features
            market_data: Related market data if available
            
        Returns:
            Detailed sentiment scoring result
        """
        try:
            # Get text embedding
            embedding = self.embedding_model.get_embedding(text)
            
            # Calculate base sentiment scores
            base_scores = self._calculate_base_sentiment(embedding)
            
            # Apply crypto-specific adjustments
            crypto_scores = self._apply_crypto_adjustments(text, base_scores)
            
            # Analyze context if available
            if context:
                context_features = self._analyze_context(context)
                crypto_scores = self._adjust_for_context(crypto_scores, context_features)
            else:
                context_features = {}
            
            # Consider market data if available
            if market_data:
                market_impact = self._analyze_market_impact(market_data)
                crypto_scores = self._adjust_for_market(crypto_scores, market_impact)
            
            # Calculate confidence score
            confidence = self._calculate_confidence(
                embedding,
                crypto_scores,
                context_features
            )
            
            # Generate token-level scores
            token_scores = self._score_tokens(text)
            
            # Calculate compound score
            compound_score = self._calculate_compound_score(crypto_scores)
            
            # Identify risk flags
            risk_flags = self._identify_risk_flags(
                text,
                crypto_scores,
                context_features
            )
            
            # Create result
            result = SentimentScore(
                text=text,
                timestamp=datetime.now(),
                compound_score=compound_score,
                sentiment_scores=crypto_scores,
                confidence=confidence,
                context_features=context_features,
                token_scores=token_scores,
                metadata={
                    'embedding_dim': embedding.embedding.shape[-1],
                    'text_length': len(text),
                    'has_context': bool(context),
                    'has_market_data': bool(market_data)
                },
                risk_flags=risk_flags
            )
            
            # Update cache and metrics
            self._update_tracking(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error scoring text: {e}")
            raise

    def _calculate_base_sentiment(self, embedding) -> Dict[str, float]:
        """Calculate base sentiment scores from embedding."""
        try:
            # Convert embedding to tensor
            if isinstance(embedding.embedding, np.ndarray):
                embed_tensor = torch.from_numpy(embedding.embedding)
            else:
                embed_tensor = embedding.embedding
            
            # Get classifier predictions
            with torch.no_grad():
                logits = self.sentiment_classifier(embed_tensor)
                probs = softmax(logits.numpy(), axis=-1)
            
            return {
                'positive': float(probs[0]),
                'negative': float(probs[1]),
                'neutral': float(probs[2]),
                'uncertainty': float(probs[3])
            }
            
        except Exception as e:
            logger.error(f"Error calculating base sentiment: {e}")
            raise

    def _apply_crypto_adjustments(
        self,
        text: str,
        base_scores: Dict[str, float]
    ) -> Dict[str, float]:
        """Apply crypto-specific adjustments to sentiment scores."""
        try:
            scores = base_scores.copy()
            
            # Check for crypto-specific terms
            for term, impact in self.crypto_lexicon.items():
                if term.lower() in text.lower():
                    scores['positive'] *= impact.get('positive', 1.0)
                    scores['negative'] *= impact.get('negative', 1.0)
                    scores['uncertainty'] *= impact.get('uncertainty', 1.0)
            
            # Check for emojis
            for emoji, impact in self.emoji_lexicon.items():
                if emoji in text:
                    scores['positive'] *= impact.get('positive', 1.0)
                    scores['negative'] *= impact.get('negative', 1.0)
            
            # Normalize scores
            total = sum(scores.values())
            if total > 0:
                scores = {k: v/total for k, v in scores.items()}
            
            return scores
            
        except Exception as e:
            logger.error(f"Error applying crypto adjustments: {e}")
            raise

    def _analyze_context(self, context: Dict) -> Dict[str, float]:
        """Analyze contextual features for sentiment adjustment."""
        try:
            features = {}
            
            # Analyze temporal patterns
            if 'timestamp' in context:
                features['temporal_factor'] = self._analyze_temporal_pattern(
                    context['timestamp']
                )
            
            # Analyze user influence
            if 'user_stats' in context:
                features['influence_score'] = self._calculate_influence_score(
                    context['user_stats']
                )
            
            # Analyze platform impact
            if 'platform' in context:
                features['platform_factor'] = self._get_platform_factor(
                    context['platform']
                )
            
            # Analyze engagement metrics
            if 'engagement' in context:
                features['engagement_impact'] = self._calculate_engagement_impact(
                    context['engagement']
                )
            
            return features
            
        except Exception as e:
            logger.error(f"Error analyzing context: {e}")
            raise

    def _adjust_for_context(
        self,
        scores: Dict[str, float],
        context_features: Dict[str, float]
    ) -> Dict[str, float]:
        """Adjust sentiment scores based on context."""
        try:
            adjusted_scores = scores.copy()
            
            # Apply temporal adjustment
            if 'temporal_factor' in context_features:
                temporal_impact = context_features['temporal_factor']
                adjusted_scores['positive'] *= (1 + temporal_impact)
                adjusted_scores['negative'] *= (1 - temporal_impact)
            
            # Apply influence adjustment
            if 'influence_score' in context_features:
                influence_impact = context_features['influence_score']
                for sentiment in adjusted_scores:
                    adjusted_scores[sentiment] *= (1 + influence_impact)
            
            # Apply platform adjustment
            if 'platform_factor' in context_features:
                platform_impact = context_features['platform_factor']
                for sentiment in adjusted_scores:
                    adjusted_scores[sentiment] *= platform_impact
            
            # Normalize scores
            total = sum(adjusted_scores.values())
            if total > 0:
                adjusted_scores = {k: v/total for k, v in adjusted_scores.items()}
            
            return adjusted_scores
            
        except Exception as e:
            logger.error(f"Error adjusting for context: {e}")
            raise

    def _analyze_market_impact(self, market_data: Dict) -> Dict[str, float]:
        """Analyze market data for sentiment impact."""
        try:
            impact_factors = {}
            
            # Analyze price movement
            if 'price_change' in market_data:
                impact_factors['price_impact'] = np.tanh(
                    market_data['price_change'] / 100
                )
            
            # Analyze volume
            if 'volume_change' in market_data:
                impact_factors['volume_impact'] = np.clip(
                    market_data['volume_change'] / 1000,
                    -1,
                    1
                )
            
            # Analyze volatility
            if 'volatility' in market_data:
                impact_factors['volatility_impact'] = np.clip(
                    market_data['volatility'] / 100,
                    0,
                    1
                )
            
            return impact_factors
            
        except Exception as e:
            logger.error(f"Error analyzing market impact: {e}")
            raise

    def _adjust_for_market(
        self,
        scores: Dict[str, float],
        market_impact: Dict[str, float]
    ) -> Dict[str, float]:
        """Adjust sentiment scores based on market data."""
        try:
            adjusted_scores = scores.copy()
            
            # Apply price impact
            if 'price_impact' in market_impact:
                price_factor = market_impact['price_impact']
                adjusted_scores['positive'] *= (1 + max(0, price_factor))
                adjusted_scores['negative'] *= (1 + max(0, -price_factor))
            
            # Apply volume impact
            if 'volume_impact' in market_impact:
                volume_factor = market_impact['volume_impact']
                for sentiment in adjusted_scores:
                    adjusted_scores[sentiment] *= (1 + abs(volume_factor))
            
            # Apply volatility impact
            if 'volatility_impact' in market_impact:
                volatility_factor = market_impact['volatility_impact']
                adjusted_scores['uncertainty'] *= (1 + volatility_factor)
            
            # Normalize scores
            total = sum(adjusted_scores.values())
            if total > 0:
                adjusted_scores = {k: v/total for k, v in adjusted_scores.items()}
            
            return adjusted_scores
            
        except Exception as e:
            logger.error(f"Error adjusting for market: {e}")
            raise

    def _calculate_compound_score(self, scores: Dict[str, float]) -> float:
        """Calculate compound sentiment score."""
        try:
            # Weight different sentiment aspects
            weights = {
                'positive': 1.0,
                'negative': -1.0,
                'neutral': 0.0,
                'uncertainty': -0.5
            }
            
            # Calculate weighted sum
            weighted_sum = sum(
                scores.get(sentiment, 0) * weight
                for sentiment, weight in weights.items()
            )
            
            # Normalize to [-1, 1]
            return np.tanh(weighted_sum)
            
        except Exception as e:
            logger.error(f"Error calculating compound score: {e}")
            return 0.0

    def _calculate_confidence(
        self,
        embedding,
        sentiment_scores: Dict[str, float],
        context_features: Dict[str, float]
    ) -> float:
        """Calculate confidence score for sentiment analysis."""
        try:
            confidence_factors = []
            
            # Embedding quality
            embedding_norm = np.linalg.norm(embedding.embedding)
            confidence_factors.append(min(1.0, embedding_norm / 10))
            
            # Sentiment decisiveness
            sentiment_std = np.std(list(sentiment_scores.values()))
            confidence_factors.append(sentiment_std)
            
            # Context reliability
            if context_features:
                context_reliability = np.mean(list(context_features.values()))
                confidence_factors.append(context_reliability)
            
            # Calculate final confidence
            confidence = np.mean(confidence_factors)
            
            return float(confidence)
            
        except Exception as e:
            logger.error(f"Error calculating confidence: {e}")
            return 0.0

    def _score_tokens(self, text: str) -> Dict[str, float]:
        """Generate token-level sentiment scores."""
        try:
            token_scores = {}
            
            # Tokenize text
            tokens = text.lower().split()
            
            # Score individual tokens
            for token in tokens:
                # Check crypto lexicon
                if token in self.crypto_lexicon:
                    impact = self.crypto_lexicon[token]
                    token_scores[token] = impact.get('sentiment', 0.0)
                
                # Check emoji lexicon
                elif token in self.emoji_lexicon:
                    impact = self.emoji_lexicon[token]
                    token_scores[token] = impact.get('sentiment', 0.0)
                
                # Default neutral score
                else:
                    token_scores[token] = 0.0
            
            return token_scores
            
        except Exception as e:
            logger.error(f"Error scoring tokens: {e}")
            return {}

    def _identify_risk_flags(
        self,
        text: str,
        sentiment_scores: Dict[str, float],
        context_features: Dict[str, float]
    ) -> List[str]:
        """Identify potential risk flags in sentiment analysis."""
        try:
            flags = []
            
            # Check extreme sentiment
            if sentiment_scores['positive'] > 0.9:
                flags.append("EXTREME_POSITIVE")
            if sentiment_scores['negative'] > 0.9:
                flags.append("EXTREME_NEGATIVE")
                
            # Check uncertainty
            if sentiment_scores['uncertainty'] > 0.4:
                flags.append("HIGH_UNCERTAINTY")
                
            # Check manipulation indicators
            if self._has_manipulation_indicators(text):
                flags.append("POTENTIAL_MANIPULATION")
                
            # Check spam patterns
            if self._has_spam_patterns(text):
                flags.append("SPAM_LIKELY")
                
            # Check context-based risks
            if context_features:
                if context_features.get('temporal_factor', 0) > 0.8:
                    flags.append("UNUSUAL_TIMING")
                if context_features.get('influence_score', 0) > 0.8:
                    flags.append("HIGH_INFLUENCE")
                    
            return flags
            
        except Exception as e:
            logger.error(f"Error identifying risk flags: {e}")
            return []

    def _has_manipulation_indicators(self, text: str) -> bool:
        """Check for potential manipulation indicators in text."""
        try:
            manipulation_patterns = [
                r'(?i)(guaranteed|promise|definitely)',
                r'(?i)(pump.*dump|moon.*soon)',
                r'(?i)(get in now|don\'t miss|last chance)',
                r'(?i)(x1000|100x|\d{3,}x)',
                r'🚀{3,}'  # Multiple rocket emojis
            ]
            
            return any(
                re.search(pattern, text)
                for pattern in manipulation_patterns
            )
            
        except Exception as e:
            logger.error(f"Error checking manipulation indicators: {e}")
            return False

    def _has_spam_patterns(self, text: str) -> bool:
        """Check for spam patterns in text."""
        try:
            spam_indicators = [
                len(re.findall(r'[A-Z]{4,}', text)) > 2,  # Multiple all-caps words
                len(re.findall(r'!{3,}', text)) > 2,      # Multiple exclamation marks
                len(re.findall(r'(.)\\1{4,}', text)) > 0, # Repeated characters
                len(re.findall(r'http[s]?://', text)) > 2 # Multiple URLs
            ]
            
            return any(spam_indicators)
            
        except Exception as e:
            logger.error(f"Error checking spam patterns: {e}")
            return False

    def _update_tracking(self, result: SentimentScore) -> None:
        """Update tracking metrics with new scoring result."""
        try:
            # Update score cache
            self.score_cache.append(result)
            
            # Update token stats
            for token, score in result.token_scores.items():
                self.token_stats[token]['sentiment_history'].append({
                    'score': score,
                    'timestamp': result.timestamp
                })
            
            # Update metrics
            self.metrics['processing_time'].append(datetime.now())
            self.metrics['confidence_scores'].append(result.confidence)
            
            # Maintain reasonable history size
            max_history = 1000
            for metric in self.metrics:
                if len(self.metrics[metric]) > max_history:
                    self.metrics[metric] = self.metrics[metric][-max_history:]
                    
        except Exception as e:
            logger.error(f"Error updating tracking: {e}")

    def get_sentiment_stats(self) -> Dict:
        """Get current sentiment analysis statistics."""
        try:
            recent_scores = list(self.score_cache)[-1000:]
            
            return {
                "total_processed": len(self.metrics['processing_time']),
                "average_confidence": np.mean(self.metrics['confidence_scores']),
                "sentiment_distribution": self._calculate_sentiment_distribution(recent_scores),
                "risk_flags_frequency": self._calculate_risk_flags_frequency(recent_scores),
                "token_sentiment_stats": self._get_token_sentiment_stats(),
                "processing_rate": self._calculate_processing_rate()
            }
            
        except Exception as e:
            logger.error(f"Error getting sentiment stats: {e}")
            return {}

    def _calculate_sentiment_distribution(
        self,
        scores: List[SentimentScore]
    ) -> Dict[str, float]:
        """Calculate distribution of sentiment scores."""
        try:
            if not scores:
                return {}
                
            # Collect all sentiment scores
            all_sentiments = defaultdict(list)
            for score in scores:
                for sentiment, value in score.sentiment_scores.items():
                    all_sentiments[sentiment].append(value)
            
            # Calculate statistics
            return {
                sentiment: {
                    'mean': float(np.mean(values)),
                    'std': float(np.std(values)),
                    'median': float(np.median(values))
                }
                for sentiment, values in all_sentiments.items()
            }
            
        except Exception as e:
            logger.error(f"Error calculating sentiment distribution: {e}")
            return {}

    def _calculate_risk_flags_frequency(
        self,
        scores: List[SentimentScore]
    ) -> Dict[str, int]:
        """Calculate frequency of different risk flags."""
        try:
            flag_counts = defaultdict(int)
            
            for score in scores:
                for flag in score.risk_flags:
                    flag_counts[flag] += 1
            
            return dict(flag_counts)
            
        except Exception as e:
            logger.error(f"Error calculating risk flags frequency: {e}")
            return {}

    def _get_token_sentiment_stats(self) -> Dict[str, Dict]:
        """Get sentiment statistics for tracked tokens."""
        try:
            stats = {}
            
            for token, token_data in self.token_stats.items():
                recent_scores = [
                    entry['score']
                    for entry in token_data['sentiment_history']
                    if (datetime.now() - entry['timestamp']).total_seconds() < self.context_window
                ]
                
                if recent_scores:
                    stats[token] = {
                        'mean_sentiment': float(np.mean(recent_scores)),
                        'sentiment_std': float(np.std(recent_scores)),
                        'occurrence_count': len(recent_scores),
                        'price_correlation': float(token_data['price_correlation']),
                        'volatility_impact': float(token_data['volatility_impact'])
                    }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting token sentiment stats: {e}")
            return {}

    def _calculate_processing_rate(self) -> float:
        """Calculate current processing rate (scores per second)."""
        try:
            recent_times = self.metrics['processing_time'][-100:]
            if len(recent_times) < 2:
                return 0.0
            
            time_span = (recent_times[-1] - recent_times[0]).total_seconds()
            if time_span == 0:
                return 0.0
            
            return len(recent_times) / time_span
            
        except Exception as e:
            logger.error(f"Error calculating processing rate: {e}")
            return 0.0

    @staticmethod
    def _load_crypto_lexicon() -> Dict[str, Dict[str, float]]:
        """Load crypto-specific sentiment lexicon."""
        return {
            "moon": {
                "positive": 1.5,
                "sentiment": 0.8
            },
            "dump": {
                "negative": 1.5,
                "sentiment": -0.7
            },
            "hodl": {
                "positive": 1.2,
                "sentiment": 0.5
            },
            "fud": {
                "negative": 1.3,
                "uncertainty": 1.5,
                "sentiment": -0.6
            },
            "wagmi": {
                "positive": 1.4,
                "sentiment": 0.7
            },
            "ngmi": {
                "negative": 1.4,
                "sentiment": -0.7
            }
            # Add more crypto-specific terms
        }

    @staticmethod
    def _load_emoji_lexicon() -> Dict[str, Dict[str, float]]:
        """Load emoji sentiment lexicon."""
        return {
            "🚀": {
                "positive": 1.5,
                "sentiment": 0.8
            },
            "💎": {
                "positive": 1.3,
                "sentiment": 0.6
            },
            "🌙": {
                "positive": 1.4,
                "sentiment": 0.7
            },
            "📈": {
                "positive": 1.2,
                "sentiment": 0.5
            },
            "📉": {
                "negative": 1.2,
                "sentiment": -0.5
            },
            "💩": {
                "negative": 1.4,
                "sentiment": -0.7
            }
            # Add more relevant emojis
        }

if __name__ == "__main__":
    # Example usage
    def main():
        from embedding_models import CryptoEmbeddingModel
        
        # Initialize models
        embedding_model = CryptoEmbeddingModel()
        sentiment_scorer = CryptoSentimentScorer(
            embedding_model=embedding_model,
            min_confidence=0.7
        )
        
        # Example texts
        texts = [
            "Extremely bullish on $SOL! 🚀 Breaking ATH soon!",
            "Major red flags with this token. Looks like a rugpull 🚩",
            "WAGMI! Diamond hands only! 💎 100x incoming! 🌙"
        ]
        
        # Score texts
        for text in texts:
            score = sentiment_scorer.score_text(text)
            print(f"\nText: {text}")
            print(f"Compound Score: {score.compound_score:.3f}")
            print(f"Confidence: {score.confidence:.3f}")
            print(f"Risk Flags: {score.risk_flags}")
            print("-" * 50)
        
        # Print statistics
        print("\nSentiment Statistics:")
        print(json.dumps(sentiment_scorer.get_sentiment_stats(), indent=2))
        
    main()