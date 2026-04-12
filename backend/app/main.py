"""
Matreshka - FastAPI Entry Point
Unified AI Crypto Screener Platform
"""
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import settings
from .api.routes_screener import router as screener_router
from .api.routes_strategy import router as strategy_router
from .api.routes_signals import router as signals_router
from .api.routes_execution import router as execution_router
from .api.routes_settings import router as settings_router
from .core.signal_fusion import SignalFusionEngine
from .connectors.exchange_manager import ExchangeManager
from .notifications.telegram_bot import TelegramNotifier


# Global instances
exchange_manager: ExchangeManager = None
fusion_engine: SignalFusionEngine = None
telegram_notifier: TelegramNotifier = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle manager."""
    global exchange_manager, fusion_engine, telegram_notifier

    # Startup
    print(f"Starting {settings.app_name} v{settings.app_version}")
    print(f"Mode: {settings.trading_mode.value}")
    print(f"Fusion: {settings.fusion_mode.value}")

    exchange_manager = ExchangeManager()
    await exchange_manager.initialize()

    fusion_engine = SignalFusionEngine(mode=settings.fusion_mode)

    if settings.telegram_bot_token:
        telegram_notifier = TelegramNotifier(
            token=settings.telegram_bot_token,
            chat_id=settings.telegram_chat_id
        )
        await telegram_notifier.send_message(
            f"Matreshka started | Mode: {settings.trading_mode.value}"
        )

    # Store in app state
    app.state.exchange_manager = exchange_manager
    app.state.fusion_engine = fusion_engine
    app.state.telegram = telegram_notifier

    yield

    # Shutdown
    if exchange_manager:
        await exchange_manager.close()
    if telegram_notifier:
        await telegram_notifier.send_message("Matreshka stopped")
    print("Matreshka shutdown complete")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="Unified AI Crypto Screener Platform",
    version=settings.app_version,
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(screener_router, prefix="/api/screener", tags=["Screener"])
app.include_router(strategy_router, prefix="/api/strategies", tags=["Strategies"])
app.include_router(signals_router, prefix="/api/signals", tags=["Signals"])
app.include_router(execution_router, prefix="/api/execution", tags=["Execution"])
app.include_router(settings_router, prefix="/api/settings", tags=["Settings"])


@app.get("/")
async def root():
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "mode": settings.trading_mode.value,
        "fusion": settings.fusion_mode.value,
        "status": "running"
    }


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
