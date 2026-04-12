"""
Matreshka - Signal Fusion Engine
Aggregates signals from multiple strategies into a unified score.
Supports: majority vote, weighted vote, performance-weighted, AI meta-score.
"""
from typing import List, Dict, Optional
from collections import Counter
import numpy as np

from ..config import FusionMode
from ..models.signal import (
    Signal, FusedSignal, SignalDirection, MarketRegime
)


class SignalFusionEngine:
    """Core engine for combining signals from multiple strategies."""

    def __init__(self, mode: FusionMode = FusionMode.WEIGHTED_VOTE):
        self.mode = mode
        self.strategy_weights: Dict[str, float] = {}
        self.correlation_matrix: Dict[str, Dict[str, float]] = {}

    def fuse(self, signals: List[Signal], regime: Optional[MarketRegime] = None) -> Optional[FusedSignal]:
        """Fuse multiple strategy signals into one composite signal."""
        if not signals:
            return None

        # Filter expired signals
        from datetime import datetime
        active = [s for s in signals if s.expires_at is None or s.expires_at > datetime.utcnow()]
        if not active:
            return None

        if self.mode == FusionMode.MAJORITY_VOTE:
            return self._majority_vote(active, regime)
        elif self.mode == FusionMode.WEIGHTED_VOTE:
            return self._weighted_vote(active, regime)
        elif self.mode == FusionMode.PERFORMANCE_WEIGHTED:
            return self._performance_weighted(active, regime)
        elif self.mode == FusionMode.AI_META_SCORE:
            return self._ai_meta_score(active, regime)
        return None

    def _majority_vote(self, signals: List[Signal], regime: Optional[MarketRegime]) -> FusedSignal:
        """Simple majority vote - each strategy gets one vote."""
        directions = [s.direction for s in signals]
        counter = Counter(directions)
        winner = counter.most_common(1)[0]
        winning_direction = winner[0]
        consensus = winner[1]
        total = len(signals)

        # Composite score = average strength of agreeing signals
        agreeing = [s for s in signals if s.direction == winning_direction]
        avg_strength = np.mean([s.strength for s in agreeing])
        avg_confidence = np.mean([s.confidence for s in agreeing])

        return FusedSignal(
            symbol=signals[0].symbol,
            exchange=signals[0].exchange,
            direction=winning_direction,
            composite_score=float(avg_strength),
            confidence=float(avg_confidence * (consensus / total)),
            contributing_signals=signals,
            consensus_count=consensus,
            divergence_count=total - consensus,
            regime=regime,
        )

    def _weighted_vote(self, signals: List[Signal], regime: Optional[MarketRegime]) -> FusedSignal:
        """Weighted vote using strategy weights."""
        total_score = 0.0
        total_weight = 0.0

        for s in signals:
            w = self.strategy_weights.get(s.strategy_name, 1.0)
            direction_mult = 1.0 if s.direction == SignalDirection.LONG else (
                -1.0 if s.direction == SignalDirection.SHORT else 0.0
            )
            # Apply regime fit bonus
            regime_bonus = 1.2 if regime and regime in s.market_regime_fit else 1.0
            weighted = w * s.strength * s.confidence * direction_mult * regime_bonus
            total_score += weighted
            total_weight += abs(w * s.confidence * regime_bonus)

        if total_weight == 0:
            return None

        normalized = total_score / total_weight
        direction = (
            SignalDirection.LONG if normalized > 0
            else SignalDirection.SHORT if normalized < 0
            else SignalDirection.NEUTRAL
        )

        # Count consensus/divergence
        consensus = sum(1 for s in signals if s.direction == direction)
        divergence = len(signals) - consensus

        # Average confidence weighted
        conf_vals = [s.confidence * self.strategy_weights.get(s.strategy_name, 1.0) for s in signals]
        avg_conf = np.mean(conf_vals) if conf_vals else 0

        return FusedSignal(
            symbol=signals[0].symbol,
            exchange=signals[0].exchange,
            direction=direction,
            composite_score=float(np.clip(normalized * 100, -100, 100)),
            confidence=float(np.clip(avg_conf, 0, 1)),
            contributing_signals=signals,
            consensus_count=consensus,
            divergence_count=divergence,
            regime=regime,
        )

    def _performance_weighted(self, signals: List[Signal], regime: Optional[MarketRegime]) -> FusedSignal:
        """Weight by historical performance (walk-forward scores)."""
        # Override weights with performance scores, then use weighted vote
        original_weights = self.strategy_weights.copy()
        for s in signals:
            perf = getattr(s, '_performance_score', 1.0)
            self.strategy_weights[s.strategy_name] = max(perf, 0.1)
        result = self._weighted_vote(signals, regime)
        self.strategy_weights = original_weights
        return result

    def _ai_meta_score(self, signals: List[Signal], regime: Optional[MarketRegime]) -> FusedSignal:
        """Use AI model to evaluate and rank signals (placeholder)."""
        # TODO: Integrate with AI layer for meta-ranking
        # For now, falls back to weighted vote
        return self._weighted_vote(signals, regime)

    def set_weight(self, strategy_name: str, weight: float):
        """Set weight for a specific strategy."""
        self.strategy_weights[strategy_name] = weight

    def get_weights(self) -> Dict[str, float]:
        return self.strategy_weights.copy()

    def analyze_divergence(self, signals: List[Signal]) -> dict:
        """Analyze signal divergence between strategies."""
        if not signals:
            return {"status": "no_signals"}

        longs = [s for s in signals if s.direction == SignalDirection.LONG]
        shorts = [s for s in signals if s.direction == SignalDirection.SHORT]
        neutrals = [s for s in signals if s.direction == SignalDirection.NEUTRAL]

        return {
            "total_signals": len(signals),
            "long_count": len(longs),
            "short_count": len(shorts),
            "neutral_count": len(neutrals),
            "consensus": len(longs) > len(shorts) * 2 or len(shorts) > len(longs) * 2,
            "strong_divergence": len(longs) > 0 and len(shorts) > 0 and abs(len(longs) - len(shorts)) <= 1,
            "avg_long_strength": float(np.mean([s.strength for s in longs])) if longs else 0,
            "avg_short_strength": float(np.mean([s.strength for s in shorts])) if shorts else 0,
            "long_strategies": [s.strategy_name for s in longs],
            "short_strategies": [s.strategy_name for s in shorts],
        }
