"""
Crypto Anomaly Detection Engine (CADE)
Text Embedding Models Module

This module implements specialized text embedding models for crypto-related content,
optimizing for tokenomics, social media sentiment, and technical analysis language.

Author: CADE Team
License: Proprietary
"""

import torch
import torch.nn as nn
from transformers import AutoTokenizer, AutoModel
from typing import List, Dict, Optional, Union, Tuple
import numpy as np
from datetime import datetime
import logging
from dataclasses import dataclass
from collections import defaultdict
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class TextEmbedding:
    """Container for text embedding results"""
    text: str
    embedding: np.ndarray
    token_embeddings: Optional[np.ndarray]
    attention_weights: Optional[np.ndarray]
    metadata: Dict

class CryptoEmbeddingModel:
    """
    Specialized embedding model for crypto-related text.
    Implements attention-based token weighting and domain adaptation.
    """
    
    def __init__(
        self,
        model_name: str = "distilbert-base-uncased",
        embedding_dim: int = 768,
        max_length: int = 512,
        device: str = "cuda" if torch.cuda.is_available() else "cpu"
    ):
        """
        Initialize the embedding model.
        
        Args:
            model_name: Base transformer model to use
            embedding_dim: Dimension of embeddings
            max_length: Maximum sequence length
            device: Device to run model on
        """
        self.device = device
        self.embedding_dim = embedding_dim
        self.max_length = max_length
        
        # Initialize tokenizer and model
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.base_model = AutoModel.from_pretrained(model_name).to(device)
        
        # Initialize domain adaptation layer
        self.domain_adapter = nn.Sequential(
            nn.Linear(embedding_dim, embedding_dim),
            nn.LayerNorm(embedding_dim),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(embedding_dim, embedding_dim)
        ).to(device)
        
        # Token importance scoring
        self.token_scorer = nn.Sequential(
            nn.Linear(embedding_dim, 128),
            nn.ReLU(),
            nn.Linear(128, 1)
        ).to(device)
        
        # Initialize crypto-specific vocabulary
        self.crypto_vocab = self._initialize_crypto_vocab()
        
        # Tracking metrics
        self.embedding_cache = {}
        self.performance_metrics = defaultdict(list)

    def _initialize_crypto_vocab(self) -> Dict[str, float]:
        """Initialize crypto-specific vocabulary with importance weights."""
        return {
            # Token types
            "token": 1.2,
            "coin": 1.2,
            "memecoin": 1.3,
            
            # Actions
            "buy": 1.1,
            "sell": 1.1,
            "hold": 1.1,
            "moon": 1.2,
            "dump": 1.2,
            "pump": 1.2,
            
            # Technical terms
            "dex": 1.1,
            "liquidity": 1.1,
            "volume": 1.1,
            "marketcap": 1.1,
            "supply": 1.1,
            
            # Sentiment terms
            "bullish": 1.3,
            "bearish": 1.3,
            "fud": 1.2,
            "fomo": 1.2,
            
            # Platforms
            "solana": 1.2,
            "raydium": 1.1,
            "orca": 1.1,
            "jupiter": 1.1,
            
            # Meme-specific
            "wen": 1.3,
            "wagmi": 1.2,
            "gm": 1.1,
            "ngmi": 1.2,
            
            # Emojis
            "🚀": 1.3,
            "💎": 1.2,
            "🌙": 1.2,
            "🐻": 1.2,
            "🐂": 1.2
        }

    @torch.no_grad()
    def get_embedding(self, text: str) -> TextEmbedding:
        """
        Generate embedding for a text input.
        
        Args:
            text: Input text to embed
            
        Returns:
            TextEmbedding containing embeddings and metadata
        """
        try:
            # Check cache
            cache_key = hash(text)
            if cache_key in self.embedding_cache:
                return self.embedding_cache[cache_key]
            
            # Tokenize text
            inputs = self.tokenizer(
                text,
                max_length=self.max_length,
                padding=True,
                truncation=True,
                return_tensors="pt"
            ).to(self.device)
            
            # Get base embeddings
            outputs = self.base_model(**inputs)
            token_embeddings = outputs.last_hidden_state
            
            # Calculate token importance scores
            token_scores = self.token_scorer(token_embeddings).squeeze(-1)
            
            # Apply crypto-specific token weighting
            weighted_scores = self._apply_crypto_weights(
                token_scores,
                inputs['input_ids']
            )
            
            # Calculate attention weights
            attention_weights = torch.softmax(weighted_scores, dim=-1)
            
            # Get weighted embedding
            weighted_embedding = torch.sum(
                token_embeddings * attention_weights.unsqueeze(-1),
                dim=1
            )
            
            # Apply domain adaptation
            final_embedding = self.domain_adapter(weighted_embedding)
            
            # Create embedding result
            result = TextEmbedding(
                text=text,
                embedding=final_embedding.cpu().numpy(),
                token_embeddings=token_embeddings.cpu().numpy(),
                attention_weights=attention_weights.cpu().numpy(),
                metadata={
                    'timestamp': datetime.now().isoformat(),
                    'model_version': '1.0',
                    'text_length': len(text),
                    'token_count': inputs['input_ids'].size(1)
                }
            )
            
            # Update cache
            self.embedding_cache[cache_key] = result
            
            # Update metrics
            self._update_metrics('embedding_count')
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise

    def get_batch_embeddings(
        self,
        texts: List[str],
        batch_size: int = 32
    ) -> List[TextEmbedding]:
        """Generate embeddings for a batch of texts."""
        try:
            results = []
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                
                # Process batch
                batch_results = [self.get_embedding(text) for text in batch]
                results.extend(batch_results)
                
                # Update metrics
                self._update_metrics('batch_count')
                
            return results
            
        except Exception as e:
            logger.error(f"Error processing batch embeddings: {e}")
            raise

    def _apply_crypto_weights(
        self,
        token_scores: torch.Tensor,
        input_ids: torch.Tensor
    ) -> torch.Tensor:
        """Apply crypto-specific token weights to importance scores."""
        try:
            # Get token strings
            tokens = self.tokenizer.convert_ids_to_tokens(
                input_ids.squeeze().tolist()
            )
            
            # Calculate crypto weights
            crypto_weights = torch.ones_like(token_scores)
            for idx, token in enumerate(tokens):
                if token in self.crypto_vocab:
                    crypto_weights[0, idx] = self.crypto_vocab[token]
            
            # Apply weights
            weighted_scores = token_scores * crypto_weights
            
            return weighted_scores
            
        except Exception as e:
            logger.error(f"Error applying crypto weights: {e}")
            raise

    def calculate_similarity(
        self,
        embedding1: Union[TextEmbedding, np.ndarray],
        embedding2: Union[TextEmbedding, np.ndarray]
    ) -> float:
        """Calculate cosine similarity between embeddings."""
        try:
            # Extract numpy arrays if TextEmbedding objects
            if isinstance(embedding1, TextEmbedding):
                embedding1 = embedding1.embedding
            if isinstance(embedding2, TextEmbedding):
                embedding2 = embedding2.embedding
            
            # Ensure 2D arrays
            if embedding1.ndim == 1:
                embedding1 = embedding1.reshape(1, -1)
            if embedding2.ndim == 1:
                embedding2 = embedding2.reshape(1, -1)
            
            # Calculate cosine similarity
            similarity = np.dot(embedding1, embedding2.T) / (
                np.linalg.norm(embedding1) * np.linalg.norm(embedding2)
            )
            
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Error calculating similarity: {e}")
            raise

    def _update_metrics(self, metric_name: str) -> None:
        """Update performance metrics."""
        try:
            self.performance_metrics[metric_name].append(datetime.now())
            
            # Maintain last 1000 entries
            if len(self.performance_metrics[metric_name]) > 1000:
                self.performance_metrics[metric_name] = \
                    self.performance_metrics[metric_name][-1000:]
                    
        except Exception as e:
            logger.error(f"Error updating metrics: {e}")

    def get_performance_metrics(self) -> Dict:
        """Get current performance metrics."""
        try:
            return {
                'embedding_count': len(self.performance_metrics['embedding_count']),
                'batch_count': len(self.performance_metrics['batch_count']),
                'cache_size': len(self.embedding_cache),
                'memory_usage': {
                    'cache_mb': sum(
                        e.embedding.nbytes + 
                        (e.token_embeddings.nbytes if e.token_embeddings is not None else 0) +
                        (e.attention_weights.nbytes if e.attention_weights is not None else 0)
                        for e in self.embedding_cache.values()
                    ) / (1024 * 1024),
                    'model_mb': sum(
                        param.nelement() * param.element_size()
                        for param in self.base_model.parameters()
                    ) / (1024 * 1024)
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting performance metrics: {e}")
            return {}

if __name__ == "__main__":
    # Example usage
    def main():
        # Initialize model
        model = CryptoEmbeddingModel()
        
        # Example texts
        texts = [
            "Bullish on $SOL! 🚀 The memecoin ecosystem is growing fast",
            "Massive whale movement detected in BONK. Watch out for dumps 🐋",
            "New Solana memecoin launching tomorrow. Don't miss this gem! 💎"
        ]
        
        # Generate embeddings
        embeddings = model.get_batch_embeddings(texts)
        
        # Calculate similarities
        print("\nSimilarity Matrix:")
        for i, emb1 in enumerate(embeddings):
            for j, emb2 in enumerate(embeddings):
                similarity = model.calculate_similarity(emb1, emb2)
                print(f"Text {i+1} vs Text {j+1}: {similarity:.3f}")
        
        # Print performance metrics
        print("\nPerformance Metrics:")
        print(json.dumps(model.get_performance_metrics(), indent=2))
        
    main()