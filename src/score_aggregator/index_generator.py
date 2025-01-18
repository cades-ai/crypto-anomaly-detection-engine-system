"""
Crypto Anomaly Detection Engine System (CADES)
Index Generator Module

This module generates tradable indices based on aggregated metrics and risk scores,
implementing index calculation and rebalancing logic.

Author: CADES Team
License: Proprietary
"""

import asyncio
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import numpy as np
from collections import defaultdict
import logging
from dataclasses import dataclass, field

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class IndexComponent:
    """Index component details"""
    token_address: str
    weight: float
    risk_score: float
    metrics: Dict[str, float]
    last_updated: datetime

@dataclass
class IndexState:
    """Current state of an index"""
    name: str
    timestamp: datetime
    components: List[IndexComponent]
    total_value: float
    performance_metrics: Dict[str, float]
    risk_metrics: Dict[str, float]

class IndexGenerator:
    """Generates and manages tradable indices."""
    
    def __init__(
        self,
        max_components: int = 10,
        rebalance_interval: int = 86400,  # 24 hours
        risk_threshold: float = 0.7
    ):
        """Initialize the index generator."""
        self.max_components = max_components
        self.rebalance_interval = rebalance_interval
        self.risk_threshold = risk_threshold
        
        # Index tracking
        self.indices = {}
        self.last_rebalance = {}
        self.performance_history = defaultdict(list)

    async def generate_index(
        self,
        name: str,
        token_data: Dict[str, Dict],
        metrics: Dict[str, Dict],
        risk_scores: Dict[str, float]
    ) -> IndexState:
        """Generate or update an index."""
        try:
            # Check if rebalancing is needed
            if self._needs_rebalancing(name):
                components = self._select_components(
                    token_data,
                    metrics,
                    risk_scores
                )
                
                # Calculate weights
                weights = self._calculate_weights(components)
                
                # Create index components
                index_components = [
                    IndexComponent(
                        token_address=addr,
                        weight=weights[addr],
                        risk_score=risk_scores[addr],
                        metrics=metrics[addr],
                        last_updated=datetime.now()
                    )
                    for addr in components
                ]
                
                # Update index
                self.indices[name] = index_components
                self.last_rebalance[name] = datetime.now()
            
            # Calculate current index state
            total_value = self._calculate_total_value(
                self.indices[name],
                token_data
            )
            
            # Calculate performance metrics
            performance = self._calculate_performance(
                name,
                total_value
            )
            
            # Calculate risk metrics
            risk = self._calculate_index_risk(self.indices[name])
            
            return IndexState(
                name=name,
                timestamp=datetime.now(),
                components=self.indices[name],
                total_value=total_value,
                performance_metrics=performance,
                risk_metrics=risk
            )
            
        except Exception as e:
            logger.error(f"Error generating index: {e}")
            raise

    def _select_components(
        self,
        token_data: Dict[str, Dict],
        metrics: Dict[str, Dict],
        risk_scores: Dict[str, float]
    ) -> List[str]:
        """Select tokens for index inclusion."""
        try:
            candidates = []
            
            for token_address, token_metrics in metrics.items():
                if risk_scores[token_address] >= self.risk_threshold:
                    continue
                
                score = self._calculate_inclusion_score(
                    token_metrics,
                    token_data[token_address]
                )
                
                candidates.append((token_address, score))
            
            # Sort by score and take top components
            candidates.sort(key=lambda x: x[1], reverse=True)
            return [c[0] for c in candidates[:self.max_components]]
            
        except Exception as e:
            logger.error(f"Error selecting components: {e}")
            return []

    def _calculate_weights(self, components: List[str]) -> Dict[str, float]:
        """Calculate component weights."""
        try:
            # Equal weighting for simplicity
            weight = 1.0 / len(components)
            return {addr: weight for addr in components}
            
        except Exception as e:
            logger.error(f"Error calculating weights: {e}")
            return {}

    def _calculate_inclusion_score(
        self,
        metrics: Dict[str, float],
        token_data: Dict
    ) -> float:
        """Calculate score for index inclusion."""
        try:
            score_factors = []
            
            # Liquidity factor
            if 'liquidity' in metrics:
                score_factors.append(
                    min(1.0, metrics['liquidity'] / 1_000_000)
                )
            
            # Volume factor
            if 'volume' in token_data:
                score_factors.append(
                    min(1.0, token_data['volume'] / 100_000)
                )
            
            # Stability factor
            if 'volatility' in metrics:
                score_factors.append(1.0 - metrics['volatility'])
            
            return float(np.mean(score_factors)) if score_factors else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating inclusion score: {e}")
            return 0.0

    def _calculate_total_value(
        self,
        components: List[IndexComponent],
        token_data: Dict[str, Dict]
    ) -> float:
        """Calculate total index value."""
        try:
            total = 0.0
            for component in components:
                if component.token_address in token_data:
                    price = token_data[component.token_address].get('price', 0)
                    total += price * component.weight
            return total
            
        except Exception as e:
            logger.error(f"Error calculating total value: {e}")
            return 0.0

    def _calculate_performance(
        self,
        name: str,
        current_value: float
    ) -> Dict[str, float]:
        """Calculate index performance metrics."""
        try:
            metrics = {
                'current_value': current_value
            }
            
            if name in self.performance_history:
                history = self.performance_history[name]
                if history:
                    returns = np.diff(
                        [h['value'] for h in history + [{'value': current_value}]]
                    )
                    metrics.update({
                        'returns_mean': float(np.mean(returns)),
                        'returns_std': float(np.std(returns)),
                        'total_return': float(
                            (current_value - history[0]['value']) / history[0]['value']
                        )
                    })
            
            self.performance_history[name].append({
                'value': current_value,
                'timestamp': datetime.now()
            })
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating performance: {e}")
            return {'current_value': current_value}

    def _calculate_index_risk(
        self,
        components: List[IndexComponent]
    ) -> Dict[str, float]:
        """Calculate index risk metrics."""
        try:
            risk_metrics = {
                'total_risk': float(np.mean([c.risk_score for c in components])),
                'max_component_risk': float(max(c.risk_score for c in components)),
                'risk_std': float(np.std([c.risk_score for c in components]))
            }
            
            return risk_metrics
            
        except Exception as e:
            logger.error(f"Error calculating index risk: {e}")
            return {'total_risk': 0.0}

    def _needs_rebalancing(self, index_name: str) -> bool:
        """Check if index needs rebalancing."""
        try:
            if index_name not in self.last_rebalance:
                return True
                
            time_since_rebalance = (
                datetime.now() - self.last_rebalance[index_name]
            ).total_seconds()
            
            return time_since_rebalance >= self.rebalance_interval
            
        except Exception as e:
            logger.error(f"Error checking rebalance need: {e}")
            return True

if __name__ == "__main__":
    async def main():
        generator = IndexGenerator()
        
        # Example data
        token_data = {
            "token1": {"price": 100, "volume": 50000},
            "token2": {"price": 200, "volume": 75000}
        }
        metrics = {
            "token1": {"liquidity": 500000, "volatility": 0.3},
            "token2": {"liquidity": 750000, "volatility": 0.2}
        }
        risk_scores = {
            "token1": 0.4,
            "token2": 0.3
        }
        
        index = await generator.generate_index(
            "MemeIndex",
            token_data,
            metrics,
            risk_scores
        )
        
        print(f"Index Value: {index.total_value:.2f}")
        print(f"Components: {len(index.components)}")
        print(f"Risk Metrics: {index.risk_metrics}")
        
    asyncio.run(main())