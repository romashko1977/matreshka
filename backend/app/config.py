"""
Matreshka - Configuration Module
Centralized settings management with environment variable support.
"""
import os
from typing import Optional, List, Dict
from pydantic_settings import BaseSettings
from pydantic import Field, ConfigDict
from enum import Enum


class TradingMode(str, Enum):
    MONITOR = "monitor"
    PAPER = "paper"
    SEMI_AUTO = "semi_auto"
    FULL_AUTO = "full_auto"


class FusionMode(str, Enum):
    MAJORITY_VOTE = "majority_vote"
    WEIGHTED_VOTE = "weighted_vote"
    PERFORMANCE_WEIGHTED = "performance_weighted"
    AI_META_SCORE = "ai_meta_score"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = ConfigDict(extra="ignore", env_file=".env", env_file_encoding="utf-8")

    # === App ===
    app_name: str = "Matreshka"
    app_version: str = "0.1.0"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    secret_key: str = Field(default="change-me-in-production")
    language: str = "ru"  # ru | en

    # === Database ===
    database_url: str = "sqlite+aiosqlite:///./matreshka.db"
    redis_url: str = "redis://localhost:6379/0"

    # === Exchange API Keys ===
    bybit_api_key: Optional[str] = None
    bybit_api_secret: Optional[str] = None
    bybit_testnet: bool = True
    mexc_api_key: Optional[str] = None
    mexc_api_secret: Optional[str] = None
    bitunix_api_key: Optional[str] = None
    bitunix_api_secret: Optional[str] = None
    binance_api_key: Optional[str] = None
    binance_api_secret: Optional[str] = None

    # === Data Providers ===
    coinglass_api_key: Optional[str] = None
    fpi_api_key: Optional[str] = None

    # === AI Providers ===
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    ai_provider: str = "openai"  # openai | anthropic | local
    ai_model: str = "gpt-4o-mini"

    # === Telegram ===
    telegram_bot_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    telegram_alerts_enabled: bool = True

    # === Trading ===
    trading_mode: TradingMode = TradingMode.MONITOR
    fusion_mode: FusionMode = FusionMode.WEIGHTED_VOTE
    max_concurrent_positions: int = 5
    max_risk_per_trade: float = 0.02  # 2%
    max_daily_loss: float = 0.05  # 5%
    cooldown_after_losses: int = 3
    default_leverage: int = 5

    # === Screener ===
    screener_symbols: List[str] = Field(default_factory=lambda: [
        "BTC/USDT", "ETH/USDT", "SOL/USDT", "DOGE/USDT",
        "XRP/USDT", "ADA/USDT", "AVAX/USDT", "LINK/USDT",
        "DOT/USDT", "MATIC/USDT", "ARB/USDT", "OP/USDT",
        "APT/USDT", "SUI/USDT", "INJ/USDT", "TIA/USDT",
        "SEI/USDT", "JUP/USDT", "WIF/USDT", "PEPE/USDT"
    ])
    screener_timeframes: List[str] = Field(default_factory=lambda: [
        "5m", "15m", "1h", "4h"
    ])
    screener_update_interval: int = 30  # seconds

    # === Optimization ===
    backtest_start_date: str = "2024-01-01"
    backtest_end_date: str = "2025-01-01"
    walk_forward_windows: int = 5
    optuna_trials: int = 100


# Singleton
settings = Settings()


def get_exchange_configs() -> Dict[str, dict]:
    """Get configured exchange credentials."""
    exchanges = {}
    if settings.bybit_api_key:
        exchanges["bybit"] = {
            "api_key": settings.bybit_api_key,
            "api_secret": settings.bybit_api_secret,
            "testnet": settings.bybit_testnet,
        }
    if settings.mexc_api_key:
        exchanges["mexc"] = {
            "api_key": settings.mexc_api_key,
            "api_secret": settings.mexc_api_secret,
        }
    if settings.bitunix_api_key:
        exchanges["bitunix"] = {
            "api_key": settings.bitunix_api_key,
            "api_secret": settings.bitunix_api_secret,
        }
    if settings.binance_api_key:
        exchanges["binance"] = {
            "api_key": settings.binance_api_key,
            "api_secret": settings.binance_api_secret,
        }
    return exchanges
