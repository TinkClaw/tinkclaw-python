"""Synchronous and asynchronous REST client for the TinkClaw API."""

from __future__ import annotations

import httpx

_DEFAULT_BASE = "https://api.tinkclaw.com"
_TIMEOUT = 30.0


class TinkClaw:
    """TinkClaw REST API client.

    Usage::

        tc = TinkClaw(api_key="YOUR_KEY")
        sigs = tc.signals(symbols=["BTC", "ETH"])
    """

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = _DEFAULT_BASE,
        timeout: float = _TIMEOUT,
    ) -> None:
        self._base = base_url.rstrip("/")
        self._client = httpx.Client(
            base_url=self._base,
            headers={"X-API-Key": api_key},
            timeout=timeout,
        )

    # ── helpers ────────────────────────────────────────────

    def _get(self, path: str, params: dict | None = None) -> dict:
        resp = self._client.get(path, params=params)
        resp.raise_for_status()
        return resp.json()

    def _post(self, path: str, json: dict | None = None) -> dict:
        resp = self._client.post(path, json=json)
        resp.raise_for_status()
        return resp.json()

    # ── Trading Signals ────────────────────────────────────

    def signals(self, symbols: list[str] | None = None) -> dict:
        """Rule-based signals with RSI, SMA analysis."""
        params = {}
        if symbols:
            params["symbols"] = ",".join(symbols)
        return self._get("/v1/signals", params)

    def signals_ml(self, symbols: list[str] | None = None) -> dict:
        """ML-enhanced signals (Random Forest + baseline consensus)."""
        params = {}
        if symbols:
            params["symbols"] = ",".join(symbols)
        return self._get("/v1/signals-ml", params)

    def analysis(self, symbol: str) -> dict:
        """Full market analysis: trend, support/resistance, Bollinger."""
        return self._get("/v1/analysis", {"symbol": symbol})

    # ── Market Data ────────────────────────────────────────

    def market_summary(self) -> dict:
        """Crypto, forex, commodities + sentiment (all assets)."""
        return self._get("/v1/market-summary")

    def news(self, limit: int = 20) -> dict:
        """Multi-source RSS with sentiment scoring."""
        return self._get("/v1/news", {"limit": limit})

    def indices(self) -> dict:
        """Major global stock indices."""
        return self._get("/v1/indices")

    # ── Quantitative Analysis ──────────────────────────────

    def quant(self, symbol: str) -> dict:
        """MFDFA regime + Hurst exponent."""
        return self._get("/v1/quant", {"symbol": symbol})

    def indicators(self, symbol: str) -> dict:
        """RSI, MACD, Bollinger, SMA, EMA, ATR."""
        return self._get("/v1/indicators", {"symbol": symbol})

    def hurst_history(self, symbol: str | None = None) -> dict:
        """Rolling Hurst timeseries."""
        params = {}
        if symbol:
            params["symbol"] = symbol
        return self._get("/v1/quant/hurst-history", params)

    def risk_metrics(self, symbol: str) -> dict:
        """Sharpe, Sortino, VaR, CVaR, max drawdown."""
        return self._get("/v1/quant/risk-metrics", {"symbol": symbol})

    def correlation(self) -> dict:
        """Cross-asset correlation matrix."""
        return self._get("/v1/quant/correlation")

    def screener(self) -> dict:
        """All assets with key metrics + Hurst."""
        return self._get("/v1/screener")

    # ── Confluence & Backtesting ───────────────────────────

    def confluence(self, symbol: str) -> dict:
        """6-layer weighted scoring (0-100) with volatility bands."""
        return self._get("/v1/confluence", {"symbol": symbol})

    def backtest(self, symbol: str, strategy: str = "hurst_momentum") -> dict:
        """Run a backtest with configurable strategy."""
        return self._get("/v1/quant/backtest", {"symbol": symbol, "strategy": strategy})

    # ── Webhooks & Utility ─────────────────────────────────

    def webhook_subscribe(
        self,
        url: str,
        symbol: str,
        condition: str = "confluence_gte",
        threshold: float = 90,
    ) -> dict:
        """Subscribe to webhook alerts."""
        return self._post("/v1/webhooks/subscribe", {
            "url": url,
            "symbol": symbol,
            "condition": condition,
            "threshold": threshold,
        })

    def webhooks(self) -> dict:
        """List your webhook subscriptions."""
        return self._get("/v1/webhooks")

    def usage(self) -> dict:
        """API key usage stats."""
        return self._get("/v1/usage")

    # ── Ecosystem & Regime ─────────────────────────────────

    def regime(self) -> dict:
        """Current market regime detection."""
        return self._get("/v1/regime")

    def ecosystem(self) -> dict:
        """Cross-asset ecosystem view."""
        return self._get("/v1/ecosystem")

    # ── lifecycle ──────────────────────────────────────────

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> TinkClaw:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()


