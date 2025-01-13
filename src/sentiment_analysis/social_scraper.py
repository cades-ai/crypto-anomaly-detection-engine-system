"""
Crypto Anomaly Detection Engine System (CADES)
Social Media Data Scraper Module

This module implements advanced social media data collection,
focusing on crypto and memecoin-related content from multiple platforms.

Author: CADES Team
License: Proprietary
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Union, AsyncGenerator
import logging
import json
import aiohttp
import re
from collections import defaultdict, deque
import asyncio
from urllib.parse import urlencode

# Platform-specific imports
from telethon import TelegramClient
from discord import Client as DiscordClient
from tweepy.asynchronous import AsyncClient as TwitterClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class SocialPost:
    """Standardized social media post data structure"""
    platform: str
    post_id: str
    content: str
    author: str
    timestamp: datetime
    engagement: Dict[str, int]
    mentions: List[str]
    hashtags: List[str]
    urls: List[str]
    token_references: List[str]
    raw_data: Dict
    sentiment_hints: Dict[str, float] = field(default_factory=dict)
    metadata: Dict = field(default_factory=dict)

@dataclass
class ScrapingConfig:
    """Configuration for scraping parameters"""
    keywords: List[str]
    token_symbols: List[str]
    platforms: List[str]
    min_engagement: int
    max_posts_per_query: int
    rate_limits: Dict[str, int]
    blacklisted_sources: Set[str]
    language_filter: Optional[List[str]]

class SocialMediaScraper:
    """
    Advanced social media data collector for crypto content.
    Implements rate-limited, parallel scraping from multiple platforms.
    """
    
    def __init__(
        self,
        twitter_credentials: Dict,
        telegram_credentials: Dict,
        discord_credentials: Dict,
        config: ScrapingConfig,
        cache_size: int = 10000,
        update_interval: int = 60
    ):
        """
        Initialize the social media scraper.
        
        Args:
            twitter_credentials: Twitter API credentials
            telegram_credentials: Telegram API credentials
            discord_credentials: Discord bot credentials
            config: Scraping configuration parameters
            cache_size: Maximum size of post cache
            update_interval: Update interval in seconds
        """
        self.config = config
        self.update_interval = update_interval
        
        # Initialize platform clients
        self.twitter_client = self._init_twitter_client(twitter_credentials)
        self.telegram_client = self._init_telegram_client(telegram_credentials)
        self.discord_client = self._init_discord_client(discord_credentials)
        
        # Data structures
        self.post_cache = {
            'twitter': deque(maxlen=cache_size),
            'telegram': deque(maxlen=cache_size),
            'discord': deque(maxlen=cache_size)
        }
        
        # Rate limiting
        self.rate_limiters = {
            platform: self._create_rate_limiter(rate)
            for platform, rate in config.rate_limits.items()
        }
        
        # Tracking metrics
        self.metrics = defaultdict(int)
        self.errors = defaultdict(list)
        
        # Token mention tracking
        self.token_mentions = defaultdict(lambda: defaultdict(int))
        
        # Platform-specific parsers
        self.parsers = {
            'twitter': self._parse_twitter_post,
            'telegram': self._parse_telegram_message,
            'discord': self._parse_discord_message
        }

    async def start_scraping(self) -> None:
        """Start the main scraping loop."""
        try:
            logger.info("Starting social media scraping...")
            
            while True:
                scraping_tasks = []
                
                # Create tasks for each enabled platform
                if 'twitter' in self.config.platforms:
                    scraping_tasks.append(self._scrape_twitter())
                if 'telegram' in self.config.platforms:
                    scraping_tasks.append(self._scrape_telegram())
                if 'discord' in self.config.platforms:
                    scraping_tasks.append(self._scrape_discord())
                
                # Run scraping tasks concurrently
                results = await asyncio.gather(*scraping_tasks, return_exceptions=True)
                
                # Process results
                for result in results:
                    if isinstance(result, Exception):
                        logger.error(f"Scraping error: {result}")
                        
                await asyncio.sleep(self.update_interval)
                
        except Exception as e:
            logger.error(f"Error in main scraping loop: {e}")
            raise

    async def _scrape_twitter(self) -> AsyncGenerator[SocialPost, None]:
        """Scrape crypto-related posts from Twitter."""
        try:
            async with self.rate_limiters['twitter']:
                for keyword in self.config.keywords:
                    query = self._build_twitter_query(keyword)
                    
                    async for tweet in self.twitter_client.search_recent_tweets(
                        query=query,
                        max_results=self.config.max_posts_per_query,
                        tweet_fields=['created_at', 'public_metrics', 'entities']
                    ):
                        try:
                            post = await self._parse_twitter_post(tweet)
                            if post and self._should_process_post(post):
                                self.post_cache['twitter'].append(post)
                                self.metrics['twitter_posts_collected'] += 1
                                yield post
                                
                        except Exception as e:
                            logger.error(f"Error processing tweet: {e}")
                            self.errors['twitter'].append(str(e))
                            
        except Exception as e:
            logger.error(f"Error scraping Twitter: {e}")
            raise

    async def _scrape_telegram(self) -> AsyncGenerator[SocialPost, None]:
        """Scrape crypto-related messages from Telegram channels."""
        try:
            async with self.rate_limiters['telegram']:
                for channel in self._get_telegram_channels():
                    try:
                        async for message in self.telegram_client.iter_messages(
                            channel,
                            limit=self.config.max_posts_per_query,
                            search=self._build_telegram_query()
                        ):
                            try:
                                post = await self._parse_telegram_message(message)
                                if post and self._should_process_post(post):
                                    self.post_cache['telegram'].append(post)
                                    self.metrics['telegram_posts_collected'] += 1
                                    yield post
                                    
                            except Exception as e:
                                logger.error(f"Error processing Telegram message: {e}")
                                self.errors['telegram'].append(str(e))
                                
                    except Exception as e:
                        logger.error(f"Error scraping Telegram channel {channel}: {e}")
                        
        except Exception as e:
            logger.error(f"Error scraping Telegram: {e}")
            raise

    async def _scrape_discord(self) -> AsyncGenerator[SocialPost, None]:
        """Scrape crypto-related messages from Discord channels."""
        try:
            async with self.rate_limiters['discord']:
                for guild_id, channel_ids in self._get_discord_channels().items():
                    for channel_id in channel_ids:
                        try:
                            channel = self.discord_client.get_channel(channel_id)
                            async for message in channel.history(
                                limit=self.config.max_posts_per_query
                            ):
                                try:
                                    if self._matches_discord_filters(message):
                                        post = await self._parse_discord_message(message)
                                        if post and self._should_process_post(post):
                                            self.post_cache['discord'].append(post)
                                            self.metrics['discord_posts_collected'] += 1
                                            yield post
                                            
                                except Exception as e:
                                    logger.error(f"Error processing Discord message: {e}")
                                    self.errors['discord'].append(str(e))
                                    
                        except Exception as e:
                            logger.error(f"Error scraping Discord channel {channel_id}: {e}")
                            
        except Exception as e:
            logger.error(f"Error scraping Discord: {e}")
            raise

    async def _parse_twitter_post(self, tweet: Dict) -> Optional[SocialPost]:
        """Parse Twitter post into standardized format."""
        try:
            # Extract basic information
            content = tweet['text']
            author = tweet['author_id']
            timestamp = datetime.fromisoformat(tweet['created_at'].replace('Z', '+00:00'))
            
            # Extract engagement metrics
            engagement = {
                'likes': tweet['public_metrics']['like_count'],
                'retweets': tweet['public_metrics']['retweet_count'],
                'replies': tweet['public_metrics']['reply_count'],
                'quotes': tweet['public_metrics']['quote_count']
            }
            
            # Extract entities
            entities = tweet.get('entities', {})
            mentions = [m['username'] for m in entities.get('mentions', [])]
            hashtags = [h['tag'] for h in entities.get('hashtags', [])]
            urls = [u['expanded_url'] for u in entities.get('urls', [])]
            
            # Extract token references
            token_refs = self._extract_token_references(content)
            
            # Calculate sentiment hints
            sentiment_hints = self._calculate_sentiment_hints(content)
            
            return SocialPost(
                platform='twitter',
                post_id=tweet['id'],
                content=content,
                author=author,
                timestamp=timestamp,
                engagement=engagement,
                mentions=mentions,
                hashtags=hashtags,
                urls=urls,
                token_references=token_refs,
                sentiment_hints=sentiment_hints,
                raw_data=tweet,
                metadata={
                    'is_retweet': 'retweeted_status' in tweet,
                    'is_quote': 'quoted_status' in tweet,
                    'language': tweet.get('lang')
                }
            )
            
        except Exception as e:
            logger.error(f"Error parsing Twitter post: {e}")
            return None

    def _extract_token_references(self, content: str) -> List[str]:
        """Extract token symbol references from content."""
        try:
            tokens = set()
            
            # Check for cashtags
            cashtags = re.findall(r'\$([A-Za-z0-9]+)', content)
            tokens.update(cashtags)
            
            # Check for configured token symbols
            for token in self.config.token_symbols:
                if re.search(rf'\b{token}\b', content, re.IGNORECASE):
                    tokens.add(token)
            
            return list(tokens)
            
        except Exception as e:
            logger.error(f"Error extracting token references: {e}")
            return []

    def _calculate_sentiment_hints(self, content: str) -> Dict[str, float]:
        """Calculate basic sentiment hints from content."""
        try:
            hints = {}
            
            # Check for bullish indicators
            bullish_patterns = [
                r'(?i)(moon|pump|buy|bullish|ath|green|up)',
                r'🚀|💎|🔥|📈'
            ]
            
            # Check for bearish indicators
            bearish_patterns = [
                r'(?i)(dump|sell|bearish|crash|red|down)',
                r'💩|🔻|📉'
            ]
            
            # Calculate pattern matches
            bullish_count = sum(
                len(re.findall(pattern, content))
                for pattern in bullish_patterns
            )
            
            bearish_count = sum(
                len(re.findall(pattern, content))
                for pattern in bearish_patterns
            )
            
            # Calculate ratios
            total_indicators = bullish_count + bearish_count
            if total_indicators > 0:
                hints['bullish_ratio'] = bullish_count / total_indicators
                hints['bearish_ratio'] = bearish_count / total_indicators
            
            return hints
            
        except Exception as e:
            logger.error(f"Error calculating sentiment hints: {e}")
            return {}

    def _should_process_post(self, post: SocialPost) -> bool:
        """Determine if a post should be processed based on criteria."""
        try:
            # Check engagement threshold
            total_engagement = sum(post.engagement.values())
            if total_engagement < self.config.min_engagement:
                return False
            
            # Check blacklist
            if post.author in self.config.blacklisted_sources:
                return False
            
            # Check language filter
            if (self.config.language_filter and
                post.metadata.get('language') not in self.config.language_filter):
                return False
            
            # Check for token references
            if not post.token_references:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking post processing criteria: {e}")
            return False

    @staticmethod
    async def _create_rate_limiter(rate: int):
        """Create rate limiter context manager."""
        lock = asyncio.Lock()
        last_request = datetime.now()
        interval = 1 / rate  # seconds per request
        
        class RateLimiter:
            async def __aenter__(self):
                async with lock:
                    nonlocal last_request
                    now = datetime.now()
                    elapsed = (now - last_request).total_seconds()
                    if elapsed < interval:
                        await asyncio.sleep(interval - elapsed)
                    last_request = datetime.now()
                    
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass
                
        return RateLimiter()

    def get_scraping_stats(self) -> Dict:
        """Get current scraping statistics."""
        return {
            "metrics": dict(self.metrics),
            "errors": {
                platform: len(errors)
                for platform, errors in self.errors.items()
            },
            "cache_sizes": {
                platform: len(cache)
                for platform, cache in self.post_cache.items()
            },
            "token_mentions": dict(self.token_mentions)
        }

if __name__ == "__main__":
    # Example usage
    async def main():
        # Example configuration
        config = ScrapingConfig(
            keywords=["memecoin", "solana", "crypto"],
            token_symbols=["SOL", "BONK", "WEN"],
            platforms=["twitter", "telegram", "discord"],
            min_engagement=10,
            max_posts_per_query=100,
            blacklisted_sources=set([
                "known_spam_account1",
                "known_bot_account2"
            ]),
            language_filter=["en"]
        )
        
        # Example credentials (would be loaded from environment variables in production)
        twitter_credentials = {
            "consumer_key": "your_consumer_key",
            "consumer_secret": "your_consumer_secret",
            "access_token": "your_access_token",
            "access_token_secret": "your_access_token_secret"
        }
        
        telegram_credentials = {
            "api_id": "your_api_id",
            "api_hash": "your_api_hash",
            "phone": "your_phone_number"
        }
        
        discord_credentials = {
            "token": "your_bot_token"
        }
        
        # Create scraper instance
        scraper = SocialMediaScraper(
            twitter_credentials=twitter_credentials,
            telegram_credentials=telegram_credentials,
            discord_credentials=discord_credentials,
            config=config,
            cache_size=10000,
            update_interval=60
        )
        
        # Start scraping
        try:
            async for post in scraper._scrape_twitter():
                print(f"New Twitter post: {post.content[:100]}...")
                print(f"Engagement: {post.engagement}")
                print(f"Token references: {post.token_references}")
                print("-" * 50)
                
        except Exception as e:
            print(f"Error during scraping: {e}")
            
    # Run the async main function
    asyncio.run(main())