"""
Crypto Anomaly Detection Engine System (CADES)
LSTM Volatility Predictor Module

This module implements advanced volatility prediction using LSTM neural networks,
combining on-chain data, sentiment analysis, and whale activity patterns.

Author: CADES Team
License: Proprietary
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union
import logging
from dataclasses import dataclass
import json

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from sklearn.preprocessing import MinMaxScaler
from scipy.stats import zscore

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class PredictionResult:
    """Results from volatility prediction"""
    timestamp: datetime
    predicted_volatility: float
    confidence_score: float
    contributing_factors: Dict[str, float]
    risk_level: str
    warning_signals: List[str]
    supporting_metrics: Dict[str, float]

class LSTMModel(nn.Module):
    """
    Multi-layer LSTM model for volatility prediction.
    Implements attention mechanism and residual connections.
    """
    
    def __init__(
        self,
        input_size: int,
        hidden_size: int,
        num_layers: int,
        output_size: int,
        dropout: float = 0.2
    ):
        """
        Initialize the LSTM model architecture.
        
        Args:
            input_size: Number of input features
            hidden_size: Number of hidden units in LSTM layers
            num_layers: Number of LSTM layers
            output_size: Number of output features
            dropout: Dropout rate for regularization
        """
        super(LSTMModel, self).__init__()
        
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        # LSTM layers with dropout
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            dropout=dropout,
            batch_first=True,
            bidirectional=True
        )
        
        # Attention mechanism
        self.attention = nn.Sequential(
            nn.Linear(hidden_size * 2, hidden_size),
            nn.Tanh(),
            nn.Linear(hidden_size, 1),
            nn.Softmax(dim=1)
        )
        
        # Output layers with residual connection
        self.fc1 = nn.Linear(hidden_size * 2, hidden_size)
        self.relu = nn.ReLU()
        self.dropout = nn.Dropout(dropout)
        self.fc2 = nn.Linear(hidden_size, output_size)
        
        # Layer normalization
        self.layer_norm = nn.LayerNorm(hidden_size)

    def forward(
        self,
        x: torch.Tensor,
        hidden: Optional[Tuple[torch.Tensor, torch.Tensor]] = None
    ) -> Tuple[torch.Tensor, Tuple[torch.Tensor, torch.Tensor]]:
        """
        Forward pass through the network.
        
        Args:
            x: Input tensor of shape (batch_size, sequence_length, input_size)
            hidden: Initial hidden state tuple (h0, c0)
            
        Returns:
            Tuple of (output, (hidden_state, cell_state))
        """
        # LSTM forward pass
        lstm_out, hidden = self.lstm(x, hidden)
        
        # Apply attention
        attention_weights = self.attention(lstm_out)
        attention_out = torch.sum(attention_weights * lstm_out, dim=1)
        
        # Residual connection and output layers
        out = self.fc1(attention_out)
        out = self.layer_norm(out)
        out = self.relu(out)
        out = self.dropout(out)
        
        # Final output
        predictions = self.fc2(out)
        
        return predictions, hidden

    def init_hidden(self, batch_size: int, device: torch.device) -> Tuple[torch.Tensor, torch.Tensor]:
        """Initialize hidden state."""
        return (
            torch.zeros(self.num_layers * 2, batch_size, self.hidden_size).to(device),
            torch.zeros(self.num_layers * 2, batch_size, self.hidden_size).to(device)
        )

class VolatilityDataset(Dataset):
    """Dataset class for volatility prediction."""
    
    def __init__(
        self,
        price_data: np.ndarray,
        sentiment_data: np.ndarray,
        whale_data: np.ndarray,
        sequence_length: int
    ):
        self.price_data = torch.FloatTensor(price_data)
        self.sentiment_data = torch.FloatTensor(sentiment_data)
        self.whale_data = torch.FloatTensor(whale_data)
        self.sequence_length = sequence_length

    def __len__(self) -> int:
        return len(self.price_data) - self.sequence_length

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        """Get sequence of data and target."""
        x_price = self.price_data[idx:idx + self.sequence_length]
        x_sentiment = self.sentiment_data[idx:idx + self.sequence_length]
        x_whale = self.whale_data[idx:idx + self.sequence_length]
        
        # Combine features
        x = torch.cat((x_price, x_sentiment, x_whale), dim=1)
        
        # Target is the next timeframe's volatility
        y = self.price_data[idx + self.sequence_length, 0]
        
        return x, y

class VolatilityPredictor:
    """
    Advanced volatility predictor using LSTM neural networks.
    Combines multiple data sources for accurate prediction.
    """
    
    def __init__(
        self,
        sequence_length: int = 100,
        prediction_window: int = 24,  # Hours
        update_interval: int = 300,  # 5 minutes
        confidence_threshold: float = 0.7
    ):
        """
        Initialize the volatility predictor.
        
        Args:
            sequence_length: Length of input sequences
            prediction_window: Future window to predict in hours
            update_interval: Update interval in seconds
            confidence_threshold: Minimum confidence for predictions
        """
        self.sequence_length = sequence_length
        self.prediction_window = prediction_window
        self.update_interval = update_interval
        self.confidence_threshold = confidence_threshold
        
        # Initialize scalers
        self.price_scaler = MinMaxScaler()
        self.sentiment_scaler = MinMaxScaler()
        self.whale_scaler = MinMaxScaler()
        
        # Initialize model
        self.model = LSTMModel(
            input_size=15,  # Combined features
            hidden_size=64,
            num_layers=2,
            output_size=1
        )
        
        # Initialize optimizer
        self.optimizer = optim.Adam(self.model.parameters())
        self.criterion = nn.MSELoss()
        
        # Data tracking
        self.prediction_history: List[PredictionResult] = []
        self.model_metrics = {
            'training_loss': [],
            'validation_loss': [],
            'prediction_accuracy': []
        }
        
        # Warning signals tracking
        self.active_warnings: Dict[str, List[str]] = defaultdict(list)

    async def update_prediction(
        self,
        price_data: pd.DataFrame,
        sentiment_data: pd.DataFrame,
        whale_data: pd.DataFrame
    ) -> PredictionResult:
        """
        Update volatility prediction with new data.
        
        Args:
            price_data: DataFrame with price and volume data
            sentiment_data: DataFrame with sentiment metrics
            whale_data: DataFrame with whale activity metrics
            
        Returns:
            Latest prediction result
        """
        try:
            # Preprocess data
            X_price = self._preprocess_price_data(price_data)
            X_sentiment = self._preprocess_sentiment_data(sentiment_data)
            X_whale = self._preprocess_whale_data(whale_data)
            
            # Combine features
            X_combined = np.concatenate((X_price, X_sentiment, X_whale), axis=1)
            
            # Make prediction
            prediction = self._make_prediction(X_combined)
            
            # Calculate confidence
            confidence = self._calculate_prediction_confidence(prediction, X_combined)
            
            # Analyze contributing factors
            factors = self._analyze_contributing_factors(X_combined)
            
            # Generate warning signals
            warnings = self._generate_warning_signals(prediction, factors)
            
            # Create prediction result
            result = PredictionResult(
                timestamp=datetime.now(),
                predicted_volatility=float(prediction),
                confidence_score=confidence,
                contributing_factors=factors,
                risk_level=self._calculate_risk_level(prediction, confidence),
                warning_signals=warnings,
                supporting_metrics=self._calculate_supporting_metrics(X_combined)
            )
            
            # Update tracking
            self.prediction_history.append(result)
            self._update_model_metrics(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error updating prediction: {e}")
            raise

    def _preprocess_price_data(self, price_data: pd.DataFrame) -> np.ndarray:
        """Preprocess price and volume data."""
        try:
            features = []
            
            # Calculate returns
            returns = price_data['price'].pct_change()
            
            # Calculate volatility
            volatility = returns.rolling(window=24).std()
            
            # Calculate volume metrics
            volume_ma = price_data['volume'].rolling(window=24).mean()
            volume_std = price_data['volume'].rolling(window=24).std()
            
            # Create feature matrix
            features.extend([
                returns,
                volatility,
                price_data['volume'] / volume_ma,
                zscore(volume_std)
            ])
            
            # Scale features
            features = np.column_stack(features)
            if not hasattr(self, 'price_scaler_fitted'):
                self.price_scaler.fit(features)
                self.price_scaler_fitted = True
                
            return self.price_scaler.transform(features)
            
        except Exception as e:
            logger.error(f"Error preprocessing price data: {e}")
            raise

    def _preprocess_sentiment_data(self, sentiment_data: pd.DataFrame) -> np.ndarray:
        """Preprocess sentiment metrics."""
        try:
            features = []
            
            # Calculate sentiment metrics
            sentiment_ma = sentiment_data['sentiment_score'].rolling(window=24).mean()
            sentiment_std = sentiment_data['sentiment_score'].rolling(window=24).std()
            
            # Calculate engagement metrics
            engagement_ma = sentiment_data['engagement_score'].rolling(window=24).mean()
            
            # Create feature matrix
            features.extend([
                sentiment_data['sentiment_score'],
                sentiment_ma,
                sentiment_std,
                sentiment_data['engagement_score'] / engagement_ma,
                sentiment_data['spam_probability']
            ])
            
            # Scale features
            features = np.column_stack(features)
            if not hasattr(self, 'sentiment_scaler_fitted'):
                self.sentiment_scaler.fit(features)
                self.sentiment_scaler_fitted = True
                
            return self.sentiment_scaler.transform(features)
            
        except Exception as e:
            logger.error(f"Error preprocessing sentiment data: {e}")
            raise

    def _preprocess_whale_data(self, whale_data: pd.DataFrame) -> np.ndarray:
        """Preprocess whale activity metrics."""
        try:
            features = []
            
            # Calculate whale metrics
            accumulation_ma = whale_data['accumulation_score'].rolling(window=24).mean()
            distribution_ma = whale_data['distribution_score'].rolling(window=24).mean()
            
            # Create feature matrix
            features.extend([
                whale_data['accumulation_score'] / accumulation_ma,
                whale_data['distribution_score'] / distribution_ma,
                whale_data['whale_count'],
                whale_data['avg_transaction_size'],
                whale_data['coordination_score']
            ])
            
            # Scale features
            features = np.column_stack(features)
            if not hasattr(self, 'whale_scaler_fitted'):
                self.whale_scaler.fit(features)
                self.whale_scaler_fitted = True
                
            return self.whale_scaler.transform(features)
            
        except Exception as e:
            logger.error(f"Error preprocessing whale data: {e}")
            raise

    def _make_prediction(self, X: np.ndarray) -> float:
        """Make volatility prediction."""
        try:
            # Prepare input sequence
            sequence = torch.FloatTensor(X[-self.sequence_length:]).unsqueeze(0)
            
            # Make prediction
            self.model.eval()
            with torch.no_grad():
                prediction, _ = self.model(sequence)
            
            return prediction.item()
            
        except Exception as e:
            logger.error(f"Error making prediction: {e}")
            raise

    def _calculate_prediction_confidence(
        self,
        prediction: float,
        features: np.ndarray
    ) -> float:
        """Calculate confidence score for prediction."""
        try:
            # Data quality factor
            data_quality = self._assess_data_quality(features)
            
            # Model uncertainty
            prediction_std = self._calculate_prediction_std(features)
            uncertainty_factor = 1 - min(1.0, prediction_std)
            
            # Historical accuracy
            historical_accuracy = self._calculate_historical_accuracy()
            
            # Combine factors
            confidence = (
                data_quality * 0.4 +
                uncertainty_factor * 0.3 +
                historical_accuracy * 0.3
            )
            
            return min(1.0, confidence)
            
        except Exception as e:
            logger.error(f"Error calculating prediction confidence: {e}")
            return 0.5

    def _analyze_contributing_factors(self, features: np.ndarray) -> Dict[str, float]:
        """Analyze factors contributing to prediction."""
        try:
            # Calculate feature importances
            importances = self._calculate_feature_importances(features)
            
            return {
                'price_volatility': importances[0],
                'volume_impact': importances[1],
                'sentiment_influence': importances[2],
                'whale_activity': importances[3],
                'market_momentum': importances[4]
            }
            
        except Exception as e:
            logger.error(f"Error analyzing contributing factors: {e}")
            return {}

    def _generate_warning_signals(
        self,
        prediction: float,
        factors: Dict[str, float]
    ) -> List[str]:
        """Generate warning signals based on prediction and factors."""
        warnings = []
        try:
            # Volatility warnings
            if prediction > 0.8:
                warnings.append("CRITICAL: Extreme volatility predicted")
            elif prediction > 0.6:
                warnings.append("HIGH: Significant volatility expected")
                
            # Factor-based warnings
            if factors['price_volatility'] > 0.7:
                warnings.append("Price volatility reaching critical levels")
                
            if factors['sentiment_influence'] > 0.7:
                warnings.append("Unusual social sentiment activity detected")
                
            if factors['whale_activity'] > 0.7:
                warnings.append("Significant whale movement detected")
                
            if factors['volume_impact'] > 0.7:
                warnings.append("Abnormal volume patterns observed")
                
            if factors['market_momentum'] > 0.7:
                warnings.append("Strong market momentum detected")
                
            return warnings
            
        except Exception as e:
            logger.error(f"Error generating warning signals: {e}")
            return ["Error generating warnings"]

    def _calculate_supporting_metrics(self, features: np.ndarray) -> Dict[str, float]:
        """Calculate additional supporting metrics for prediction."""
        try:
            # Calculate trend strength
            trend_strength = self._calculate_trend_strength(features)
            
            # Calculate market momentum
            momentum = self._calculate_market_momentum(features)
            
            # Calculate volume profile
            volume_profile = self._analyze_volume_profile(features)
            
            return {
                'trend_strength': trend_strength,
                'market_momentum': momentum,
                'volume_profile': volume_profile,
                'prediction_stability': self._calculate_prediction_stability(),
                'model_confidence': self._calculate_model_confidence()
            }
            
        except Exception as e:
            logger.error(f"Error calculating supporting metrics: {e}")
            return {}

    def _calculate_risk_level(self, prediction: float, confidence: float) -> str:
        """Calculate overall risk level."""
        try:
            # Weight prediction and confidence
            risk_score = prediction * 0.7 + (1 - confidence) * 0.3
            
            if risk_score >= 0.8:
                return "CRITICAL"
            elif risk_score >= 0.6:
                return "HIGH"
            elif risk_score >= 0.4:
                return "MEDIUM"
            else:
                return "LOW"
                
        except Exception as e:
            logger.error(f"Error calculating risk level: {e}")
            return "UNKNOWN"

    def _assess_data_quality(self, features: np.ndarray) -> float:
        """Assess quality of input data."""
        try:
            # Check for missing or invalid data
            valid_data_ratio = 1 - (np.isnan(features).sum() / features.size)
            
            # Check feature variance
            feature_variance = np.var(features, axis=0)
            variance_score = np.mean(feature_variance > 0.01)
            
            # Check for outliers
            z_scores = np.abs(zscore(features, nan_policy='omit'))
            outlier_ratio = 1 - (np.sum(z_scores > 3) / features.size)
            
            # Combine scores
            quality_score = (
                valid_data_ratio * 0.4 +
                variance_score * 0.3 +
                outlier_ratio * 0.3
            )
            
            return min(1.0, quality_score)
            
        except Exception as e:
            logger.error(f"Error assessing data quality: {e}")
            return 0.5

    def _calculate_feature_importances(self, features: np.ndarray) -> np.ndarray:
        """Calculate feature importance scores."""
        try:
            # Get feature correlations with target
            correlations = np.corrcoef(features.T)
            
            # Calculate importance based on correlation strength
            importances = np.abs(correlations[0, 1:])
            
            # Normalize importances
            importances = importances / np.sum(importances)
            
            return importances
            
        except Exception as e:
            logger.error(f"Error calculating feature importances: {e}")
            return np.zeros(features.shape[1])

    def _calculate_trend_strength(self, features: np.ndarray) -> float:
        """Calculate strength of current market trend."""
        try:
            # Use price features to calculate trend
            price_features = features[:, :4]  # First 4 features are price-related
            
            # Calculate trend direction consistency
            returns = np.diff(price_features[:, 0])
            consistency = np.sum(np.sign(returns[1:]) == np.sign(returns[:-1])) / len(returns)
            
            # Calculate trend magnitude
            magnitude = np.abs(np.mean(returns))
            
            # Combine metrics
            trend_strength = (consistency * 0.6 + magnitude * 0.4)
            
            return min(1.0, trend_strength)
            
        except Exception as e:
            logger.error(f"Error calculating trend strength: {e}")
            return 0.0

    def _calculate_market_momentum(self, features: np.ndarray) -> float:
        """Calculate market momentum indicator."""
        try:
            # Use recent price and volume features
            recent_features = features[-10:]
            
            # Calculate price momentum
            price_momentum = np.mean(np.diff(recent_features[:, 0]))
            
            # Calculate volume momentum
            volume_momentum = np.mean(np.diff(recent_features[:, 3]))
            
            # Combine with weights
            momentum = (
                np.abs(price_momentum) * 0.7 +
                np.abs(volume_momentum) * 0.3
            )
            
            return min(1.0, momentum)
            
        except Exception as e:
            logger.error(f"Error calculating market momentum: {e}")
            return 0.0

    def _analyze_volume_profile(self, features: np.ndarray) -> float:
        """Analyze volume profile for unusual patterns."""
        try:
            # Get volume features
            volume_features = features[:, 3:5]  # Volume-related features
            
            # Calculate volume concentration
            volume_mean = np.mean(volume_features[:, 0])
            volume_std = np.std(volume_features[:, 0])
            
            # Calculate abnormality score
            abnormality = np.sum(np.abs(volume_features[:, 0] - volume_mean) > 2 * volume_std)
            abnormality_score = abnormality / len(volume_features)
            
            return min(1.0, abnormality_score)
            
        except Exception as e:
            logger.error(f"Error analyzing volume profile: {e}")
            return 0.0

    def _calculate_prediction_stability(self) -> float:
        """Calculate stability of recent predictions."""
        try:
            if len(self.prediction_history) < 10:
                return 0.5
                
            recent_predictions = [
                p.predicted_volatility 
                for p in self.prediction_history[-10:]
            ]
            
            # Calculate stability metrics
            prediction_std = np.std(recent_predictions)
            stability_score = 1 - min(1.0, prediction_std)
            
            return stability_score
            
        except Exception as e:
            logger.error(f"Error calculating prediction stability: {e}")
            return 0.5

    def _calculate_model_confidence(self) -> float:
        """Calculate overall model confidence based on recent performance."""
        try:
            if not self.model_metrics['prediction_accuracy']:
                return 0.5
                
            # Get recent accuracy metrics
            recent_accuracy = np.mean(self.model_metrics['prediction_accuracy'][-100:])
            
            # Get recent loss trends
            recent_loss = np.mean(self.model_metrics['validation_loss'][-100:])
            loss_trend = np.mean(np.diff(self.model_metrics['validation_loss'][-100:]))
            
            # Calculate confidence score
            confidence = (
                recent_accuracy * 0.5 +
                (1 - min(1.0, recent_loss)) * 0.3 +
                (1 - min(1.0, abs(loss_trend))) * 0.2
            )
            
            return confidence
            
        except Exception as e:
            logger.error(f"Error calculating model confidence: {e}")
            return 0.5

    def _update_model_metrics(self, prediction_result: PredictionResult) -> None:
        """Update model performance metrics."""
        try:
            # Update prediction accuracy
            if len(self.prediction_history) > 1:
                previous_prediction = self.prediction_history[-2]
                accuracy = self._calculate_prediction_accuracy(
                    previous_prediction,
                    prediction_result
                )
                self.model_metrics['prediction_accuracy'].append(accuracy)
            
            # Maintain history size
            max_history = 1000
            if len(self.model_metrics['prediction_accuracy']) > max_history:
                self.model_metrics['prediction_accuracy'] = \
                    self.model_metrics['prediction_accuracy'][-max_history:]
                    
        except Exception as e:
            logger.error(f"Error updating model metrics: {e}")

    def _calculate_prediction_accuracy(
        self,
        previous: PredictionResult,
        current: PredictionResult
    ) -> float:
        """Calculate accuracy of previous prediction."""
        try:
            predicted_volatility = previous.predicted_volatility
            actual_volatility = current.predicted_volatility  # Using current as proxy for actual
            
            # Calculate accuracy as inverse of relative error
            relative_error = abs(predicted_volatility - actual_volatility) / actual_volatility
            accuracy = max(0, 1 - relative_error)
            
            return accuracy
            
        except Exception as e:
            logger.error(f"Error calculating prediction accuracy: {e}")
            return 0.0

    def get_prediction_insights(self) -> Dict:
        """Get comprehensive insights from recent predictions."""
        try:
            if not self.prediction_history:
                return {"error": "No prediction history available"}
            
            recent_predictions = self.prediction_history[-100:]
            
            return {
                "current_prediction": recent_predictions[-1].__dict__,
                "prediction_trend": self._analyze_prediction_trend(recent_predictions),
                "risk_metrics": {
                    "current_risk": self._calculate_risk_level(
                        recent_predictions[-1].predicted_volatility,
                        recent_predictions[-1].confidence_score
                    ),
                    "risk_trend": self._analyze_risk_trend(recent_predictions)
                },
                "performance_metrics": {
                    "prediction_accuracy": np.mean(self.model_metrics['prediction_accuracy'][-100:]),
                    "model_confidence": self._calculate_model_confidence()
                },
                "active_warnings": self.active_warnings
            }
            
        except Exception as e:
            logger.error(f"Error getting prediction insights: {e}")
            return {"error": str(e)}

    def _analyze_prediction_trend(self, predictions: List[PredictionResult]) -> Dict:
        """Analyze trend in recent predictions."""
        try:
            volatility_values = [p.predicted_volatility for p in predictions]
            confidence_values = [p.confidence_score for p in predictions]
            
            return {
                "volatility_trend": np.polyfit(range(len(volatility_values)), volatility_values, 1)[0],
                "confidence_trend": np.polyfit(range(len(confidence_values)), confidence_values, 1)[0],
                "trend_stability": self._calculate_prediction_stability(),
                "trend_direction": "increasing" if volatility_values[-1] > volatility_values[0] else "decreasing"
            }
            
        except Exception as e:
            logger.error(f"Error analyzing prediction trend: {e}")
            return {}

    def _analyze_risk_trend(self, predictions: List[PredictionResult]) -> Dict:
        """Analyze trend in risk levels."""
        try:
            risk_values = [
                1.0 if p.risk_level == "CRITICAL" else
                0.75 if p.risk_level == "HIGH" else
                0.5 if p.risk_level == "MEDIUM" else
                0.25
                for p in predictions
            ]
            
            return {
                "risk_trend": np.polyfit(range(len(risk_values)), risk_values, 1)[0],
                "risk_stability": 1 - np.std(risk_values),
                "risk_direction": "increasing" if risk_values[-1] > risk_values[0] else "decreasing",
                "risk_acceleration": np.diff(risk_values, 2).mean()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing risk trend: {e}")
            return {}

if __name__ == "__main__":
    # Example usage
    async def main():
        predictor = VolatilityPredictor(
            sequence_length=100,
            prediction_window=24,
            update_interval=300,
            confidence_threshold=0.7
        )
        
        # Example data (in practice, this would come from other modules)
        price_data = pd.DataFrame({
            'price': np.random.randn(1000).cumsum(),
            'volume': np.random.rand(1000) * 1000
        })
        
        sentiment_data = pd.DataFrame({
            'sentiment_score': np.random.randn(1000),
            'engagement_score': np.random.rand(1000),
            'spam_probability': np.random.rand(1000)
        })
        
        whale_data = pd.DataFrame({
            'accumulation_score': np.random.rand(1000),
            'distribution_score': np.random.rand(1000),
            'whale_count': np.random.randint(0, 100, 1000),
            'avg_transaction_size': np.random.rand(1000) * 10000,
            'coordination_score': np.random.rand(1000)
        })
        
        # Make prediction
        prediction = await predictor.update_prediction(
            price_data,
            sentiment_data,
            whale_data
        )
        
        print(f"Predicted Volatility: {prediction.predicted_volatility:.2f}")
        print(f"Confidence Score: {prediction.confidence_score:.2f}")
        print(f"Risk Level: {prediction.risk_level}")
        print("Warning Signals:", prediction.warning_signals)
        
    asyncio.run(main())