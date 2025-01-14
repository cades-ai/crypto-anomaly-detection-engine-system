"""
Crypto Anomaly Detection Engine System(CADES)
API Routes Module

This module implements the REST API endpoints for the CADES system.
Provides access to analysis, metrics, and monitoring functionality.

Author: CADES Team
License: Proprietary
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional
import logging
from datetime import datetime
import asyncio
import aiohttp
import json
from web3 import Web3
from redis import Redis
import numpy as np
from sklearn.preprocessing import StandardScaler
from textblob import TextBlob

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize connections
redis_client = Redis(host='localhost', port=6379, db=0)
w3 = Web3(Web3.HTTPProvider('https://api.mainnet.solana.com'))

app = FastAPI(title="CADES API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response Models
class TokenAnalysisRequest(BaseModel):
    token_address: str
    timeframe: Optional[int] = 3600  # 1 hour default

class AnalysisResponse(BaseModel):
    token_address: str
    timestamp: datetime
    metrics: Dict
    risk_assessment: Dict
    alerts: List[Dict]

class MonitoringRequest(BaseModel):
    token_addresses: List[str]
    update_interval: Optional[int] = 60

class IndexRequest(BaseModel):
    name: str
    token_addresses: Optional[List[str]] = None
    max_components: Optional[int] = 10

# API Endpoints
@app.get("/")
async def root():
    """API root endpoint."""
    return {
        "name": "CADES API",
        "version": "1.0.0",
        "status": "operational"
    }

@app.post("/analyze")
async def analyze_token(
    request: TokenAnalysisRequest,
    background_tasks: BackgroundTasks
):
    """Analyze a specific token."""
    try:
        # Start analysis tasks
        background_tasks.add_task(
            _update_analysis_cache,
            request.token_address
        )
        
        # Get chain analysis
        chain_data = await _get_chain_analysis(
            request.token_address,
            request.timeframe
        )
        
        # Get sentiment analysis
        sentiment_data = await _get_sentiment_analysis(
            request.token_address,
            request.timeframe
        )
        
        # Get market analysis
        market_data = await _get_market_analysis(
            request.token_address,
            request.timeframe
        )
        
        # Calculate metrics and risks
        metrics = await _calculate_metrics(
            chain_data,
            sentiment_data,
            market_data
        )
        
        risk_assessment = await _assess_risks(
            metrics,
            market_data
        )
        
        # Get any active alerts
        alerts = await _get_active_alerts(
            request.token_address
        )
        
        return AnalysisResponse(
            token_address=request.token_address,
            timestamp=datetime.now(),
            metrics=metrics,
            risk_assessment=risk_assessment,
            alerts=alerts
        )
        
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/monitor")
async def monitor_tokens(request: MonitoringRequest):
    """Start monitoring tokens."""
    try:
        # Validate tokens
        valid_tokens = await _validate_tokens(request.token_addresses)
        if not valid_tokens:
            raise HTTPException(
                status_code=400,
                detail="No valid tokens provided"
            )
        
        # Start monitoring tasks
        monitoring_tasks = await _start_monitoring(
            valid_tokens,
            request.update_interval
        )
        
        return {
            "status": "monitoring_started",
            "tokens": valid_tokens,
            "task_ids": monitoring_tasks
        }
        
    except Exception as e:
        logger.error(f"Monitoring error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Utility functions
async def _update_analysis_cache(token_address: str):
    """Update analysis cache for token."""
    try:
        # Get latest data
        chain_data = await _get_chain_analysis(token_address, 3600)
        sentiment_data = await _get_sentiment_analysis(token_address, 3600)
        market_data = await _get_market_analysis(token_address, 3600)
        
        # Combine data
        cache_data = {
            "chain_data": chain_data,
            "sentiment_data": sentiment_data,
            "market_data": market_data,
            "timestamp": datetime.now().timestamp()
        }
        
        # Store in Redis with 1-hour expiry
        redis_client.setex(
            f"analysis_cache:{token_address}",
            3600,
            json.dumps(cache_data)
        )
        
    except Exception as e:
        logger.error(f"Cache update error: {e}")

async def _get_chain_analysis(
    token_address: str,
    timeframe: int
) -> Dict:
    """Get chain analysis data."""
    try:
        # Get recent transactions
        transactions = await _fetch_token_transactions(token_address, timeframe)
        
        # Analyze transaction patterns
        volume_data = _analyze_volume_patterns(transactions)
        whale_data = _analyze_whale_movements(transactions)
        liquidity_data = _analyze_liquidity_changes(transactions)
        
        # Detect anomalies
        anomalies = _detect_transaction_anomalies(transactions)
        
        return {
            "volume_metrics": volume_data,
            "whale_activity": whale_data,
            "liquidity_metrics": liquidity_data,
            "detected_anomalies": anomalies,
            "transaction_count": len(transactions)
        }
        
    except Exception as e:
        logger.error(f"Chain analysis error: {e}")
        return {}

async def _get_sentiment_analysis(
    token_address: str,
    timeframe: int
) -> Dict:
    """Get sentiment analysis data."""
    try:
        # Fetch social media data
        twitter_data = await _fetch_twitter_data(token_address, timeframe)
        telegram_data = await _fetch_telegram_data(token_address, timeframe)
        
        # Analyze sentiment
        twitter_sentiment = _analyze_sentiment(twitter_data)
        telegram_sentiment = _analyze_sentiment(telegram_data)
        
        # Calculate engagement metrics
        engagement = _calculate_engagement_metrics(twitter_data, telegram_data)
        
        # Detect sentiment anomalies
        anomalies = _detect_sentiment_anomalies(
            twitter_sentiment,
            telegram_sentiment
        )
        
        return {
            "twitter_metrics": twitter_sentiment,
            "telegram_metrics": telegram_sentiment,
            "engagement_stats": engagement,
            "sentiment_anomalies": anomalies
        }
        
    except Exception as e:
        logger.error(f"Sentiment analysis error: {e}")
        return {}

async def _get_market_analysis(
    token_address: str,
    timeframe: int
) -> Dict:
    """Get market analysis data."""
    try:
        # Fetch market data
        price_data = await _fetch_price_data(token_address, timeframe)
        volume_data = await _fetch_volume_data(token_address, timeframe)
        
        # Calculate market metrics
        volatility = _calculate_volatility(price_data)
        momentum = _calculate_momentum(price_data)
        liquidity = _calculate_liquidity_metrics(volume_data)
        
        # Detect market anomalies
        anomalies = _detect_market_anomalies(price_data, volume_data)
        
        return {
            "price_metrics": {
                "volatility": volatility,
                "momentum": momentum
            },
            "volume_metrics": liquidity,
            "detected_anomalies": anomalies
        }
        
    except Exception as e:
        logger.error(f"Market analysis error: {e}")
        return {}

async def _calculate_metrics(
    chain_data: Dict,
    sentiment_data: Dict,
    market_data: Dict
) -> Dict:
    """Calculate combined metrics."""
    try:
        metrics = {
            "chain_metrics": {
                "transaction_volume": chain_data.get("volume_metrics", {}),
                "whale_activity": chain_data.get("whale_activity", {}),
                "liquidity_score": chain_data.get("liquidity_metrics", {})
            },
            "sentiment_metrics": {
                "overall_sentiment": _combine_sentiment_scores(
                    sentiment_data.get("twitter_metrics", {}),
                    sentiment_data.get("telegram_metrics", {})
                ),
                "engagement_score": sentiment_data.get("engagement_stats", {})
            },
            "market_metrics": {
                "price_volatility": market_data.get("price_metrics", {}).get("volatility", 0),
                "market_momentum": market_data.get("price_metrics", {}).get("momentum", 0),
                "liquidity_depth": market_data.get("volume_metrics", {})
            }
        }
        
        return metrics
        
    except Exception as e:
        logger.error(f"Metrics calculation error: {e}")
        return {}

async def _assess_risks(metrics: Dict, market_data: Dict) -> Dict:
    """Assess risks based on metrics."""
    try:
        # Calculate risk scores
        volatility_risk = _calculate_volatility_risk(
            metrics["market_metrics"]["price_volatility"]
        )
        
        liquidity_risk = _calculate_liquidity_risk(
            metrics["chain_metrics"]["liquidity_score"],
            metrics["market_metrics"]["liquidity_depth"]
        )
        
        whale_risk = _calculate_whale_risk(
            metrics["chain_metrics"]["whale_activity"]
        )
        
        sentiment_risk = _calculate_sentiment_risk(
            metrics["sentiment_metrics"]["overall_sentiment"]
        )
        
        # Combine risk scores
        overall_risk = _calculate_overall_risk([
            volatility_risk,
            liquidity_risk,
            whale_risk,
            sentiment_risk
        ])
        
        return {
            "overall_risk_score": overall_risk,
            "risk_components": {
                "volatility_risk": volatility_risk,
                "liquidity_risk": liquidity_risk,
                "whale_risk": whale_risk,
                "sentiment_risk": sentiment_risk
            },
            "risk_level": _get_risk_level(overall_risk)
        }
        
    except Exception as e:
        logger.error(f"Risk assessment error: {e}")
        return {}

async def _get_active_alerts(token_address: str) -> List[Dict]:
    """Get active alerts for token."""
    try:
        alerts = []
        
        # Check Redis for cached alerts
        cached_alerts = redis_client.get(f"alerts:{token_address}")
        if cached_alerts:
            return json.loads(cached_alerts)
        
        # Generate new alerts
        metrics = await _get_latest_metrics(token_address)
        if metrics:
            alerts.extend(_generate_metric_alerts(metrics))
        
        risk_assessment = await _assess_risks(metrics, {})
        if risk_assessment:
            alerts.extend(_generate_risk_alerts(risk_assessment))
        
        # Cache alerts
        redis_client.setex(
            f"alerts:{token_address}",
            300,  # 5 minute cache
            json.dumps(alerts)
        )
        
        return alerts
        
    except Exception as e:
        logger.error(f"Alerts error: {e}")
        return []

# Helper functions for data analysis
def _analyze_volume_patterns(transactions: List[Dict]) -> Dict:
    """Analyze transaction volume patterns."""
    volumes = [tx['amount'] for tx in transactions]
    return {
        "mean_volume": np.mean(volumes),
        "std_volume": np.std(volumes),
        "max_volume": max(volumes),
        "min_volume": min(volumes),
        "volume_trend": _calculate_trend(volumes)
    }

def _analyze_whale_movements(transactions: List[Dict]) -> Dict:
    """Analyze whale wallet movements."""
    whale_threshold = np.percentile([tx['amount'] for tx in transactions], 95)
    whale_txs = [tx for tx in transactions if tx['amount'] >= whale_threshold]
    
    return {
        "whale_transaction_count": len(whale_txs),
        "total_whale_volume": sum(tx['amount'] for tx in whale_txs),
        "unique_whale_wallets": len(set(tx['from'] for tx in whale_txs))
    }

def _analyze_sentiment(social_data: List[Dict]) -> Dict:
    """Analyze sentiment from social media data."""
    sentiments = []
    for post in social_data:
        blob = TextBlob(post['text'])
        sentiments.append(blob.sentiment.polarity)
    
    return {
        "mean_sentiment": np.mean(sentiments),
        "sentiment_std": np.std(sentiments),
        "sentiment_trend": _calculate_trend(sentiments)
    }

def _calculate_trend(data: List[float]) -> float:
    """Calculate trend from time series data."""
    if not data:
        return 0
    x = np.arange(len(data))
    z = np.polyfit(x, data, 1)
    return z[0]  # Return slope

def _calculate_overall_risk(risk_scores: List[float]) -> float:
    """Calculate overall risk score."""
    weights = [0.3, 0.25, 0.25, 0.2]  # Weights for different risk components
    return sum(score * weight for score, weight in zip(risk_scores, weights))

def _get_risk_level(risk_score: float) -> str:
    """Get risk level from risk score."""
    if risk_score >= 0.8:
        return "CRITICAL"
    elif risk_score >= 0.6:
        return "HIGH"
    elif risk_score >= 0.4:
        return "MEDIUM"
    elif risk_score >= 0.2:
        return "LOW"
    else:
        return "MINIMAL"

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)