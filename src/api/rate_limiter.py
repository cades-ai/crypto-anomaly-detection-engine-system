"""
Crypto Anomaly Detection Engine System (CADES)
Rate Limiter Module

This module implements rate limiting functionality for the API endpoints
using a token bucket algorithm and Redis for distributed rate limiting.

Author: CADES Team
License: Proprietary
"""

import time
import logging
from typing import Optional, Tuple, Dict
from datetime import datetime
import asyncio
import yaml
from redis.asyncio import Redis
from fastapi import HTTPException, Request
import orjson

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RateLimiter:
    """
    Implements token bucket algorithm for rate limiting with Redis backend.
    Supports multiple rate limit tiers and dynamic rate adjustments.
    """
    
    def __init__(self, redis_url: str, config_path: str = "config/default.yml"):
        """
        Initialize rate limiter with Redis connection and config.
        
        Args:
            redis_url: Redis connection URL
            config_path: Path to configuration YAML file
        """
        self.redis: Optional[Redis] = None
        self.redis_url = redis_url
        self.config = self._load_config(config_path)
        self.rate_limits = self.config.get('rate_limits', {})
        
    def _load_config(self, config_path: str) -> Dict:
        """Load rate limit configuration from YAML file."""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return {}
            
    async def initialize(self) -> None:
        """Initialize Redis connection pool."""
        try:
            self.redis = Redis.from_url(
                self.redis_url,
                decode_responses=True,
                encoding='utf-8'
            )
            await self.redis.ping()
            logger.info("Successfully connected to Redis")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
            
    async def close(self) -> None:
        """Close Redis connection."""
        if self.redis:
            await self.redis.close()
            
    async def _get_tier_limits(self, api_key: str) -> Dict:
        """Get rate limit configuration for API key tier."""
        # Check tier from configuration or Redis
        tier_key = f"tier:{api_key}"
        tier = await self.redis.get(tier_key) or "basic"
        
        return self.rate_limits.get(tier, self.rate_limits["basic"])
        
    async def check_rate_limit(
        self,
        api_key: str,
        endpoint: str
    ) -> Tuple[bool, Dict]:
        """
        Check if request is within rate limits.
        
        Args:
            api_key: API key for the request
            endpoint: API endpoint being accessed
            
        Returns:
            Tuple of (is_allowed: bool, limit_info: Dict)
        """
        try:
            # Get tier limits
            tier_limits = await self._get_tier_limits(api_key)
            
            # Get endpoint specific limits
            endpoint_limits = tier_limits.get(endpoint, tier_limits.get("default"))
            if not endpoint_limits:
                logger.warning(f"No rate limits found for endpoint {endpoint}")
                return True, {}
                
            # Current timestamp
            now = time.time()
            
            # Keys for rate limiting
            bucket_key = f"bucket:{api_key}:{endpoint}"
            last_update_key = f"last_update:{api_key}:{endpoint}"
            
            # Get current bucket level and last update time
            pipeline = self.redis.pipeline()
            pipeline.get(bucket_key)
            pipeline.get(last_update_key)
            current_tokens, last_update = await pipeline.execute()
            
            # Initialize if not exists
            current_tokens = float(current_tokens) if current_tokens else endpoint_limits["burst"]
            last_update = float(last_update) if last_update else now
            
            # Calculate token refill
            time_passed = now - last_update
            token_refill = time_passed * endpoint_limits["rate"]
            new_tokens = min(
                current_tokens + token_refill,
                endpoint_limits["burst"]
            )
            
            # Check if request can be processed
            if new_tokens >= 1:
                new_tokens -= 1
                is_allowed = True
            else:
                is_allowed = False
                
            # Update bucket and timestamp
            pipeline = self.redis.pipeline()
            pipeline.set(bucket_key, new_tokens)
            pipeline.set(last_update_key, now)
            await pipeline.execute()
            
            # Prepare limit info
            limit_info = {
                "limit": endpoint_limits["burst"],
                "remaining": int(new_tokens),
                "reset": int(now + (endpoint_limits["burst"] - new_tokens) / endpoint_limits["rate"])
            }
            
            return is_allowed, limit_info
            
        except Exception as e:
            logger.error(f"Error checking rate limit: {e}")
            # Fail open - allow request if rate limiting fails
            return True, {}
            
    async def get_rate_limit_headers(
        self,
        api_key: str,
        endpoint: str
    ) -> Dict[str, str]:
        """Generate rate limit headers for response."""
        try:
            _, limit_info = await self.check_rate_limit(api_key, endpoint)
            
            return {
                "X-RateLimit-Limit": str(limit_info.get("limit", "")),
                "X-RateLimit-Remaining": str(limit_info.get("remaining", "")),
                "X-RateLimit-Reset": str(limit_info.get("reset", ""))
            }
        except Exception as e:
            logger.error(f"Error generating rate limit headers: {e}")
            return {}

