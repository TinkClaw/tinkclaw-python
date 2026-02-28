"""
TinkClaw API Client

Official Python SDK for TinkClaw quant intelligence API.
Docs: https://tinkclaw.com/docs
"""

import requests
from typing import Optional, List, Dict, Any


class TinkClawClient:
    """
    TinkClaw API client for trading signals, confluence scoring, and market analysis.

    Usage:
        client = TinkClawClient(api_key="tinkclaw_free_xxx")
        signals = client.get_signals(["BTC", "ETH"])
        for s in signals:
            print(f"{s['symbol']}: {s['signal']} ({s['confidence']}%)")
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.tinkclaw.com"
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'X-API-Key': api_key,
            'User-Agent': 'TinkClaw-Python/0.5.0',
        })
        self._last_remaining = None

    def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make authenticated request to TinkClaw API."""
        url = f"{self.base_url}{endpoint}"
        response = self.session.request(method, url, timeout=15, **kwargs)

        # Track rate limit
        remaining = response.headers.get('X-RateLimit-Remaining')
        if remaining is not None:
            self._last_remaining = int(remaining)

        if response.status_code == 401:
            raise PermissionError("Invalid API key. Register at https://tinkclaw.com")
        if response.status_code == 429:
            raise RuntimeError("Rate limit exceeded. Upgrade at https://tinkclaw.com/pricing")
        response.raise_for_status()
        return response.json()

    @property
    def calls_remaining(self) -> Optional[int]:
        """Remaining API calls for today (updated after each request)."""
        return self._last_remaining

    # ==================== SIGNALS ====================

    def get_signals(self, symbols: List[str] = None) -> List[Dict[str, Any]]:
        """
        Get BUY/SELL/HOLD trading signals.

        Args:
            symbols: List of symbols (default: all tracked assets)

        Returns:
            List of signal dicts with: symbol, signal, confidence, price,
            target, stop_loss, signal_source, trade_type, region
        """
        params = {}
        if symbols:
            params['symbols'] = ','.join(symbols)
        data = self._request('GET', '/v1/signals', params=params)
        return data.get('signals', [])

    def get_top_signals(
        self,
        min_score: int = 60,
        limit: int = 10,
        direction: str = None,
    ) -> List[Dict[str, Any]]:
        """
        Get top trading signals sorted by confidence.

        Convenience wrapper around get_signals() that filters and ranks.

        Args:
            min_score: Minimum confidence score (0-100)
            limit: Max signals to return
            direction: Filter by "BUY" or "SELL" (default: all)

        Returns:
            List of signal dicts sorted by confidence (descending)
        """
        signals = self.get_signals()
        if direction:
            signals = [s for s in signals if s.get("signal") == direction]
        signals = [s for s in signals if s.get("confidence", 0) >= min_score]
        signals.sort(key=lambda s: s.get("confidence", 0), reverse=True)
        return signals[:limit]

    def get_signals_ml(self, symbols: List[str] = None) -> List[Dict[str, Any]]:
        """
        Get ML-enhanced trading signals (baseline + Random Forest).

        Args:
            symbols: List of symbols (default: ["BTC", "ETH"])

        Returns:
            List of ML signal dicts with: recommendation, confidence, source, baseline, ml
        """
        params = {}
        if symbols:
            params['symbols'] = ','.join(symbols)
        data = self._request('GET', '/v1/signals-ml', params=params)
        return data.get('signals', [])

    # ==================== ANALYSIS ====================

    def get_analysis(self, symbols=None) -> Any:
        """
        Get market analysis with trend, support/resistance, recommendation.

        Args:
            symbols: Symbol string or list of symbols. Single symbol returns flat object.
        """
        if isinstance(symbols, str):
            symbols = [symbols]
        if symbols and len(symbols) > 1:
            return self._request('GET', '/v1/analysis', params={'symbols': ','.join(symbols)})
        symbol = symbols[0] if symbols else 'BTC'
        return self._request('GET', '/v1/analysis', params={'symbol': symbol})

    def get_confluence(self, symbols=None, timeframes: List[int] = None) -> Any:
        """
        Get confluence score (6-layer: technical, sentiment, on-chain, macro, flow, quant).

        Args:
            symbols: Symbol string or list of symbols. Single symbol returns flat object.
            timeframes: Lookback periods in days (e.g., [7, 30, 90, 365])
        """
        if isinstance(symbols, str):
            symbols = [symbols]
        params = {}
        if symbols and len(symbols) > 1:
            params['symbols'] = ','.join(symbols)
        else:
            params['symbol'] = symbols[0] if symbols else 'BTC'
        if timeframes:
            params['timeframes'] = ','.join(str(t) for t in timeframes)
        return self._request('GET', '/v1/confluence', params=params)

    def get_indicators(self, symbol: str, range_days: int = 30) -> Dict[str, Any]:
        """
        Get technical indicators (RSI, MACD, Bollinger Bands, EMA, SMA, ATR).

        Args:
            symbol: Asset symbol
            range_days: Lookback period (7/30/90/365)
        """
        return self._request('GET', '/v1/indicators', params={'symbols': symbol, 'range': range_days})

    # ==================== QUANT ====================

    def get_risk_metrics(self, symbols: List[str] = None) -> Dict[str, Any]:
        """VaR, CVaR, Sharpe, Sortino, Max Drawdown, Calmar ratio."""
        params = {'symbols': ','.join(symbols)} if symbols else {}
        return self._request('GET', '/v1/risk-metrics', params=params)

    def get_correlation(self, symbols: List[str] = None) -> Dict[str, Any]:
        """Pairwise Pearson correlation matrix."""
        params = {'symbols': ','.join(symbols)} if symbols else {}
        return self._request('GET', '/v1/correlation', params=params)

    def get_screener(self) -> Dict[str, Any]:
        """Multi-asset screener with metrics for all supported symbols."""
        return self._request('GET', '/v1/screener')

    def get_cross_market(self, symbol: str = 'BTC') -> Dict[str, Any]:
        """Cross-market crypto-to-stock correlations and recommendations."""
        return self._request('GET', '/v1/cross-market', params={'symbol': symbol})

    # ==================== BACKTEST ====================

    def backtest(self, symbol: str, strategy: str = 'hurst_momentum', days: int = 365) -> Dict[str, Any]:
        """
        Run backtest with built-in strategy.

        Args:
            symbol: Asset symbol
            strategy: hurst_momentum, mean_reversion, breakout, ensemble
            days: Lookback period
        """
        return self._request('GET', '/v1/backtest', params={
            'symbol': symbol, 'strategy': strategy, 'days': days,
        })

    # ==================== MARKET DATA ====================

    def get_market_summary(self) -> Dict[str, Any]:
        """Comprehensive market overview for all asset classes."""
        return self._request('GET', '/v1/market-summary')

    def get_news(self, symbol: str = None) -> Dict[str, Any]:
        """Financial news from RSS feeds."""
        params = {'symbol': symbol} if symbol else {}
        return self._request('GET', '/v1/news', params=params)

    def get_indices(self) -> Dict[str, Any]:
        """Global stock market indices (S&P 500, DAX, Nikkei, etc.)."""
        return self._request('GET', '/v1/indices')

    def get_symbols(self) -> Dict[str, Any]:
        """List all supported trading symbols and asset classes."""
        return self._request('GET', '/v1/symbols')

    # ==================== WEBHOOKS ====================

    def subscribe_webhook(self, url: str, symbol: str, condition: str, threshold: float = None) -> Dict[str, Any]:
        """
        Subscribe to real-time alerts.

        Args:
            url: Your webhook endpoint URL
            symbol: Symbol to watch
            condition: confluence_gte, confluence_lte, rsi_gte, rsi_lte, price_gte, price_lte
            threshold: Trigger value
        """
        return self._request('POST', '/v1/webhooks/subscribe', json={
            'url': url, 'symbol': symbol, 'condition': condition, 'threshold': threshold,
        })

    def list_webhooks(self) -> List[Dict[str, Any]]:
        """List active webhook subscriptions."""
        data = self._request('GET', '/v1/webhooks')
        return data.get('webhooks', [])

    def delete_webhook(self, webhook_id: str) -> Dict[str, Any]:
        """Delete a webhook subscription by ID."""
        return self._request('DELETE', f'/v1/webhooks/{webhook_id}')

    # ==================== ACCOUNT ====================

    def get_usage(self) -> Dict[str, Any]:
        """Get API key usage stats for today."""
        return self._request('GET', '/v1/usage')

    def key_info(self) -> Dict[str, Any]:
        """Get API key metadata: plan, status, usage, remaining quota, key prefix."""
        return self._request('GET', '/v1/api-keys/info')

    def rotate_key(self) -> Dict[str, Any]:
        """
        Rotate API key. Returns a new key; old key stays active for 24 hours.

        After calling this, update your client with the new key:
            result = client.rotate_key()
            client = TinkClawClient(api_key=result['api_key'])
        """
        return self._request('POST', '/v1/api-keys/rotate')

    def health(self) -> Dict[str, Any]:
        """Check API health (unauthenticated)."""
        return requests.get(f"{self.base_url}/v1/health", timeout=5).json()

    # ==================== OPTIONS ====================

    def get_options_signals(self, underlyings: List[str] = None) -> List[Dict[str, Any]]:
        """
        Get options environment signals (IV rank, flow direction, Greeks context).
        Requires Pro+ ($149/mo) or Enterprise plan.

        Args:
            underlyings: List of underlying symbols (default: all tracked).
                         Available: AAPL, MSFT, NVDA, TSLA, AMZN, SPY, QQQ

        Returns:
            List of options signal dicts with: underlying, signal_type, severity,
            confidence, iv, iv_rank, iv_percentile, delta, gamma, theta, vega
        """
        params = {}
        if underlyings:
            params['underlyings'] = ','.join(underlyings)
        data = self._request('GET', '/v1/options/signals', params=params)
        return data.get('signals', [])

    # ==================== STREAMING ====================

    def get_stream_token(self) -> Dict[str, Any]:
        """
        Get a JWT token for WebSocket streaming.

        Returns:
            Dict with: token, expires_in, ws_url, plan, limits
        """
        return self._request('POST', '/v1/stream/token')

    def stream(self, symbols: List[str] = None, channels: List[str] = None):
        """
        Create a real-time streaming connection.

        Requires: pip install tinkclaw[streaming]

        Args:
            symbols: Symbols to subscribe to (default: ["BTC", "ETH"])
            channels: Channels to receive (default: ["tick", "candle:60", "signal"])

        Returns:
            TinkClawStream instance ready to start

        Usage:
            stream = client.stream(["BTC", "ETH"])

            @stream.on_tick
            def handle(tick):
                print(f"{tick['symbol']}: ${tick['price']}")

            stream.start()
        """
        from .streaming import TinkClawStream

        token_data = self.get_stream_token()
        s = TinkClawStream(
            token=token_data["token"],
            ws_url=token_data.get("ws_url", "wss://stream.tinkclaw.com"),
        )
        if symbols or channels:
            s.subscribe(symbols or ["BTC", "ETH"], channels)
        return s
