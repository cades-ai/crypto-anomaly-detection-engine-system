# CADE API Endpoints Documentation

## Overview
This document describes the available endpoints in the Crypto Anomaly Detection Engine System (CADES) API. All endpoints require API key authentication via the `X-API-Key` header.

## Base URL
```
https://api.cades.io/v1
```

## Authentication
All requests must include an API key in the header:
```
X-API-Key: your-api-key
```

## Rate Limits
- Standard tier: 60 requests per minute
- Premium tier: 300 requests per minute
- Enterprise tier: Custom limits

## Endpoints

### Health Check
```http
GET /health
```
Returns the current status of the API.

#### Response
```json
{
    "status": "operational",
    "timestamp": "2024-01-07T12:00:00Z",
    "version": "1.0.0"
}
```

### Token Analysis
```http
GET /token/{token_address}/analysis
```
Get comprehensive analysis for a specific token.

#### Parameters
- `token_address` (path) - Solana token address
- `timeframe` (query) - Analysis timeframe (1h, 24h, 7d) [default: 24h]

#### Response
```json
{
    "risk_score": 0.75,
    "anomalies": [
        {
            "type": "whale_movement",
            "severity": 0.8,
            "timestamp": "2024-01-07T11:30:00Z",
            "details": {
                "wallet_address": "...",
                "amount": 100000,
                "usd_value": 50000
            }
        }
    ],
    "metrics": {
        "price_change": -5.2,
        "volume_change": 150.3,
        "liquidity_score": 0.65
    }
}
```

### Track Token
```http
POST /token/track
```
Start tracking a token for anomaly detection.

#### Request Body
```json
{
    "token_address": "token_address",
    "tracking_parameters": {
        "alert_threshold": 0.7,
        "update_interval": 60
    }
}
```

#### Response
```json
{
    "status": "tracking_initiated",
    "token_address": "token_address"
}
```

### Get Anomalies
```http
GET /anomalies
```
Retrieve detected anomalies within a specified timeframe.

#### Parameters
- `start_time` (query) - Start time for anomaly search
- `end_time` (query) - End time for anomaly search
- `min_risk_score` (query) - Minimum risk score [0-1, default: 0.7]
- `limit` (query) - Maximum number of results [1-1000, default: 100]

#### Response
```json
{
    "anomalies": [
        {
            "token_address": "...",
            "risk_score": 0.85,
            "anomaly_type": "liquidity_removal",
            "timestamp": "2024-01-07T10:15:00Z",
            "details": {
                "previous_liquidity": 1000000,
                "current_liquidity": 500000,
                "change_percentage": -50
            }
        }
    ],
    "total_count": 1
}
```

### Sentiment Analysis
```http
GET /analytics/sentiment/{token_address}
```
Get social sentiment analysis for a token.

#### Parameters
- `token_address` (path) - Token address to analyze
- `timeframe` (query) - Analysis timeframe (1h, 24h, 7d) [default: 24h]

#### Response
```json
{
    "overall_sentiment": 0.65,
    "sentiment_breakdown": {
        "positive": 0.7,
        "neutral": 0.2,
        "negative": 0.1
    },
    "social_metrics": {
        "total_mentions": 1500,
        "engagement_rate": 0.08,
        "trending_hashtags": ["solana", "memecoin"]
    }
}
```

### Price Prediction
```http
GET /analytics/prediction/{token_address}
```
Get price prediction analysis for a token.

#### Parameters
- `token_address` (path) - Token address
- `prediction_window` (query) - Hours ahead to predict [1-168, default: 24]

#### Response
```json
{
    "predictions": [
        {
            "timestamp": "2024-01-07T13:00:00Z",
            "predicted_price": 1.25,
            "confidence": 0.85
        }
    ],
    "model_metrics": {
        "accuracy": 0.82,
        "volatility_index": 0.45
    }
}
```

### Custom Analysis
```http
POST /analytics/custom
```
Run custom analysis with specified metrics.

#### Request Body
```json
{
    "token_address": "token_address",
    "metrics": ["price_impact", "whale_concentration", "liquidity_depth"],
    "timeframe": "24h"
}
```

#### Response
```json
{
    "price_impact": 0.35,
    "whale_concentration": 0.65,
    "liquidity_depth": 0.8,
    "analysis_timestamp": "2024-01-07T12:00:00Z"
}
```

## WebSocket API

### Connect
```
ws://api.cade.io/v1/ws
```

#### Authentication
Include API key in connection URL:
```
ws://api.cade.io/v1/ws?api_key=your-api-key
```

#### Message Format
```json
{
    "type": "anomaly_alert",
    "data": {
        "token_address": "...",
        "risk_score": 0.85,
        "anomaly_type": "whale_movement",
        "timestamp": "2024-01-07T12:00:00Z",
        "details": {
            "wallet_address": "...",
            "amount": 500000,
            "usd_value": 250000
        }
    }
}
```

## Error Responses

### Common Error Codes
- 400: Bad Request
- 401: Unauthorized
- 403: Forbidden
- 429: Too Many Requests
- 500: Internal Server Error

### Error Response Format
```json
{
    "error": {
        "code": "rate_limit_exceeded",
        "message": "Rate limit exceeded",
        "details": {
            "limit": 60,
            "reset_at": "2024-01-07T12:01:00Z"
        }
    }
}
```
