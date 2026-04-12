"""
Matreshka - Screener API Routes
Endpoints for the main screener dashboard.
"""
from fastapi import APIRouter, Request, Query
from typing import List, Optional
import asyncio

from ..config import settings
from ..strategies.registry import create_default_registry
from ..core.signal_fusion import SignalFusionEngine

router = APIRouter()

# Initialize registry
registry = create_default_registry()


@router.get("/scan")
async def scan_all(request: Request, timeframe: str = "15m"):
    """Run full screener scan on all configured symbols."""
    exchange_mgr = request.app.state.exchange_manager
    fusion = request.app.state.fusion_engine

    results = []
    for symbol in settings.screener_symbols:
        try:
            data = await exchange_mgr.get_market_data(symbol, timeframe)
            signals = registry.run_all(data)
            fused = fusion.fuse(signals) if signals else None

            result = {
                "symbol": symbol,
                "price": data.last_price,
                "signals_count": len(signals),
                "fused": fused.model_dump() if fused else None,
                "divergence": fusion.analyze_divergence(signals),
            }
            results.append(result)
        except Exception as e:
            results.append({"symbol": symbol, "error": str(e)})

    # Sort by absolute composite score
    results.sort(
        key=lambda x: abs(x.get("fused", {}).get("composite_score", 0) if x.get("fused") else 0),
        reverse=True
    )
    return {"results": results, "count": len(results), "timeframe": timeframe}


@router.get("/scan/{symbol}")
async def scan_symbol(request: Request, symbol: str, timeframe: str = "15m"):
    """Scan a single symbol."""
    exchange_mgr = request.app.state.exchange_manager
    fusion = request.app.state.fusion_engine

    data = await exchange_mgr.get_market_data(symbol, timeframe)
    signals = registry.run_all(data)
    fused = fusion.fuse(signals) if signals else None

    return {
        "symbol": symbol,
        "price": data.last_price,
        "signals": [s.model_dump() for s in signals],
        "fused": fused.model_dump() if fused else None,
        "divergence": fusion.analyze_divergence(signals),
    }


@router.get("/symbols")
async def get_symbols():
    """Get configured screener symbols."""
    return {"symbols": settings.screener_symbols}


@router.get("/status")
async def screener_status(request: Request):
    """Get screener status."""
    exchange_mgr = request.app.state.exchange_manager
    return {
        "connected_exchanges": exchange_mgr.get_connected_exchanges(),
        "symbols_count": len(settings.screener_symbols),
        "strategies_count": len(registry.get_enabled()),
        "trading_mode": settings.trading_mode.value,
        "fusion_mode": settings.fusion_mode.value,
    }
