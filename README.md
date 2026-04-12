# MATRESHKA - Unified AI Crypto Screener Platform

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)
![React](https://img.shields.io/badge/React-18+-61DAFB.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

> Multi-strategy signal fusion, AI analysis, multi-exchange auto-trading dashboard

## Architecture

```
Data Connectors -> Feature Engine -> Strategy Plugins -> Signal Fusion -> AI Layer -> Execution
     |                  |                  |                 |              |           |
  CCXT/APIs        OHLCV/OI/FR      Momentum/MR/BO      Voting/WS      Regime      Orders
  Coinglass        CVD/Liq/Vol      LiqReaction/Arb     AI-Meta       Ranking     Risk Mgmt
  FPI/TG           Volatility       Custom Plugins      Consensus     Anomaly     Paper/Live
```

## Features

- **Strategy Marketplace** - plug-in any strategy, enable/disable, set weights
- **Signal Fusion Engine** - majority vote, weighted, performance-based, AI meta-score
- **AI Advisor** - regime detection, signal ranking, anomaly detection, explainability
- **Multi-Exchange** - Bybit, MEXC, Bitunix, Binance via CCXT + native APIs
- **Data Providers** - Coinglass (OI/funding/liquidations), FPI, custom feeds
- **Execution Engine** - paper trading, semi-auto, full auto with risk controls
- **Beautiful Dashboard** - dark/light theme, multi-language (RU/EN), real-time charts
- **Optimization Center** - backtest, walk-forward, Optuna/Bayesian parameter search
- **Secrets Vault** - secure API key management for exchanges, Telegram, AI providers
- **Telegram Integration** - alerts, commands, emergency stop

## Project Structure

```
matreshka/
|-- backend/
|   |-- app/
|   |   |-- main.py                 # FastAPI entry point
|   |   |-- config.py               # Settings & environment
|   |   |-- models/                 # Pydantic models
|   |   |   |-- signal.py           # Signal data model
|   |   |   |-- strategy.py         # Strategy config model
|   |   |   |-- market.py           # Market data model
|   |   |   |-- order.py            # Order/execution model
|   |   |-- api/                    # REST API routes
|   |   |   |-- routes_screener.py  # Screener endpoints
|   |   |   |-- routes_strategy.py  # Strategy management
|   |   |   |-- routes_signals.py   # Signal fusion
|   |   |   |-- routes_execution.py # Trading execution
|   |   |   |-- routes_settings.py  # Settings & secrets
|   |   |-- core/                   # Core engine
|   |   |   |-- feature_engine.py   # Feature computation
|   |   |   |-- signal_fusion.py    # Signal aggregation
|   |   |   |-- regime_detector.py  # Market regime detection
|   |   |-- strategies/             # Strategy plugins
|   |   |   |-- base.py             # Base strategy class
|   |   |   |-- registry.py         # Strategy registry
|   |   |   |-- momentum.py         # Momentum strategy
|   |   |   |-- mean_reversion.py   # Mean reversion
|   |   |   |-- breakout.py         # Breakout strategy
|   |   |   |-- liquidation.py      # Liquidation reaction
|   |   |   |-- funding_arb.py      # Funding rate arbitrage
|   |   |   |-- volume_spike.py     # Volume spike detector
|   |   |   |-- oi_divergence.py    # OI divergence
|   |   |   |-- cvd_flow.py         # CVD flow analysis
|   |   |-- connectors/             # Data connectors
|   |   |   |-- exchange_manager.py # Multi-exchange manager
|   |   |   |-- ccxt_adapter.py     # CCXT wrapper
|   |   |   |-- bybit_native.py     # Bybit native API
|   |   |   |-- mexc_native.py      # MEXC native API
|   |   |   |-- coinglass.py        # Coinglass API
|   |   |   |-- fpi_client.py       # FPI data client
|   |   |-- ai/                     # AI layer
|   |   |   |-- meta_model.py       # Meta-ranking model
|   |   |   |-- regime_classifier.py# Regime classifier
|   |   |   |-- anomaly_detector.py # Anomaly detection
|   |   |   |-- param_recommender.py# Parameter optimizer
|   |   |   |-- explainer.py        # Signal explainability
|   |   |-- execution/              # Execution engine
|   |   |   |-- order_manager.py    # Order management
|   |   |   |-- risk_engine.py      # Risk controls
|   |   |   |-- paper_trader.py     # Paper trading
|   |   |   |-- live_trader.py      # Live execution
|   |   |-- optimization/           # Optimization
|   |   |   |-- backtester.py       # Backtest engine
|   |   |   |-- walk_forward.py     # Walk-forward validation
|   |   |   |-- optimizer.py        # Optuna parameter search
|   |   |-- notifications/          # Notifications
|   |   |   |-- telegram_bot.py     # Telegram integration
|   |   |   |-- webhook.py          # Webhook sender
|   |   |-- vault/                  # Secrets management
|   |   |   |-- secrets_manager.py  # Encrypted key storage
|   |   |   |-- vault_models.py     # Vault data models
|-- frontend/
|   |-- src/
|   |   |-- App.tsx                 # Main app
|   |   |-- i18n/                   # Internationalization
|   |   |   |-- en.json             # English
|   |   |   |-- ru.json             # Russian
|   |   |-- pages/                  # Dashboard pages
|   |   |   |-- Overview.tsx        # Market pulse
|   |   |   |-- Screener.tsx        # Screener grid
|   |   |   |-- StrategyLab.tsx     # Strategy management
|   |   |   |-- SignalFusion.tsx    # Signal analysis
|   |   |   |-- AIAdvisor.tsx       # AI recommendations
|   |   |   |-- Optimization.tsx    # Backtest & optimize
|   |   |   |-- Execution.tsx       # Trading center
|   |   |   |-- Alerts.tsx          # Alert configuration
|   |   |   |-- Settings.tsx        # API keys & config
|   |   |-- components/             # UI components
|   |   |   |-- SignalHeatmap.tsx    # Signal heatmap
|   |   |   |-- CoinCard.tsx        # Coin detail card
|   |   |   |-- StrategyCard.tsx    # Strategy toggle card
|   |   |   |-- TradePanel.tsx      # Trade execution panel
|   |   |   |-- SecretVault.tsx     # API key input panel
|-- docker-compose.yml
|-- Dockerfile
|-- requirements.txt
|-- .env.example
```

## Signal Flow

1. **Data Collection** - CCXT/native APIs fetch OHLCV, orderbook, trades
2. **Feature Computation** - OI, funding, CVD proxy, volatility, volume profile
3. **Strategy Execution** - Each plugin computes signal independently
4. **Signal Normalization** - All signals mapped to [-100, +100] with confidence [0, 1]
5. **Fusion** - Weighted aggregation with correlation penalty and regime fit
6. **AI Evaluation** - Meta-model ranks signals, detects anomalies
7. **Decision** - Final score + risk check -> trade or alert

## Strategy Plugin Contract

```python
class BaseStrategy(ABC):
    name: str
    version: str
    inputs_required: List[str]  # ['ohlcv', 'oi', 'funding']
    risk_profile: str           # 'scalp' | 'intraday' | 'swing'
    market_regime_fit: List[str] # ['trend', 'squeeze', 'volatile']

    @abstractmethod
    def compute_features(self, data: MarketData) -> dict: ...

    @abstractmethod
    def generate_signal(self, features: dict) -> Signal: ...

    @abstractmethod
    def explain(self, signal: Signal) -> str: ...
```

## Fusion Modes

| Mode | Description |
|------|-------------|
| Majority Vote | Simple strategy polling |
| Weighted Vote | Manual weight per strategy |
| Performance-Weighted | Auto-weight by walk-forward results |
| AI Meta-Score | ML model evaluates strategy reliability per regime |

## Quick Start

```bash
git clone https://github.com/romashko1977/matreshka.git
cd matreshka
cp .env.example .env
# Edit .env with your API keys
docker-compose up -d
# Open http://localhost:3000
```

## Tech Stack

- **Backend**: Python 3.11+, FastAPI, asyncio, Celery
- **Data**: PostgreSQL + TimescaleDB, Redis
- **ML**: scikit-learn, LightGBM, Optuna
- **Frontend**: React 18, TypeScript, Tailwind CSS, Lightweight Charts
- **Realtime**: WebSocket, SSE
- **Deploy**: Docker Compose

## Roadmap

- [x] Phase 1: Core screener + signal fusion + dashboard
- [ ] Phase 2: Strategy marketplace + plugin system
- [ ] Phase 3: AI advisor + regime detection
- [ ] Phase 4: Optimization center + walk-forward
- [ ] Phase 5: Execution engine + multi-exchange
- [ ] Phase 6: Production + i18n + RBAC

## License

MIT License