class RateLimitMiddleware:
    """FastAPI middleware for rate limiting."""
    
    def __init__(self, redis_url: str, config_path: str = "config/default.yml"):
        self.rate_limiter = RateLimiter(redis_url, config_path)
        
    async def __call__(self, request: Request, call_next):
        """Process request with rate limiting."""
        try:
            # Initialize rate limiter if needed
            if not self.rate_limiter.redis:
                await self.rate_limiter.initialize()
                
            # Extract API key from request
            api_key = request.headers.get("X-API-Key")
            if not api_key:
                raise HTTPException(status_code=401, detail="API key required")
                
            # Get endpoint path for rate limiting
            endpoint = request.url.path
            
            # Check rate limit
            is_allowed, limit_info = await self.rate_limiter.check_rate_limit(
                api_key, endpoint
            )
            
            if not is_allowed:
                raise HTTPException(
                    status_code=429,
                    detail="Rate limit exceeded",
                    headers={"Retry-After": str(limit_info.get("reset", 60))}
                )
                
            # Process request
            response = await call_next(request)
            
            # Add rate limit headers
            headers = await self.rate_limiter.get_rate_limit_headers(
                api_key, endpoint
            )
            response.headers.update(headers)
            
            return response
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in rate limit middleware: {e}")
            return await call_next(request)
            
    async def close(self):
        """Cleanup resources."""
        await self.rate_limiter.close()

# Example usage and utility functions
def create_rate_limit_middleware(app, redis_url: str, config_path: str = "config/default.yml"):
    """Create and configure rate limit middleware for FastAPI app."""
    middleware = RateLimitMiddleware(redis_url, config_path)
    
    @app.on_event("startup")
    async def startup():
        await middleware.rate_limiter.initialize()
        
    @app.on_event("shutdown")
    async def shutdown():
        await middleware.close()
        
    app.middleware("http")(middleware)
    
# CLI utility for managing rate limits
async def manage_rate_limits(
    redis_url: str,
    action: str,
    api_key: str,
    tier: str = None,
    config_path: str = "config/default.yml"
):
    """CLI utility for managing API rate limits."""
    rate_limiter = RateLimiter(redis_url, config_path)
    
    try:
        await rate_limiter.initialize()
        
        if action == "set_tier":
            if not tier:
                raise ValueError("Tier required for set_tier action")
            await rate_limiter.redis.set(f"tier:{api_key}", tier)
            print(f"Set tier {tier} for API key {api_key}")
            
        elif action == "get_tier":
            tier = await rate_limiter.redis.get(f"tier:{api_key}")
            print(f"API key {api_key} is in tier: {tier or 'basic'}")
            
        elif action == "reset":
            pattern = f"bucket:{api_key}:*"
            keys = await rate_limiter.redis.keys(pattern)
            if keys:
                await rate_limiter.redis.delete(*keys)
            print(f"Reset rate limits for API key {api_key}")
            
        else:
            print(f"Unknown action: {action}")
            
    finally:
        await rate_limiter.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Manage API rate limits")
    parser.add_argument("--redis-url", default="redis://localhost:6379/0",
                       help="Redis connection URL")
    parser.add_argument("--config", default="config/default.yml",
                       help="Path to config file")
    parser.add_argument("action", choices=["set_tier", "get_tier", "reset"],
                       help="Action to perform")
    parser.add_argument("--api-key", required=True,
                       help="API key to manage")
    parser.add_argument("--tier",
                       help="Tier for set_tier action")
                       
    args = parser.parse_args()
    
    asyncio.run(manage_rate_limits(
        args.redis_url,
        args.action,
        args.api_key,
        args.tier,
        args.config
    ))