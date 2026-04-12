"""
Matreshka - Signal Data Models
Unified signal format for all strategies.
"""
from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, Field
from enum import Enum


class SignalDirection(str, Enum):
    LONG = "long"
    SHORT = "short"
    NEUTRAL = "neutral"


class RiskProfile(str, Enum):
    SCALP = "scalp"
    INTRADAY = "intraday"
    SWING = "swing"
    HIGH_RISK = "high_risk"


class MarketRegime(str, Enum):
    TRENDING_UP = "trending_up"
    TRENDING_DOWN = "trending_down"
    RANGING = "ranging"
    HIGH_VOLATILITY = "high_volatility"
    SQUEEZE = "squeeze"
    PANIC = "panic"
    PUMP = "pump"


class Signal(BaseModel):
    """Unified signal from any strategy."""
    strategy_name: str
    strategy_version: str = "1.0"
    symbol: str
    exchange: str = "bybit"
    timeframe: str = "15m"
    direction: SignalDirection
    strength: float = Field(ge=-100, le=100)  # -100 to +100
    confidence: float = Field(ge=0, le=1)  # 0 to 1
    risk_profile: RiskProfile = RiskProfile.INTRADAY
    market_regime_fit: List[MarketRegime] = []
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    take_profit_2: Optional[float] = None
    take_profit_3: Optional[float] = None
    leverage: int = 5
    explanation: str = ""
    features: Dict[str, float] = {}
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    tags: List[str] = []

    @property
    def is_bullish(self) -> bool:
        return self.direction == SignalDirection.LONG

    @property
    def is_bearish(self) -> bool:
        return self.direction == SignalDirection.SHORT

    @property
    def weighted_score(self) -> float:
        return self.strength * self.confidence


class FusedSignal(BaseModel):
    """Aggregated signal from multiple strategies."""
    symbol: str
    exchange: str
    direction: SignalDirection
    composite_score: float = Field(ge=-100, le=100)
    confidence: float = Field(ge=0, le=1)
    contributing_signals: List[Signal] = []
    consensus_count: int = 0
    divergence_count: int = 0
    regime: Optional[MarketRegime] = None
    ai_comment: str = ""
    ai_ranking: float = 0.0
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    risk_reward_ratio: Optional[float] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    @property
    def signal_agreement(self) -> float:
        total = self.consensus_count + self.divergence_count
        return self.consensus_count / total if total > 0 else 0


class SignalHistory(BaseModel):
    """Historical signal record for backtesting."""
    signal: FusedSignal
    result: Optional[str] = None  # 'win' | 'loss' | 'breakeven'
    pnl: Optional[float] = None
    pnl_percent: Optional[float] = None
    duration_minutes: Optional[int] = None
    closed_at: Optional[datetime] = None
