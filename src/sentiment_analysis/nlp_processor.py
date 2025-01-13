"""
Crypto Anomaly Detection Engine System (CADES)
Social Media NLP Processor Module

This module implements advanced NLP processing for crypto social media content,
focusing on memecoin-specific sentiment analysis and trend detection.

Author: CADES Team
License: Proprietary
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple
import numpy as np
from collections import defaultdict, deque
import logging
import json
import re
from enum import Enum

# NLP-specific imports
from transformers import pipeline
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import spacy
from textblob import TextBlob

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SentimentClass(Enum):
    """Classification of sentiment types"""
    VERY_BULLISH = "very_bullish"
    BULLISH = "bullish"
    NEUTRAL = "neutral"
    BEARISH = "bearish"
    VERY_BEARISH = "very_bearish"
    UNCERTAIN = "uncertain"
    SHILL = "shill"
    FUD = "fud"

@dataclass
class SocialMediaPost:
    """Representation of a social media post"""
    platform: str
    content: str
    timestamp: datetime
    author: str
    engagement: Dict[str, int]
    mentions: List[str]
    hashtags: List[str]
    urls: List[str]
    is_reply: bool
    reply_to: Optional[str]
    raw_data: Dict

@dataclass
class SentimentAnalysis:
    """Results of sentiment analysis on a post"""
    post_id: str
    sentiment_class: SentimentClass
    sentiment_scores: Dict[str, float]
    confidence: float
    key_phrases: List[str]
    entities: List[str]
    spam_probability: float
    shill_probability: float
    influence_score: float
    timestamp: datetime

class SocialMediaNLPProcessor:
    """
    Advanced NLP processor for crypto social media content.
    Implements specialized analysis for memecoin-related discussions.
    """
    
    def __init__(
        self,
        language_model: str = "finiteautomata/bertweet-base-sentiment-analysis",
        min_confidence: float = 0.75,
        cache_size: int = 10000,
        update_interval: int = 60
    ):
        """
        Initialize the NLP processor with specified models and parameters.
        
        Args:
            language_model: Pre-trained model to use for sentiment analysis
            min_confidence: Minimum confidence threshold for sentiment classification
            cache_size: Maximum size of post cache
            update_interval: Update interval in seconds
        """
        self.min_confidence = min_confidence
        self.update_interval = update_interval
        
        # Initialize NLP models
        try:
            self.sentiment_analyzer = pipeline("sentiment-analysis", model=language_model)
            self.vader_analyzer = SentimentIntensityAnalyzer()
            self.nlp = spacy.load("en_core_web_sm")
            logger.info("Successfully loaded NLP models")
        except Exception as e:
            logger.error(f"Error loading NLP models: {e}")
            raise

        # Data structures for analysis
        self.post_cache = deque(maxlen=cache_size)
        self.sentiment_history: Dict[str, List[SentimentAnalysis]] = defaultdict(list)
        self.author_profiles: Dict[str, Dict] = defaultdict(dict)
        self.token_mentions: Dict[str, List[Dict]] = defaultdict(list)
        
        # Specialized lexicons and patterns
        self.crypto_lexicon = self._load_crypto_lexicon()
        self.meme_patterns = self._load_meme_patterns()
        self.spam_patterns = self._compile_spam_patterns()
        
        # Temporal analysis windows
        self.sentiment_windows: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=360)  # 1 hour of 10-second intervals
        )

    def process_post(self, post: SocialMediaPost) -> Optional[SentimentAnalysis]:
        """
        Process a single social media post for sentiment and other metrics.
        
        Args:
            post: Social media post to analyze
            
        Returns:
            Sentiment analysis results if processing successful
        """
        try:
            # Preprocess text
            cleaned_text = self._preprocess_text(post.content)
            if not cleaned_text:
                return None

            # Extract key components
            entities = self._extract_entities(cleaned_text)
            key_phrases = self._extract_key_phrases(cleaned_text)
            
            # Perform sentiment analysis
            sentiment_scores = self._analyze_sentiment(cleaned_text)
            
            # Classify sentiment
            sentiment_class, confidence = self._classify_sentiment(
                sentiment_scores,
                post.engagement,
                entities
            )
            
            if confidence < self.min_confidence:
                sentiment_class = SentimentClass.UNCERTAIN
            
            # Calculate spam and shill probabilities
            spam_prob = self._calculate_spam_probability(post, cleaned_text)
            shill_prob = self._calculate_shill_probability(post, cleaned_text)
            
            # Calculate influence score
            influence_score = self._calculate_influence_score(post)
            
            # Create sentiment analysis result
            analysis = SentimentAnalysis(
                post_id=str(hash(post.content)),
                sentiment_class=sentiment_class,
                sentiment_scores=sentiment_scores,
                confidence=confidence,
                key_phrases=key_phrases,
                entities=entities,
                spam_probability=spam_prob,
                shill_probability=shill_prob,
                influence_score=influence_score,
                timestamp=post.timestamp
            )
            
            # Update tracking data
            self._update_tracking_data(post, analysis)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error processing post: {e}")
            return None

    def _preprocess_text(self, text: str) -> str:
        """Preprocess social media text for analysis."""
        try:
            # Remove URLs
            text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
            
            # Remove emojis while preserving crypto-relevant symbols
            text = self._clean_emojis(text)
            
            # Normalize whitespace
            text = ' '.join(text.split())
            
            # Convert crypto slang to standard terms
            text = self._normalize_crypto_terms(text)
            
            # Remove ASCII art and repetitive patterns
            text = self._remove_ascii_art(text)
            
            return text.strip()
            
        except Exception as e:
            logger.error(f"Error preprocessing text: {e}")
            return ""

    def _analyze_sentiment(self, text: str) -> Dict[str, float]:
        """
        Perform multi-model sentiment analysis on text.
        
        Returns:
            Dict containing sentiment scores from different models
        """
        try:
            # Get transformer model sentiment
            transformer_sentiment = self.sentiment_analyzer(text)[0]
            
            # Get VADER sentiment
            vader_sentiment = self.vader_analyzer.polarity_scores(text)
            
            # Get TextBlob sentiment
            blob_sentiment = TextBlob(text).sentiment
            
            # Combine scores with weights
            combined_sentiment = {
                'positive': transformer_sentiment['score'] if transformer_sentiment['label'] == 'POSITIVE' else 0,
                'negative': transformer_sentiment['score'] if transformer_sentiment['label'] == 'NEGATIVE' else 0,
                'neutral': vader_sentiment['neu'],
                'compound': vader_sentiment['compound'],
                'subjectivity': blob_sentiment.subjectivity
            }
            
            # Add crypto-specific sentiment
            crypto_sentiment = self._analyze_crypto_sentiment(text)
            combined_sentiment.update(crypto_sentiment)
            
            return combined_sentiment
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            return {
                'positive': 0,
                'negative': 0,
                'neutral': 1,
                'compound': 0,
                'subjectivity': 0
            }

    def _analyze_crypto_sentiment(self, text: str) -> Dict[str, float]:
        """Analyze crypto-specific sentiment patterns."""
        try:
            sentiment = {
                'fomo': 0.0,
                'fud': 0.0,
                'shill': 0.0,
                'moon': 0.0,
                'dump': 0.0
            }
            
            # Check for FOMO indicators
            fomo_patterns = [
                r'(?i)(don\'t miss|gonna moon|next 100x|guaranteed|cant miss)',
                r'(?i)(early|presale|whitelist|private sale)',
                r'🚀|💎|🌙'
            ]
            
            # Check for FUD indicators
            fud_patterns = [
                r'(?i)(scam|rug|honeypot|fake|ponzi)',
                r'(?i)(dead|dump|crash|bear|manipulation)',
                r'⚠️|🔪|💀'
            ]
            
            # Calculate pattern matches
            for pattern in fomo_patterns:
                matches = re.findall(pattern, text)
                sentiment['fomo'] += len(matches) * 0.2
                
            for pattern in fud_patterns:
                matches = re.findall(pattern, text)
                sentiment['fud'] += len(matches) * 0.2
            
            # Normalize scores
            for key in sentiment:
                sentiment[key] = min(1.0, sentiment[key])
            
            return sentiment
            
        except Exception as e:
            logger.error(f"Error analyzing crypto sentiment: {e}")
            return {'fomo': 0, 'fud': 0, 'shill': 0, 'moon': 0, 'dump': 0}

    def _classify_sentiment(
        self,
        sentiment_scores: Dict[str, float],
        engagement: Dict[str, int],
        entities: List[str]
    ) -> Tuple[SentimentClass, float]:
        """
        Classify sentiment based on scores and context.
        
        Returns:
            Tuple of (SentimentClass, confidence_score)
        """
        try:
            # Base sentiment classification
            compound_score = sentiment_scores['compound']
            fomo_score = sentiment_scores.get('fomo', 0)
            fud_score = sentiment_scores.get('fud', 0)
            
            # Calculate confidence based on multiple factors
            confidence_factors = [
                abs(compound_score),
                1 - sentiment_scores['neutral'],
                min(1.0, len(entities) / 5),
                min(1.0, engagement.get('likes', 0) / 100)
            ]
            
            confidence = np.mean(confidence_factors)
            
            # Determine sentiment class
            if fomo_score > 0.7:
                return SentimentClass.SHILL, confidence
            elif fud_score > 0.7:
                return SentimentClass.FUD, confidence
            elif compound_score >= 0.5:
                return SentimentClass.VERY_BULLISH, confidence
            elif compound_score >= 0.1:
                return SentimentClass.BULLISH, confidence
            elif compound_score <= -0.5:
                return SentimentClass.VERY_BEARISH, confidence
            elif compound_score <= -0.1:
                return SentimentClass.BEARISH, confidence
            else:
                return SentimentClass.NEUTRAL, confidence
                
        except Exception as e:
            logger.error(f"Error classifying sentiment: {e}")
            return SentimentClass.UNCERTAIN, 0.0

    def _calculate_influence_score(self, post: SocialMediaPost) -> float:
        """Calculate influence score for a social media post."""
        try:
            # Base engagement metrics
            likes_score = min(1.0, post.engagement.get('likes', 0) / 1000)
            retweets_score = min(1.0, post.engagement.get('retweets', 0) / 500)
            replies_score = min(1.0, post.engagement.get('replies', 0) / 100)
            
            # Author influence metrics
            author_profile = self.author_profiles.get(post.author, {})
            follower_score = min(1.0, author_profile.get('followers', 0) / 10000)
            author_reputation = author_profile.get('reputation', 0.5)
            
            # Calculate temporal relevance
            time_diff = (datetime.now() - post.timestamp).total_seconds() / 3600
            temporal_factor = np.exp(-time_diff / 24)  # Decay over 24 hours
            
            # Combine scores with weights
            influence_score = (
                likes_score * 0.3 +
                retweets_score * 0.2 +
                replies_score * 0.1 +
                follower_score * 0.2 +
                author_reputation * 0.2
            ) * temporal_factor
            
            return min(1.0, influence_score)
            
        except Exception as e:
            logger.error(f"Error calculating influence score: {e}")
            return 0.0

    def _extract_entities(self, text: str) -> List[str]:
        """Extract named entities and crypto-specific terms."""
        try:
            entities = set()
            
            # Extract named entities using spaCy
            doc = self.nlp(text)
            for ent in doc.ents:
                if ent.label_ in ['ORG', 'PRODUCT', 'PERSON']:
                    entities.add(ent.text)
            
            # Extract crypto-specific entities
            for token in self.crypto_lexicon['tokens']:
                if token.lower() in text.lower():
                    entities.add(token)
            
            # Extract cashtags
            cashtags = re.findall(r'\$([A-Za-z0-9]+)', text)
            entities.update(cashtags)
            
            return list(entities)
            
        except Exception as e:
            logger.error(f"Error extracting entities: {e}")
            return []

    def _extract_key_phrases(self, text: str) -> List[str]:
        """Extract key phrases from text."""
        try:
            # Use spaCy for noun phrase extraction
            doc = self.nlp(text)
            noun_phrases = [chunk.text for chunk in doc.noun_chunks]
            
            # Extract phrases with crypto terms
            crypto_phrases = []
            for phrase in noun_phrases:
                if any(term in phrase.lower() for term in self.crypto_lexicon['terms']):
                    crypto_phrases.append(phrase)
            
            # Extract price-related phrases
            price_phrases = re.findall(
                r'([0-9]+(?:[,.][0-9]+)?[\s]*(?:x|×|times|%))',
                text
            )
            
            return list(set(crypto_phrases + price_phrases))
            
        except Exception as e:
            logger.error(f"Error extracting key phrases: {e}")
            return []

    def _update_tracking_data(self, post: SocialMediaPost, analysis: SentimentAnalysis) -> None:
        """Update tracking data with new post analysis."""
        try:
            # Update sentiment history
            for entity in analysis.entities:
                if self._is_token_entity(entity):
                    self.sentiment_history[entity].append(analysis)
                    
                    # Maintain history size
                    if len(self.sentiment_history[entity]) > 1000:
                        self.sentiment_history[entity] = self.sentiment_history[entity][-1000:]
            
            # Update author profile
            self._update_author_profile(post, analysis)
            
            # Update token mentions
            self._update_token_mentions(post, analysis)
            
        except Exception as e:
            logger.error(f"Error updating tracking data: {e}")

    def _update_author_profile(self, post: SocialMediaPost, analysis: SentimentAnalysis) -> None:
        """Update author profile with new post data."""
        try:
            profile = self.author_profiles.get(post.author, {
                'posts_count': 0,
                'spam_count': 0,
                'shill_count': 0,
                'influence_scores': [],
                'sentiment_distribution': defaultdict(int),
                'last_active': None,
                'reputation': 0.5
            })
            
            # Update basic metrics
            profile['posts_count'] += 1
            if analysis.spam_probability > 0.7:
                profile['spam_count'] += 1
            if analysis.shill_probability > 0.7:
                profile['shill_count'] += 1
            
            # Update influence tracking
            profile['influence_scores'].append(analysis.influence_score)
            if len(profile['influence_scores']) > 100:
                profile['influence_scores'] = profile['influence_scores'][-100:]
            
            # Update sentiment distribution
            profile['sentiment_distribution'][analysis.sentiment_class.value] += 1
            
            # Update activity timestamp
            profile['last_active'] = post.timestamp
            
            # Calculate reputation score
            profile['reputation'] = self._calculate_author_reputation(profile)
            
            self.author_profiles[post.author] = profile
            
        except Exception as e:
            logger.error(f"Error updating author profile: {e}")

    def _calculate_author_reputation(self, profile: Dict) -> float:
        """Calculate author reputation score."""
        try:
            if profile['posts_count'] == 0:
                return 0.5
                
            # Calculate spam and shill rates
            spam_rate = profile['spam_count'] / profile['posts_count']
            shill_rate = profile['shill_count'] / profile['posts_count']
            
            # Calculate average influence
            avg_influence = np.mean(profile['influence_scores']) if profile['influence_scores'] else 0.5
            
            # Calculate sentiment diversity
            sentiment_counts = list(profile['sentiment_distribution'].values())
            sentiment_diversity = len([c for c in sentiment_counts if c > 0]) / len(SentimentClass)
            
            # Combine factors
            reputation = (
                (1 - spam_rate) * 0.3 +
                (1 - shill_rate) * 0.3 +
                avg_influence * 0.2 +
                sentiment_diversity * 0.2
            )
            
            return min(1.0, max(0.0, reputation))
            
        except Exception as e:
            logger.error(f"Error calculating author reputation: {e}")
            return 0.5

    def get_token_sentiment_analysis(self, token_symbol: str) -> Dict:
        """Get comprehensive sentiment analysis for a token."""
        try:
            sentiment_data = self.sentiment_history.get(token_symbol, [])
            if not sentiment_data:
                return {
                    "error": "No sentiment data available for token"
                }
            
            # Calculate sentiment metrics
            recent_sentiment = sentiment_data[-100:]  # Last 100 analyses
            
            sentiment_distribution = defaultdict(int)
            influence_weighted_sentiment = defaultdict(float)
            total_influence = 0
            
            for analysis in recent_sentiment:
                sentiment_distribution[analysis.sentiment_class.value] += 1
                influence_weighted_sentiment[analysis.sentiment_class.value] += analysis.influence_score
                total_influence += analysis.influence_score
            
            # Calculate averages and normalize
            if total_influence > 0:
                weighted_distribution = {
                    k: v / total_influence
                    for k, v in influence_weighted_sentiment.items()
                }
            else:
                weighted_distribution = {
                    k: v / len(recent_sentiment)
                    for k, v in sentiment_distribution.items()
                }
            
            return {
                "sentiment_distribution": dict(sentiment_distribution),
                "weighted_sentiment": weighted_distribution,
                "overall_sentiment": self._calculate_overall_sentiment(recent_sentiment),
                "confidence": np.mean([a.confidence for a in recent_sentiment]),
                "spam_rate": np.mean([a.spam_probability for a in recent_sentiment]),
                "shill_rate": np.mean([a.shill_probability for a in recent_sentiment]),
                "influence_score": np.mean([a.influence_score for a in recent_sentiment]),
                "analysis_count": len(recent_sentiment)
            }
            
        except Exception as e:
            logger.error(f"Error getting token sentiment analysis: {e}")
            return {"error": str(e)}

    def _calculate_overall_sentiment(self, analyses: List[SentimentAnalysis]) -> str:
        """Calculate overall sentiment from a list of analyses."""
        try:
            if not analyses:
                return "neutral"
            
            # Weight sentiments by influence score
            weighted_sentiments = defaultdict(float)
            total_influence = 0
            
            for analysis in analyses:
                weighted_sentiments[analysis.sentiment_class.value] += analysis.influence_score
                total_influence += analysis.influence_score
            
            if total_influence == 0:
                return "neutral"
            
            # Normalize weights
            normalized_sentiments = {
                k: v / total_influence
                for k, v in weighted_sentiments.items()
            }
            
            # Return dominant sentiment
            return max(normalized_sentiments.items(), key=lambda x: x[1])[0]
            
        except Exception as e:
            logger.error(f"Error calculating overall sentiment: {e}")
            return "neutral"

    @staticmethod
    def _is_token_entity(entity: str) -> bool:
        """Check if an entity is a token symbol."""
        return bool(re.match(r'^[A-Z0-9]{2,10}_spam_probability(self, post: SocialMediaPost, text: str) -> float:
        """Calculate probability that a post is spam."""
        try:
            spam_indicators = [
                len(re.findall(pattern, text))
                for pattern in self.spam_patterns
            ]
            
            # Calculate basic spam score
            spam_score = sum([
                # Repetitive patterns
                min(1.0, sum(spam_indicators) / 5),
                
                # Too many hashtags
                min(1.0, len(post.hashtags) / 10),
                
                # Too many URLs
                min(1.0, len(post.urls) / 3),
                
                # ALL CAPS ratio
                len(re.findall(r'[A-Z]{4,}', text)) / (len(text.split()) + 1),
                
                # Excessive punctuation
                len(re.findall(r'[!?]{2,}', text)) / (len(text) + 1)
            ]) / 5
            
            # Adjust based on author reputation
            author_profile = self.author_profiles.get(post.author, {})
            if author_profile:
                reputation_factor = author_profile.get('spam_rate', 0.5)
                spam_score = (spam_score + reputation_factor) / 2
            
            return min(1.0, spam_score)
            
        except Exception as e:
            logger.error(f"Error calculating spam probability: {e}")
            return 0.5

    def _calculate_shill_probability(self, post: SocialMediaPost, text: str) -> float:
        """Calculate probability that a post is shilling."""
        try:
            shill_indicators = [
                # Excessive emojis
                len(re.findall(r'[\U0001F300-\U0001F9FF]', text)) / (len(text) + 1),
                
                # Price/gain mentions
                len(re.findall(r'(?i)(x1000|100x|\d+%|moon|pump)', text)) / (len(text.split()) + 1),
                
                # Urgency terms
                len(re.findall(r'(?i)(hurry|fast|quick|soon|now|today)', text)) / (len(text.split()) + 1),
                
                # Multiple exclamations
                len(re.findall(r'!{2,}', text)) / (len(text) + 1),
                
                # ALL CAPS words
                len(re.findall(r'[A-Z]{4,}', text)) / (len(text.split()) + 1)
            ]
            
            # Calculate base shill score
            shill_score = sum(shill_indicators) / len(shill_indicators)
            
            # Adjust based on author history
            author_profile = self.author_profiles.get(post.author, {})
            if author_profile:
                shill_factor = author_profile.get('shill_rate', 0.5)
                shill_score = (shill_score + shill_factor) / 2
            
            return min(1.0, shill_score)
            
        except Exception as e:
            logger.error(f"Error calculating shill probability: {e}")
            return 0.5

    def _calculate, entity))

    @staticmethod
    def _load_crypto_lexicon() -> Dict:
        """Load crypto-specific terms and patterns."""
        return {
            'tokens': [
                'BTC', 'ETH', 'SOL', 'USDT', 'USDC',
                'DEX', 'NFT', 'DeFi', 'AMM', 'LP'
            ],
            'terms': [
                'moon', 'dump', 'pump', 'hodl', 'fud',
                'fomo', 'dip', 'shill', 'rug', 'ape'
            ],
            'patterns': [
                r'(?i)(x\d+)',
                r'(?i)(to the moon)',
                r'(?i)(diamond hands)',
                r'(?i)(paper hands)',
                r'(?i)(buy the dip)'
            ]
        }

    @staticmethod
    def _compile_spam_patterns() -> List[str]:
        """Compile regex patterns for spam detection."""
        return [
            r'(?i)(win|earn|claim|airdrop|free)',
            r'(?i)(join now|last chance|don\'t miss)',
            r'(?i)(guaranteed|proven|best|profitable)',
            r'(\d{12,})',  # Long numbers
            r'([@#]\w+){3,}'  # Multiple tags
        ]

    def _remove_ascii_art(self, text: str) -> str:
        """Remove ASCII art and repetitive patterns."""
        # Remove lines with repetitive characters
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            if not re.match(r'^(.)\1{4,}_spam_probability(self, post: SocialMediaPost, text: str) -> float:
        """Calculate probability that a post is spam."""
        try:
            spam_indicators = [
                len(re.findall(pattern, text))
                for pattern in self.spam_patterns
            ]
            
            # Calculate basic spam score
            spam_score = sum([
                # Repetitive patterns
                min(1.0, sum(spam_indicators) / 5),
                
                # Too many hashtags
                min(1.0, len(post.hashtags) / 10),
                
                # Too many URLs
                min(1.0, len(post.urls) / 3),
                
                # ALL CAPS ratio
                len(re.findall(r'[A-Z]{4,}', text)) / (len(text.split()) + 1),
                
                # Excessive punctuation
                len(re.findall(r'[!?]{2,}', text)) / (len(text) + 1)
            ]) / 5
            
            # Adjust based on author reputation
            author_profile = self.author_profiles.get(post.author, {})
            if author_profile:
                reputation_factor = author_profile.get('spam_rate', 0.5)
                spam_score = (spam_score + reputation_factor) / 2
            
            return min(1.0, spam_score)
            
        except Exception as e:
            logger.error(f"Error calculating spam probability: {e}")
            return 0.5

    def _calculate_shill_probability(self, post: SocialMediaPost, text: str) -> float:
        """Calculate probability that a post is shilling."""
        try:
            shill_indicators = [
                # Excessive emojis
                len(re.findall(r'[\U0001F300-\U0001F9FF]', text)) / (len(text) + 1),
                
                # Price/gain mentions
                len(re.findall(r'(?i)(x1000|100x|\d+%|moon|pump)', text)) / (len(text.split()) + 1),
                
                # Urgency terms
                len(re.findall(r'(?i)(hurry|fast|quick|soon|now|today)', text)) / (len(text.split()) + 1),
                
                # Multiple exclamations
                len(re.findall(r'!{2,}', text)) / (len(text) + 1),
                
                # ALL CAPS words
                len(re.findall(r'[A-Z]{4,}', text)) / (len(text.split()) + 1)
            ]
            
            # Calculate base shill score
            shill_score = sum(shill_indicators) / len(shill_indicators)
            
            # Adjust based on author history
            author_profile = self.author_profiles.get(post.author, {})
            if author_profile:
                shill_factor = author_profile.get('shill_rate', 0.5)
                shill_score = (shill_score + shill_factor) / 2
            
            return min(1.0, shill_score)
            
        except Exception as e:
            logger.error(f"Error calculating shill probability: {e}")
            return 0.5

    def _calculate, line.strip()):
                cleaned_lines.append(line)
        return ' '.join(cleaned_lines)

if __name__ == "__main__":
    # Example usage
    async def main():
        processor = SocialMediaNLPProcessor()
        
        # Example social media post
        post = SocialMediaPost(
            platform="twitter",
            content="$SOL is mooning! 🚀 Don't miss this incredible 100x opportunity! #Solana #DeFi",
            timestamp=datetime.now(),
            author="crypto_whale",
            engagement={'likes': 100, 'retweets': 50, 'replies': 20},
            mentions=['@solana'],
            hashtags=['#Solana', '#DeFi'],
            urls=[],
            is_reply=False,
            reply_to=None,
            raw_data={}
        )
        
        # Process post
        analysis = processor.process_post(post)
        if analysis:
            print(f"Sentiment: {analysis.sentiment_class}")
            print(f"Confidence: {analysis.confidence:.2f}")
            print(f"Shill Probability: {analysis.shill_probability:.2f}")
        
    asyncio.run(main())_spam_probability(self, post: SocialMediaPost, text: str) -> float:
        """Calculate probability that a post is spam."""
        try:
            spam_indicators = [
                len(re.findall(pattern, text))
                for pattern in self.spam_patterns
            ]
            
            # Calculate basic spam score
            spam_score = sum([
                # Repetitive patterns
                min(1.0, sum(spam_indicators) / 5),
                
                # Too many hashtags
                min(1.0, len(post.hashtags) / 10),
                
                # Too many URLs
                min(1.0, len(post.urls) / 3),
                
                # ALL CAPS ratio
                len(re.findall(r'[A-Z]{4,}', text)) / (len(text.split()) + 1),
                
                # Excessive punctuation
                len(re.findall(r'[!?]{2,}', text)) / (len(text) + 1)
            ]) / 5
            
            # Adjust based on author reputation
            author_profile = self.author_profiles.get(post.author, {})
            if author_profile:
                reputation_factor = author_profile.get('spam_rate', 0.5)
                spam_score = (spam_score + reputation_factor) / 2
            
            return min(1.0, spam_score)
            
        except Exception as e:
            logger.error(f"Error calculating spam probability: {e}")
            return 0.5

    def _calculate_shill_probability(self, post: SocialMediaPost, text: str) -> float:
        """Calculate probability that a post is shilling."""
        try:
            shill_indicators = [
                # Excessive emojis
                len(re.findall(r'[\U0001F300-\U0001F9FF]', text)) / (len(text) + 1),
                
                # Price/gain mentions
                len(re.findall(r'(?i)(x1000|100x|\d+%|moon|pump)', text)) / (len(text.split()) + 1),
                
                # Urgency terms
                len(re.findall(r'(?i)(hurry|fast|quick|soon|now|today)', text)) / (len(text.split()) + 1),
                
                # Multiple exclamations
                len(re.findall(r'!{2,}', text)) / (len(text) + 1),
                
                # ALL CAPS words
                len(re.findall(r'[A-Z]{4,}', text)) / (len(text.split()) + 1)
            ]
            
            # Calculate base shill score
            shill_score = sum(shill_indicators) / len(shill_indicators)
            
            # Adjust based on author history
            author_profile = self.author_profiles.get(post.author, {})
            if author_profile:
                shill_factor = author_profile.get('shill_rate', 0.5)
                shill_score = (shill_score + shill_factor) / 2
            
            return min(1.0, shill_score)
            
        except Exception as e:
            logger.error(f"Error calculating shill probability: {e}")
            return 0.5

    def _calculate_temporal_metrics(self, token: str) -> Dict[str, float]:
        """Calculate temporal metrics for token sentiment analysis."""
        try:
            now = datetime.now()
            recent_analyses = [
                analysis for analysis in self.sentiment_history.get(token, [])
                if (now - analysis.timestamp).total_seconds() < 3600  # Last hour
            ]
            
            if not recent_analyses:
                return {
                    'sentiment_velocity': 0.0,
                    'sentiment_acceleration': 0.0,
                    'engagement_rate': 0.0
                }
            
            # Calculate sentiment velocity (rate of change)
            sentiment_values = [
                1 if a.sentiment_class in [SentimentClass.VERY_BULLISH, SentimentClass.BULLISH]
                else -1 if a.sentiment_class in [SentimentClass.VERY_BEARISH, SentimentClass.BEARISH]
                else 0 for a in recent_analyses
            ]
            
            # Calculate metrics over 10-minute windows
            window_size = 600  # 10 minutes in seconds
            windows = []
            
            for i in range(0, 3600, window_size):
                window_start = now - timedelta(seconds=3600-i)
                window_end = window_start + timedelta(seconds=window_size)
                
                window_analyses = [
                    a for a in recent_analyses
                    if window_start <= a.timestamp < window_end
                ]
                
                if window_analyses:
                    avg_sentiment = np.mean([
                        s for s in sentiment_values[:len(window_analyses)]
                    ])
                    windows.append(avg_sentiment)
                else:
                    windows.append(0)
            
            # Calculate velocity (first derivative)
            velocity = np.gradient(windows).mean()
            
            # Calculate acceleration (second derivative)
            acceleration = np.gradient(np.gradient(windows)).mean()
            
            # Calculate engagement rate
            total_analyses = len(recent_analyses)
            engagement_rate = total_analyses / 36  # Per 100 seconds
            
            return {
                'sentiment_velocity': float(velocity),
                'sentiment_acceleration': float(acceleration),
                'engagement_rate': float(engagement_rate)
            }
            
        except Exception as e:
            logger.error(f"Error calculating temporal metrics: {e}")
            return {
                'sentiment_velocity': 0.0,
                'sentiment_acceleration': 0.0,
                'engagement_rate': 0.0
            }

    def _clean_emojis(self, text: str) -> str:
        """Clean emojis while preserving crypto-relevant symbols."""
        try:
            # Define crypto-relevant emojis to keep
            crypto_emojis = {
                '🚀', '💎', '🌙', '📈', '📉', '💰', '🔥',
                '🌟', '⭐', '🎯', '🎮', '🌐', '💫', '⚡'
            }
            
            # Replace other emojis with space
            clean_text = ''
            for char in text:
                if char in crypto_emojis:
                    clean_text += char
                elif ord(char) >= 0x1F300:  # Unicode emoji range
                    clean_text += ' '
                else:
                    clean_text += char
            
            return ' '.join(clean_text.split())
            
        except Exception as e:
            logger.error(f"Error cleaning emojis: {e}")
            return text

    def _normalize_crypto_terms(self, text: str) -> str:
        """Normalize crypto-specific terms and slang."""
        try:
            # Define normalization mappings
            normalizations = {
                r'(?i)hodl': 'hold',
                r'(?i)rekt': 'wrecked',
                r'(?i)wagmi': 'we are going to make it',
                r'(?i)ngmi': 'not going to make it',
                r'(?i)gm': 'good morning',
                r'(?i)ser': 'sir',
                r'(?i)smol': 'small',
                r'(?i)safu': 'safe',
                r'(?i)gwei': 'gas',
                r'(?i)ser': 'sir',
                r'(?i)ngmi': 'not going to make it',
                r'(?i)fud': 'fear uncertainty doubt',
                r'(?i)fomo': 'fear of missing out'
            }
            
            normalized_text = text
            for pattern, replacement in normalizations.items():
                normalized_text = re.sub(pattern, replacement, normalized_text)
            
            return normalized_text
            
        except Exception as e:
            logger.error(f"Error normalizing crypto terms: {e}")
            return text

    def _update_token_mentions(self, post: SocialMediaPost, analysis: SentimentAnalysis) -> None:
        """Update token mentions tracking data."""
        try:
            for entity in analysis.entities:
                if self._is_token_entity(entity):
                    mention_data = {
                        'timestamp': post.timestamp,
                        'sentiment_class': analysis.sentiment_class.value,
                        'influence_score': analysis.influence_score,
                        'author': post.author,
                        'engagement': post.engagement
                    }
                    
                    self.token_mentions[entity].append(mention_data)
                    
                    # Maintain history size
                    if len(self.token_mentions[entity]) > 1000:
                        self.token_mentions[entity] = self.token_mentions[entity][-1000:]
                        
        except Exception as e:
            logger.error(f"Error updating token mentions: {e}")

    def _load_meme_patterns(self) -> Dict[str, List[str]]:
        """Load patterns for detecting meme-specific content."""
        return {
            'templates': [
                r'(?i)(wen moon)',
                r'(?i)(number go up)',
                r'(?i)(make it clap)',
                r'(?i)(lets pump it)',
                r'(?i)(to the moon)'
            ],
            'reactions': [
                r'(?i)(based)',
                r'(?i)(bullish)',
                r'(?i)(this is the way)',
                r'(?i)(let\'s go)',
                r'(?i)(wagmi)'
            ],
            'trends': [
                r'(?i)(pepe)',
                r'(?i)(wojak)',
                r'(?i)(chad)',
                r'(?i)(virgin)',
                r'(?i)(diamond hands)'
            ]
        }

    async def process_posts_batch(self, posts: List[SocialMediaPost]) -> List[SentimentAnalysis]:
        """Process a batch of posts asynchronously."""
        try:
            analyses = []
            for post in posts:
                analysis = self.process_post(post)
                if analysis:
                    analyses.append(analysis)
            return analyses
            
        except Exception as e:
            logger.error(f"Error processing posts batch: {e}")
            return []

    def get_trending_topics(self, timeframe: int = 3600) -> List[Dict]:
        """Get trending topics from recent analyses."""
        try:
            now = datetime.now()
            recent_mentions = []
            
            # Collect recent mentions across all tokens
            for token, mentions in self.token_mentions.items():
                token_mentions = [
                    m for m in mentions
                    if (now - m['timestamp']).total_seconds() < timeframe
                ]
                
                if token_mentions:
                    # Calculate engagement score
                    total_engagement = sum(
                        m['engagement'].get('likes', 0) +
                        m['engagement'].get('retweets', 0) * 2 +
                        m['engagement'].get('replies', 0) * 3
                        for m in token_mentions
                    )
                    
                    # Calculate weighted sentiment
                    sentiment_score = sum(
                        m['influence_score'] * (
                            1 if m['sentiment_class'] in ['very_bullish', 'bullish']
                            else -1 if m['sentiment_class'] in ['very_bearish', 'bearish']
                            else 0
                        )
                        for m in token_mentions
                    )
                    
                    recent_mentions.append({
                        'token': token,
                        'mention_count': len(token_mentions),
                        'unique_authors': len(set(m['author'] for m in token_mentions)),
                        'engagement_score': total_engagement,
                        'sentiment_score': sentiment_score,
                        'trending_score': (
                            len(token_mentions) * 0.4 +
                            total_engagement * 0.4 +
                            abs(sentiment_score) * 0.2
                        )
                    })
            
            # Sort by trending score
            trending = sorted(
                recent_mentions,
                key=lambda x: x['trending_score'],
                reverse=True
            )
            
            return trending[:10]  # Return top 10 trending topics
            
        except Exception as e:
            logger.error(f"Error getting trending topics: {e}")
            return []