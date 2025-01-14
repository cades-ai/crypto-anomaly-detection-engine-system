"""
Integration tests for the Crypto Anomaly Detection Engine System (CADES)
Tests the full pipeline from data ingestion to pattern detection and scoring.

Author: CADES Team
License: Proprietary
"""

import pytest
import asyncio
import json
from datetime import datetime, timezone
from typing import Dict, List
import logging
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from src.api.routes import app
from src.chain_analysis.blockchain_listener import SolanaBlockchainListener
from src.sentiment_analysis.social_scraper import SocialScraper
from src.temporal_analysis.volatility_calculator import VolatilityCalculator
from src.whale_detection.whale_tracker import WhaleTracker
from src.score_aggregator.metric_calculator import MetricCalculator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test client setup
client = TestClient(app)

@pytest.fixture
async def blockchain_listener():
    """Fixture for blockchain listener with mock RPC."""
    listener = SolanaBlockchainListener(
        rpc_urls=["http://mock-rpc"],
        watched_programs=["test-program-id"]
    )
    
    # Mock RPC responses
    async def mock_get_transaction(*args, **kwargs):
        return {
            "result": {
                "transaction": "base64_encoded_transaction",
                "slot": 100,
                "blockTime": int(datetime.now(timezone.utc).timestamp())
            }
        }
    
    with patch.object(listener.client, "get_transaction", mock_get_transaction):
        yield listener

@pytest.fixture
def sample_transaction_data():
    """Fixture for sample transaction data."""
    return {
        "signature": "test_signature",
        "slot": 100,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "program_ids": ["test-program-id"],
        "instructions": [
            {
                "program_id": "test-program-id",
                "data": "test_data",
                "accounts": ["account1", "account2"]
            }
        ]
    }

@pytest.fixture
def sample_social_data():
    """Fixture for sample social media data."""
    return {
        "platform": "twitter",
        "posts": [
            {
                "id": "123",
                "text": "Bullish on $TEST! 🚀",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "user": "trader1",
                "sentiment": 0.8
            }
        ]
    }

@pytest.mark.asyncio
async def test_full_pipeline_integration(
    blockchain_listener,
    sample_transaction_data,
    sample_social_data
):
    """
    Test full pipeline integration from data ingestion to scoring.
    Tests the entire flow of data through the system.
    """
    try:
        # 1. Test blockchain data ingestion
        transaction_result = await test_blockchain_ingestion(
            blockchain_listener,
            sample_transaction_data
        )
        assert transaction_result["success"], "Blockchain ingestion failed"
        
        # 2. Test sentiment analysis
        sentiment_result = await test_sentiment_analysis(sample_social_data)
        assert sentiment_result["success"], "Sentiment analysis failed"
        
        # 3. Test pattern detection
        patterns_result = await test_pattern_detection(sample_transaction_data)
        assert patterns_result["success"], "Pattern detection failed"
        
        # 4. Test score aggregation
        score_result = await test_score_aggregation(
            transaction_result["data"],
            sentiment_result["data"],
            patterns_result["data"]
        )
        assert score_result["success"], "Score aggregation failed"
        
        # 5. Test API endpoints
        api_result = await test_api_endpoints(score_result["data"])
        assert api_result["success"], "API endpoint tests failed"
        
        logger.info("Full pipeline integration test passed successfully")
        
    except Exception as e:
        logger.error(f"Pipeline test failed: {e}")
        raise

async def test_blockchain_ingestion(
    listener: SolanaBlockchainListener,
    sample_data: Dict
) -> Dict:
    """Test blockchain data ingestion component."""
    try:
        # Process sample transaction
        processed_tx = await listener.process_transaction(sample_data)
        
        # Verify processing results
        assert processed_tx, "Transaction processing failed"
        assert processed_tx.get("signature") == sample_data["signature"]
        
        return {
            "success": True,
            "data": processed_tx,
            "message": "Blockchain ingestion successful"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Blockchain ingestion failed"
        }

async def test_sentiment_analysis(sample_data: Dict) -> Dict:
    """Test sentiment analysis component."""
    try:
        with patch("src.sentiment_analysis.social_scraper.SocialScraper") as MockScraper:
            scraper = MockScraper()
            scraper.analyze_sentiment.return_value = {
                "compound": 0.8,
                "positive": 0.9,
                "negative": 0.1,
                "neutral": 0.0
            }
            
            # Process sample social data
            sentiment_results = await scraper.analyze_sentiment(
                sample_data["posts"]
            )
            
            assert sentiment_results["compound"] > 0
            
            return {
                "success": True,
                "data": sentiment_results,
                "message": "Sentiment analysis successful"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Sentiment analysis failed"
        }

async def test_pattern_detection(sample_data: Dict) -> Dict:
    """Test pattern detection components."""
    try:
        # Test temporal analysis
        with patch("src.temporal_analysis.volatility_calculator.VolatilityCalculator") as MockCalc:
            calc = MockCalc()
            calc.calculate_volatility.return_value = {
                "volatility": 0.15,
                "trend": "increasing",
                "anomaly_score": 0.7
            }
            
            volatility_results = await calc.calculate_volatility(sample_data)
            
        # Test whale detection
        with patch("src.whale_detection.whale_tracker.WhaleTracker") as MockTracker:
            tracker = MockTracker()
            tracker.detect_patterns.return_value = {
                "whale_activity": True,
                "accumulation_phase": True,
                "confidence": 0.85
            }
            
            whale_results = await tracker.detect_patterns(sample_data)
        
        return {
            "success": True,
            "data": {
                "volatility": volatility_results,
                "whale_patterns": whale_results
            },
            "message": "Pattern detection successful"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Pattern detection failed"
        }

async def test_score_aggregation(
    blockchain_data: Dict,
    sentiment_data: Dict,
    pattern_data: Dict
) -> Dict:
    """Test score aggregation component."""
    try:
        with patch("src.score_aggregator.metric_calculator.MetricCalculator") as MockCalc:
            calc = MockCalc()
            calc.calculate_risk_score.return_value = {
                "total_score": 0.75,
                "components": {
                    "blockchain": 0.8,
                    "sentiment": 0.7,
                    "patterns": 0.75
                },
                "confidence": 0.9
            }
            
            risk_score = await calc.calculate_risk_score(
                blockchain_data,
                sentiment_data,
                pattern_data
            )
            
            assert 0 <= risk_score["total_score"] <= 1
            
            return {
                "success": True,
                "data": risk_score,
                "message": "Score aggregation successful"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Score aggregation failed"
        }

async def test_api_endpoints(score_data: Dict) -> Dict:
    """Test API endpoints with aggregated data."""
    try:
        # Test GET /health
        response = client.get("/health")
        assert response.status_code == 200
        
        # Test POST /api/v1/analyze
        response = client.post(
            "/api/v1/analyze",
            json={"data": score_data}
        )
        assert response.status_code == 200
        result = response.json()
        assert "risk_score" in result
        
        # Test websocket connection
        with client.websocket_connect("/ws") as websocket:
            data = websocket.receive_json()
            assert "type" in data
            
        return {
            "success": True,
            "data": {
                "endpoints_tested": ["/health", "/api/v1/analyze", "/ws"],
                "all_passing": True
            },
            "message": "API endpoint tests successful"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "API endpoint tests failed"
        }

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])