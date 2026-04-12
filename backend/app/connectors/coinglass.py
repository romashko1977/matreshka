"""
Matreshka - Coinglass API Client
Fetches OI, funding rates, liquidations, long/short ratio from Coinglass.
"""
import httpx
from typing import Optional, Dict, List
import pandas as pd
from datetime import datetime

from ..config import settings


class CoinglassClient:
    """Client for Coinglass API v4."""

    BASE_URL = "https://open-api-v3.coinglass.com/api"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.coinglass_api_key
        self.headers = {
            "accept": "application/json",
            "CG-API-KEY": self.api_key or "",
        }

    async def _get(self, endpoint: str, params: dict = None) -> Optional[dict]:
        if not self.api_key:
            return None
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{self.BASE_URL}{endpoint}",
                    headers=self.headers,
                    params=params or {},
                    timeout=15,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("success"):
                        return data.get("data")
                return None
        except Exception as e:
            print(f"Coinglass API error: {e}")
            return None

    async def get_open_interest(self, symbol: str = "BTC", interval: str = "h4") -> Optional[pd.DataFrame]:
        """Get open interest history."""
        data = await self._get("/futures/openInterest/ohlc-history", {
            "symbol": symbol, "interval": interval
        })
        if data:
            return pd.DataFrame(data)
        return None

    async def get_funding_rate(self, symbol: str = "BTC") -> Optional[Dict]:
        """Get current funding rates across exchanges."""
        return await self._get("/futures/funding/current", {"symbol": symbol})

    async def get_funding_history(self, symbol: str = "BTC") -> Optional[pd.DataFrame]:
        """Get funding rate history."""
        data = await self._get("/futures/funding/history", {"symbol": symbol})
        if data:
            return pd.DataFrame(data)
        return None

    async def get_liquidations(self, symbol: str = "BTC", interval: str = "h1") -> Optional[pd.DataFrame]:
        """Get liquidation data."""
        data = await self._get("/futures/liquidation/history", {
            "symbol": symbol, "interval": interval
        })
        if data:
            return pd.DataFrame(data)
        return None

    async def get_long_short_ratio(self, symbol: str = "BTC", interval: str = "h4") -> Optional[Dict]:
        """Get long/short account ratio."""
        return await self._get("/futures/globalLongShortAccountRatio/history", {
            "symbol": symbol, "interval": interval
        })

    async def get_oi_by_exchange(self, symbol: str = "BTC") -> Optional[List[Dict]]:
        """Get open interest breakdown by exchange."""
        return await self._get("/futures/openInterest/chart", {"symbol": symbol})

    async def get_aggregated_oi(self, symbol: str = "BTC") -> Optional[Dict]:
        """Get aggregated OI data."""
        return await self._get("/futures/openInterest/aggregated-ohlc", {"symbol": symbol})

    async def get_top_liquidations(self) -> Optional[List[Dict]]:
        """Get top liquidation events."""
        return await self._get("/futures/liquidation/order")

    async def get_full_symbol_data(self, symbol: str) -> Dict:
        """Get all available data for a symbol."""
        import asyncio
        oi, funding, liqs, ls_ratio = await asyncio.gather(
            self.get_open_interest(symbol),
            self.get_funding_rate(symbol),
            self.get_liquidations(symbol),
            self.get_long_short_ratio(symbol),
            return_exceptions=True
        )
        return {
            "open_interest": oi if not isinstance(oi, Exception) else None,
            "funding_rate": funding if not isinstance(funding, Exception) else None,
            "liquidations": liqs if not isinstance(liqs, Exception) else None,
            "long_short_ratio": ls_ratio if not isinstance(ls_ratio, Exception) else None,
        }
