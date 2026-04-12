"""
Matreshka - Base Strategy Plugin
Abstract base class for all trading strategies.
Every strategy must implement this interface to be registered in the platform.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
from datetime import datetime
import pandas as pd

from ..models.signal import Signal, SignalDirection, RiskProfile, MarketRegime


class MarketData:
    """Container for market data passed to strategies."""
    def __init__(
        self,
        symbol: str,
        exchange: str,
        ohlcv: Optional[pd.DataFrame] = None,
        orderbook: Optional[dict] = None,
        trades: Optional[pd.DataFrame] = None,
        open_interest: Optional[pd.DataFrame] = None,
        funding_rate: Optional[float] = None,
        funding_history: Optional[pd.DataFrame] = None,
        liquidations: Optional[pd.DataFrame] = None,
        long_short_ratio: Optional[float] = None,
        cvd: Optional[pd.DataFrame] = None,
        volume_profile: Optional[dict] = None,
        extra: Optional[Dict[str, Any]] = None,
    ):
        self.symbol = symbol
        self.exchange = exchange
        self.ohlcv = ohlcv
        self.orderbook = orderbook
        self.trades = trades
        self.open_interest = open_interest
        self.funding_rate = funding_rate
        self.funding_history = funding_history
        self.liquidations = liquidations
        self.long_short_ratio = long_short_ratio
        self.cvd = cvd
        self.volume_profile = volume_profile
        self.extra = extra or {}

    @property
    def last_price(self) -> Optional[float]:
        if self.ohlcv is not None and len(self.ohlcv) > 0:
            return float(self.ohlcv['close'].iloc[-1])
        return None


class BaseStrategy(ABC):
    """Abstract base class for all Matreshka strategies."""

    # === Required metadata ===
    name: str = "unnamed_strategy"
    version: str = "1.0.0"
    description: str = ""
    author: str = "matreshka"

    # === Data requirements ===
    inputs_required: List[str] = ["ohlcv"]  # ohlcv, oi, funding, cvd, liquidations, orderbook
    min_candles: int = 50
    timeframes: List[str] = ["15m"]

    # === Strategy profile ===
    risk_profile: RiskProfile = RiskProfile.INTRADAY
    market_regime_fit: List[MarketRegime] = []  # Which regimes this strategy works best in

    # === Parameters (overridable) ===
    parameters: Dict[str, Any] = {}
    parameter_ranges: Dict[str, tuple] = {}  # For optimization: {"param": (min, max, step)}

    # === State ===
    enabled: bool = True
    weight: float = 1.0  # Weight in signal fusion
    last_signal: Optional[Signal] = None
    performance_score: float = 0.0  # Updated by walk-forward

    def __init__(self, **kwargs):
        """Initialize strategy with optional parameter overrides."""
        for key, value in kwargs.items():
            if key in self.parameters:
                self.parameters[key] = value
            elif hasattr(self, key):
                setattr(self, key, value)

    @abstractmethod
    def compute_features(self, data: MarketData) -> Dict[str, float]:
        """
        Compute strategy-specific features from market data.
        Returns dict of feature_name -> value.
        """
        pass

    @abstractmethod
    def generate_signal(self, features: Dict[str, float], data: MarketData) -> Signal:
        """
        Generate trading signal based on computed features.
        Must return a Signal object with direction, strength, confidence.
        """
        pass

    @abstractmethod
    def explain(self, signal: Signal, features: Dict[str, float]) -> str:
        """
        Human-readable explanation of why signal was generated.
        Used in dashboard and Telegram alerts.
        """
        pass

    def validate_data(self, data: MarketData) -> bool:
        """Check if all required data is available."""
        for inp in self.inputs_required:
            if inp == "ohlcv" and (data.ohlcv is None or len(data.ohlcv) < self.min_candles):
                return False
            if inp == "oi" and data.open_interest is None:
                return False
            if inp == "funding" and data.funding_rate is None:
                return False
            if inp == "cvd" and data.cvd is None:
                return False
            if inp == "liquidations" and data.liquidations is None:
                return False
            if inp == "orderbook" and data.orderbook is None:
                return False
        return True

    def run(self, data: MarketData) -> Optional[Signal]:
        """Execute strategy pipeline: validate -> compute -> generate -> explain."""
        if not self.enabled:
            return None

        if not self.validate_data(data):
            return None

        try:
            features = self.compute_features(data)
            signal = self.generate_signal(features, data)
            signal.explanation = self.explain(signal, features)
            signal.strategy_name = self.name
            signal.strategy_version = self.version
            signal.symbol = data.symbol
            signal.exchange = data.exchange
            signal.risk_profile = self.risk_profile
            signal.market_regime_fit = self.market_regime_fit
            self.last_signal = signal
            return signal
        except Exception as e:
            print(f"Strategy {self.name} error: {e}")
            return None

    def get_config(self) -> dict:
        """Return strategy configuration for UI display."""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "enabled": self.enabled,
            "weight": self.weight,
            "risk_profile": self.risk_profile.value,
            "inputs_required": self.inputs_required,
            "timeframes": self.timeframes,
            "parameters": self.parameters,
            "parameter_ranges": self.parameter_ranges,
            "performance_score": self.performance_score,
            "market_regime_fit": [r.value for r in self.market_regime_fit],
        }

    def update_parameters(self, params: Dict[str, Any]):
        """Update strategy parameters (from optimizer or UI)."""
        for key, value in params.items():
            if key in self.parameters:
                self.parameters[key] = value