class AsyncTinkClaw:
    """Async version of the TinkClaw REST client.

    Usage::

        async with AsyncTinkClaw(api_key="YOUR_KEY") as tc:
            sigs = await tc.signals(symbols=["BTC", "ETH"])
    """

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = _DEFAULT_BASE,
        timeout: float = _TIMEOUT,
    ) -> None:
        self._base = base_url.rstrip("/")
        self._client = httpx.AsyncClient(
            base_url=self._base,
            headers={"X-API-Key": api_key},
            timeout=timeout,
        )

    async def _get(self, path: str, params: dict | None = None) -> dict:
        resp = await self._client.get(path, params=params)
        resp.raise_for_status()
        return resp.json()

    async def _post(self, path: str, json: dict | None = None) -> dict:
        resp = await self._client.post(path, json=json)
        resp.raise_for_status()
        return resp.json()

    async def signals(self, symbols: list[str] | None = None) -> dict:
        params = {}
        if symbols:
            params["symbols"] = ",".join(symbols)
        return await self._get("/v1/signals", params)

    async def signals_ml(self, symbols: list[str] | None = None) -> dict:
        params = {}
        if symbols:
            params["symbols"] = ",".join(symbols)
        return await self._get("/v1/signals-ml", params)

    async def analysis(self, symbol: str) -> dict:
        return await self._get("/v1/analysis", {"symbol": symbol})

    async def market_summary(self) -> dict:
        return await self._get("/v1/market-summary")

    async def news(self, limit: int = 20) -> dict:
        return await self._get("/v1/news", {"limit": limit})

    async def indices(self) -> dict:
        return await self._get("/v1/indices")

    async def quant(self, symbol: str) -> dict:
        return await self._get("/v1/quant", {"symbol": symbol})

    async def indicators(self, symbol: str) -> dict:
        return await self._get("/v1/indicators", {"symbol": symbol})

    async def hurst_history(self, symbol: str | None = None) -> dict:
        params = {}
        if symbol:
            params["symbol"] = symbol
        return await self._get("/v1/quant/hurst-history", params)

    async def risk_metrics(self, symbol: str) -> dict:
        return await self._get("/v1/quant/risk-metrics", {"symbol": symbol})

    async def correlation(self) -> dict:
        return await self._get("/v1/quant/correlation")

    async def screener(self) -> dict:
        return await self._get("/v1/screener")

    async def confluence(self, symbol: str) -> dict:
        return await self._get("/v1/confluence", {"symbol": symbol})

    async def backtest(self, symbol: str, strategy: str = "hurst_momentum") -> dict:
        return await self._get("/v1/quant/backtest", {"symbol": symbol, "strategy": strategy})

    async def webhook_subscribe(self, url: str, symbol: str, condition: str = "confluence_gte", threshold: float = 90) -> dict:
        return await self._post("/v1/webhooks/subscribe", {"url": url, "symbol": symbol, "condition": condition, "threshold": threshold})

    async def webhooks(self) -> dict:
        return await self._get("/v1/webhooks")

    async def usage(self) -> dict:
        return await self._get("/v1/usage")

    async def regime(self) -> dict:
        return await self._get("/v1/regime")

    async def ecosystem(self) -> dict:
        return await self._get("/v1/ecosystem")

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> AsyncTinkClaw:
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.close()
