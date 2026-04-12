"""
Matreshka - Strategy Registry
Manages registration, discovery, and lifecycle of strategy plugins.
"""
from typing import Dict, List, Optional, Type
from .base import BaseStrategy, MarketData
from ..models.signal import Signal


class StrategyRegistry:
    """Central registry for all strategy plugins."""

    def __init__(self):
        self._strategies: Dict[str, BaseStrategy] = {}

    def register(self, strategy: BaseStrategy):
        """Register a strategy instance."""
        self._strategies[strategy.name] = strategy
        print(f"Strategy registered: {strategy.name} v{strategy.version}")

    def unregister(self, name: str):
        """Remove a strategy."""
        if name in self._strategies:
            del self._strategies[name]

    def get(self, name: str) -> Optional[BaseStrategy]:
        return self._strategies.get(name)

    def get_all(self) -> List[BaseStrategy]:
        return list(self._strategies.values())

    def get_enabled(self) -> List[BaseStrategy]:
        return [s for s in self._strategies.values() if s.enabled]

    def enable(self, name: str):
        if name in self._strategies:
            self._strategies[name].enabled = True

    def disable(self, name: str):
        if name in self._strategies:
            self._strategies[name].enabled = False

    def set_weight(self, name: str, weight: float):
        if name in self._strategies:
            self._strategies[name].weight = weight

    def run_all(self, data: MarketData) -> List[Signal]:
        """Run all enabled strategies and collect signals."""
        signals = []
        for strategy in self.get_enabled():
            signal = strategy.run(data)
            if signal is not None:
                signals.append(signal)
        return signals

    def get_configs(self) -> List[dict]:
        """Get configuration of all strategies for UI."""
        return [s.get_config() for s in self._strategies.values()]

    def update_parameters(self, name: str, params: dict):
        """Update strategy parameters."""
        if name in self._strategies:
            self._strategies[name].update_parameters(params)


def create_default_registry() -> StrategyRegistry:
    """Create registry with all built-in strategies."""
    from .momentum import MomentumStrategy
    # Import more strategies as they are created:
    # from .mean_reversion import MeanReversionStrategy
    # from .breakout import BreakoutStrategy
    # from .liquidation import LiquidationStrategy
    # from .funding_arb import FundingArbStrategy
    # from .volume_spike import VolumeSpikeStrategy
    # from .oi_divergence import OIDivergenceStrategy
    # from .cvd_flow import CVDFlowStrategy

    registry = StrategyRegistry()
    registry.register(MomentumStrategy())
    # registry.register(MeanReversionStrategy())
    # registry.register(BreakoutStrategy())
    # registry.register(LiquidationStrategy())
    # registry.register(FundingArbStrategy())
    # registry.register(VolumeSpikeStrategy())
    # registry.register(OIDivergenceStrategy())
    # registry.register(CVDFlowStrategy())

    return registry
