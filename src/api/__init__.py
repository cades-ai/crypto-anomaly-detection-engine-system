"""Crypto Anomaly Detection Engine (CADE)

API Module

This module implements the REST API and WebSocket interfaces for the CADE system,
providing real-time access to analysis and detection capabilities.

Author: CADE Team
License: Proprietary"""

from .routes import app
from .middleware import SecurityMiddleware, RateLimiter
from .websocket import WSManager

__version__ = '1.0.0'
__author__ = 'CADE Team'
__email__ = 'contact@cadesol.ai'

__all__ = [
    'app',
    'SecurityMiddleware',
    'RateLimiter',
    'WSManager',
]

# API configuration
API_CONFIG = {
    'version': 'v1',
    'prefix': '/api/v1',
    'rate_limit': 100,  # requests per minute
    'ws_max_clients': 1000,
}

# Security settings
SECURITY_CONFIG = {
    'jwt_expiration': 3600,  # 1 hour
    'refresh_expiration': 86400,  # 24 hours
    'require_api_key': True,
    'cors_origins': [
        'https://app.cadesol.ai',
        'https://api.cadesol.ai'
    ]
}

# WebSocket configuration
WS_CONFIG = {
    'ping_interval': 30,
    'ping_timeout': 10,
    'max_message_size': 1024 * 1024,  # 1MB
    'compression': True
}
