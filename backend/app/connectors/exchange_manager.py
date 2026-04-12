"""
Matreshka - Exchange Manager
Multi-exchange connection manager using CCXT.
"""
import asyncio
from typing import Dict, List, Optional
import ccxt.async_support as ccxt
import pandas as pd
from datetime import datetime

from ..config import settings, get_exchange_configs
from ..strategies.base import MarketData


class ExchangeManager:
    """Manages connections to multiple exchanges."""

    def __init__(self):
        self.exchanges: Dict[str, ccxt.Exchange] = {}
        self.default_exchange: str = "bybit"

    async def initialize(self):
        """Initialize exchange connections from config."""
        configs = get_exchange_configs()
        for name, cfg in configs.items():
            try:
                exchange_class = getattr(ccxt, name, None)
                if exchange_class is None:
                    print(f"Exchange {name} not found in CCXT")
                    continue
                exchange = exchange_class({
                    'apiKey': cfg['api_key'],
                    'secret': cfg['api_secret'],
                    'enableRateLimit': True,
                    'options': {'defaultType': 'swap'},
                })
                if cfg.get('testnet'):
                    exchange.set_sandbox_mode(True)
                await exchange.load_markets()
                self.exchanges[name] = exchange
                print(f"Connected to {name}: {len(exchange.markets)} markets")
            except Exception as e:
                print(f"Failed to connect to {name}: {e}")

        if self.exchanges:
            self.default_exchange = list(self.exchanges.keys())[0]

    async def close(self):
        """Close all exchange connections."""
        for name, exchange in self.exchanges.items():
            try:
                await exchange.close()
            except Exception:
                pass

    async def fetch_ohlcv(
        self, symbol: str, timeframe: str = "15m",
        limit: int = 200, exchange: str = None
    ) -> Optional[pd.DataFrame]:
        """Fetch OHLCV candles."""
        ex = self.exchanges.get(exchange or self.default_exchange)
        if not ex:
            return None
        try:
            data = await ex.fetch_ohlcv(symbol, timeframe, limit=limit)
            df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            return df
        except Exception as e:
            print(f"OHLCV error {symbol} on {exchange}: {e}")
            return None

    async def fetch_ticker(self, symbol: str, exchange: str = None) -> Optional[dict]:
        ex = self.exchanges.get(exchange or self.default_exchange)
        if not ex:
            return None
        try:
            return await ex.fetch_ticker(symbol)
        except Exception as e:
            print(f"Ticker error {symbol}: {e}")
            return None

    async def fetch_orderbook(self, symbol: str, limit: int = 20, exchange: str = None) -> Optional[dict]:
        ex = self.exchanges.get(exchange or self.default_exchange)
        if not ex:
            return None
        try:
            return await ex.fetch_order_book(symbol, limit=limit)
        except Exception as e:
            print(f"Orderbook error {symbol}: {e}")
            return None

    async def fetch_funding_rate(self, symbol: str, exchange: str = None) -> Optional[float]:
        ex = self.exchanges.get(exchange or self.default_exchange)
        if not ex:
            return None
        try:
            funding = await ex.fetch_funding_rate(symbol)
            return funding.get('fundingRate', 0)
        except Exception:
            return None

    async def get_market_data(
        self, symbol: str, timeframe: str = "15m",
        exchange: str = None, include_extras: bool = True
    ) -> MarketData:
        """Fetch complete market data for a symbol."""
        ex_name = exchange or self.default_exchange
        ohlcv = await self.fetch_ohlcv(symbol, timeframe, exchange=ex_name)
        funding = None
        orderbook = None

        if include_extras:
            funding, orderbook = await asyncio.gather(
                self.fetch_funding_rate(symbol, exchange=ex_name),
                self.fetch_orderbook(symbol, exchange=ex_name),
                return_exceptions=True
            )
            if isinstance(funding, Exception):
                funding = None
            if isinstance(orderbook, Exception):
                orderbook = None

        return MarketData(
            symbol=symbol,
            exchange=ex_name,
            ohlcv=ohlcv,
            funding_rate=funding,
            orderbook=orderbook,
        )

    async def get_all_symbols(self, exchange: str = None) -> List[str]:
        """Get all available USDT perpetual symbols."""
        ex = self.exchanges.get(exchange or self.default_exchange)
        if not ex:
            return []
        return [
            s for s in ex.markets
            if ex.markets[s].get('swap') and 'USDT' in s
        ]

    def get_connected_exchanges(self) -> List[str]:
        return list(self.exchanges.keys())

    # === Order execution ===
    async def create_order(
        self, symbol: str, side: str, amount: float,
        price: Optional[float] = None, order_type: str = "market",
        exchange: str = None, params: dict = None
    ) -> Optional[dict]:
        """Create an order on the exchange."""
        ex = self.exchanges.get(exchange or self.default_exchange)
        if not ex:
            return None
        try:
            order = await ex.create_order(
                symbol=symbol,
                type=order_type,
                side=side,
                amount=amount,
                price=price,
                params=params or {}
            )
            return order
        except Exception as e:
            print(f"Order error {symbol} {side}: {e}")
            return None

    async def get_positions(self, exchange: str = None) -> List[dict]:
        """Get open positions."""
        ex = self.exchanges.get(exchange or self.default_exchange)
        if not ex:
            return []
        try:
            positions = await ex.fetch_positions()
            return [p for p in positions if float(p.get('contracts', 0)) > 0]
        except Exception as e:
            print(f"Positions error: {e}")
            return []

    async def get_balance(self, exchange: str = None) -> Optional[dict]:
        ex = self.exchanges.get(exchange or self.default_exchange)
        if not ex:
            return None
        try:
            return await ex.fetch_balance()
        except Exception as e:
            print(f"Balance error: {e}")
            return None
