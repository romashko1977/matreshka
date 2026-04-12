"""
Matreshka - Momentum Strategy
Multi-indicator momentum strategy using RSI, MACD, EMA crossover, volume.
"""
import numpy as np
import pandas as pd
from typing import Dict, List

from .base import BaseStrategy, MarketData
from ..models.signal import Signal, SignalDirection, RiskProfile, MarketRegime


class MomentumStrategy(BaseStrategy):
    name = "momentum"
    version = "1.0.0"
    description = "Multi-indicator momentum: RSI + MACD + EMA crossover + volume confirmation"
    author = "matreshka"

    inputs_required = ["ohlcv"]
    min_candles = 100
    timeframes = ["15m", "1h", "4h"]
    risk_profile = RiskProfile.INTRADAY
    market_regime_fit = [MarketRegime.TRENDING_UP, MarketRegime.TRENDING_DOWN]

    parameters = {
        "rsi_period": 14,
        "rsi_overbought": 70,
        "rsi_oversold": 30,
        "macd_fast": 12,
        "macd_slow": 26,
        "macd_signal": 9,
        "ema_fast": 9,
        "ema_slow": 21,
        "volume_ma_period": 20,
        "volume_spike_mult": 1.5,
        "atr_period": 14,
        "atr_sl_mult": 1.5,
        "atr_tp_mult": 2.5,
    }

    parameter_ranges = {
        "rsi_period": (7, 21, 1),
        "rsi_overbought": (65, 80, 1),
        "rsi_oversold": (20, 35, 1),
        "ema_fast": (5, 15, 1),
        "ema_slow": (15, 50, 1),
        "volume_spike_mult": (1.2, 3.0, 0.1),
        "atr_sl_mult": (1.0, 3.0, 0.1),
        "atr_tp_mult": (1.5, 5.0, 0.1),
    }

    def _calc_rsi(self, close: pd.Series, period: int) -> pd.Series:
        delta = close.diff()
        gain = delta.where(delta > 0, 0).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss.replace(0, np.nan)
        return 100 - (100 / (1 + rs))

    def _calc_macd(self, close: pd.Series) -> tuple:
        fast = close.ewm(span=self.parameters["macd_fast"]).mean()
        slow = close.ewm(span=self.parameters["macd_slow"]).mean()
        macd = fast - slow
        signal = macd.ewm(span=self.parameters["macd_signal"]).mean()
        hist = macd - signal
        return macd, signal, hist

    def _calc_atr(self, df: pd.DataFrame, period: int) -> pd.Series:
        high, low, close = df['high'], df['low'], df['close']
        tr = pd.concat([
            high - low,
            (high - close.shift()).abs(),
            (low - close.shift()).abs()
        ], axis=1).max(axis=1)
        return tr.rolling(window=period).mean()

    def compute_features(self, data: MarketData) -> Dict[str, float]:
        df = data.ohlcv.copy()
        close = df['close']
        volume = df['volume']
        p = self.parameters

        rsi = self._calc_rsi(close, p["rsi_period"])
        macd, macd_signal, macd_hist = self._calc_macd(close)
        ema_fast = close.ewm(span=p["ema_fast"]).mean()
        ema_slow = close.ewm(span=p["ema_slow"]).mean()
        vol_ma = volume.rolling(p["volume_ma_period"]).mean()
        atr = self._calc_atr(df, p["atr_period"])

        return {
            "rsi": float(rsi.iloc[-1]),
            "rsi_prev": float(rsi.iloc[-2]),
            "macd": float(macd.iloc[-1]),
            "macd_signal": float(macd_signal.iloc[-1]),
            "macd_hist": float(macd_hist.iloc[-1]),
            "macd_hist_prev": float(macd_hist.iloc[-2]),
            "ema_fast": float(ema_fast.iloc[-1]),
            "ema_slow": float(ema_slow.iloc[-1]),
            "ema_cross": float(ema_fast.iloc[-1] - ema_slow.iloc[-1]),
            "ema_cross_prev": float(ema_fast.iloc[-2] - ema_slow.iloc[-2]),
            "volume_ratio": float(volume.iloc[-1] / vol_ma.iloc[-1]) if vol_ma.iloc[-1] > 0 else 1.0,
            "atr": float(atr.iloc[-1]),
            "price": float(close.iloc[-1]),
            "price_change_pct": float((close.iloc[-1] / close.iloc[-5] - 1) * 100),
        }

    def generate_signal(self, features: Dict[str, float], data: MarketData) -> Signal:
        p = self.parameters
        score = 0.0
        factors = 0

        # RSI
        if features["rsi"] < p["rsi_oversold"]:
            score += 25
            factors += 1
        elif features["rsi"] > p["rsi_overbought"]:
            score -= 25
            factors += 1

        # MACD histogram crossover
        if features["macd_hist"] > 0 and features["macd_hist_prev"] <= 0:
            score += 30
            factors += 1
        elif features["macd_hist"] < 0 and features["macd_hist_prev"] >= 0:
            score -= 30
            factors += 1

        # EMA crossover
        if features["ema_cross"] > 0 and features["ema_cross_prev"] <= 0:
            score += 25
            factors += 1
        elif features["ema_cross"] < 0 and features["ema_cross_prev"] >= 0:
            score -= 25
            factors += 1
        elif features["ema_cross"] > 0:
            score += 10
        elif features["ema_cross"] < 0:
            score -= 10

        # Volume confirmation
        if features["volume_ratio"] > p["volume_spike_mult"]:
            score *= 1.3
            factors += 1

        # Direction
        score = np.clip(score, -100, 100)
        if score > 15:
            direction = SignalDirection.LONG
        elif score < -15:
            direction = SignalDirection.SHORT
        else:
            direction = SignalDirection.NEUTRAL

        # Confidence based on factor agreement
        confidence = min(factors / 4.0, 1.0) * 0.8 + 0.1

        # Calculate SL/TP
        atr = features["atr"]
        price = features["price"]
        if direction == SignalDirection.LONG:
            sl = price - atr * p["atr_sl_mult"]
            tp = price + atr * p["atr_tp_mult"]
        elif direction == SignalDirection.SHORT:
            sl = price + atr * p["atr_sl_mult"]
            tp = price - atr * p["atr_tp_mult"]
        else:
            sl, tp = None, None

        return Signal(
            strategy_name=self.name,
            symbol=data.symbol,
            exchange=data.exchange,
            direction=direction,
            strength=float(score),
            confidence=float(confidence),
            entry_price=price,
            stop_loss=sl,
            take_profit=tp,
            features=features,
            tags=["momentum", "rsi", "macd", "ema"],
        )

    def explain(self, signal: Signal, features: Dict[str, float]) -> str:
        parts = []
        p = self.parameters
        if features["rsi"] < p["rsi_oversold"]:
            parts.append(f"RSI oversold ({features['rsi']:.1f})")
        elif features["rsi"] > p["rsi_overbought"]:
            parts.append(f"RSI overbought ({features['rsi']:.1f})")
        if features["macd_hist"] > 0 and features["macd_hist_prev"] <= 0:
            parts.append("MACD bullish crossover")
        elif features["macd_hist"] < 0 and features["macd_hist_prev"] >= 0:
            parts.append("MACD bearish crossover")
        if features["ema_cross"] > 0 and features["ema_cross_prev"] <= 0:
            parts.append("EMA golden cross")
        elif features["ema_cross"] < 0 and features["ema_cross_prev"] >= 0:
            parts.append("EMA death cross")
        if features["volume_ratio"] > p["volume_spike_mult"]:
            parts.append(f"Volume spike x{features['volume_ratio']:.1f}")
        return " | ".join(parts) if parts else "No strong signals"
