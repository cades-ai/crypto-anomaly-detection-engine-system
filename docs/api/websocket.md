# WebSocket API Documentation

## Overview
The CADES WebSocket API provides real-time access to memecoin trading patterns, anomalies, and blockchain data. This interface enables instant notifications about detected patterns and market movements.

## Connection
```
wss://api.cades.io/v1/ws
```

### Authentication
Include your API key in the connection headers:
```
Authorization: Bearer YOUR_API_KEY
```

## Message Format
All messages follow a standard JSON format:

```json
{
  "type": "message_type",
  "data": {},
  "timestamp": "ISO8601_TIMESTAMP"
}
```

## Subscribe to Events
Send a subscription message to receive specific event types:

```json
{
  "type": "subscribe",
  "channels": [
    "patterns",
    "whale_movements",
    "anomalies"
  ]
}
```

### Available Channels
- `patterns`: All detected trading patterns
- `whale_movements`: Large token transfers and accumulation
- `anomalies`: Unusual market behavior
- `liquidityChanges`: Pool liquidity updates
- `wash_trading`: Potential wash trading detection
- `cyclic_transfers`: Cyclic transaction patterns

## Event Types

### Pattern Detection Event
```json
{
  "type": "pattern",
  "data": {
    "pattern_type": "wash_trading",
    "confidence": 0.95,
    "addresses": ["address1", "address2"],
    "transactions": ["tx1", "tx2"],
    "risk_score": 0.85
  }
}
```

### Whale Movement Event
```json
{
  "type": "whale_movement",
  "data": {
    "amount": "1000000",
    "token": "TOKEN_SYMBOL",
    "from": "address1",
    "to": "address2",
    "usd_value": 150000
  }
}
```

### Anomaly Event
```json
{
  "type": "anomaly",
  "data": {
    "type": "price_spike",
    "severity": "high",
    "details": {
      "token": "TOKEN_SYMBOL",
      "change_percent": 35.5,
      "time_period": "5m"
    }
  }
}
```

## Error Messages
```json
{
  "type": "error",
  "data": {
    "code": "ERROR_CODE",
    "message": "Error description"
  }
}
```

### Error Codes
- `1001`: Authentication failed
- `1002`: Invalid subscription
- `1003`: Rate limit exceeded
- `1004`: Invalid message format
- `1005`: Server error

## Rate Limits
- Maximum 100 subscriptions per connection
- Maximum 1000 messages per minute
- Maximum 10 concurrent connections per API key

## Best Practices
1. Implement exponential backoff for reconnections
2. Handle connection drops gracefully
3. Process messages asynchronously
4. Maintain heartbeat responses
5. Monitor subscription status

## Example Implementation

```javascript
const ws = new WebSocket('wss://api.cades.io/v1/ws');

ws.onopen = () => {
  // Subscribe to channels
  ws.send(JSON.stringify({
    type: 'subscribe',
    channels: ['patterns', 'whale_movements']
  }));
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  switch(message.type) {
    case 'pattern':
      handlePattern(message.data);
      break;
    case 'whale_movement':
      handleWhaleMovement(message.data);
      break;
    case 'error':
      handleError(message.data);
      break;
  }
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

ws.onclose = () => {
  // Implement reconnection logic
  setTimeout(connectWebSocket, 5000);
};
```

## Support
For additional support or questions:
- Email: support@cades.io