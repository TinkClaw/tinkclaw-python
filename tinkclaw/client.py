"""
TinkClaw API Client

Official Python SDK for TinkClaw quant intelligence API.
Docs: https://tinkclaw.com/docs
"""

import logging
import requests
from typing import Optional, List, Dict, Any

from . import __version__

log = logging.getLogger("tinkclaw.client")


class TinkClawClient:
    """
    TinkClaw API client for trading signals, confluence scoring, and market analysis.

    Usage:
        client = TinkClawClient(api_key="tinkclaw_free_xxx")
        signals = client.get_signals(["BTC", "ETH"])
        for s in signals:
            print(f"{s['symbol']}: {s['signal']} ({s['confidence']}%)")
    """

    VALID_STRATEGIES = {'hurst_momentum', 'mean_reversion', 'breakout', 'ensemble'}

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
            'User-Agent': f'TinkClaw-Python/{__version__}',
        })
        self._last_remaining = None

    def __repr__(self) -> str:
        # Bug #1: Mask API key more aggressively - show only first 4 chars
        key_preview = self.api_key[:4] + "****..." if len(self.api_key) > 4 else "****"
        return f"TinkClawClient(base_url='{self.base_url}', key='{key_preview}')"

    def close(self):
        """Close the underlying HTTP session."""
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def __del__(self):
        """Clean up session on garbage collection."""
        try:
            self.close()
        except Exception:
            pass

    def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make authenticated request to TinkClaw API."""
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.request(method, url, timeout=15, **kwargs)
        except requests.Timeout:
            # Bug #19: Separate timeout handling with clear message
            raise RuntimeError(f"Request to {endpoint} timed out after 15 seconds")

        # Track rate limit
        # Bug #3 & #17: Wrap in try/except to handle invalid values and clamp to 0
        remaining = response.headers.get('X-RateLimit-Remaining')
        if remaining is not None:
            try:
                value = int(remaining)
                # Bug #17: Clamp to non-negative
                self._last_remaining = max(0, value)
            except ValueError:
                log.warning("Invalid rate limit value: %s", remaining)

        if response.status_code == 401:
            # Bug #15: Change message for expired keys
            raise PermissionError("Invalid or expired API key")
        if response.status_code == 429:
            raise RuntimeError("Rate limit exceeded. Upgrade at https://tinkclaw.com/pricing")
        response.raise_for_status()
        try:
            return response.json()
        except ValueError:
            # Bug #13: Truncate to 100 chars and sanitize
            sanitized_text = response.text[:100].replace('\n', ' ')
            raise RuntimeError(
                f"Invalid JSON response from {endpoint} "
                f"(HTTP {response.status_code}): {sanitized_text}"
            )

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
            symbols: List of symbols (default: server default)

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
        if not symbols:
            symbols = ['BTC']
        # Bug #12: Normalize - always use 'symbol' for single, 'symbols' for multiple
        if len(symbols) > 1:
            return self._request('GET', '/v1/analysis', params={'symbols': ','.join(symbols)})
        symbol = symbols[0]
        return self._request('GET', '/v1/analysis', params={'symbol': symbol})

    def get_confluence(self, symbols=None, timeframes: List[int] = None) -> Any:
        """
        Get confluence score (6-layer: technical, fundamental, macro, flow, quant, cross-asset).

        Args:
            symbols: Symbol string or list of symbols. Single symbol returns flat object.
            timeframes: Lookback periods in days (e.g., [7, 30, 90, 365])
        """
        if isinstance(symbols, str):
            symbols = [symbols]
        if not symbols:
            symbols = ['BTC']
        params = {}
        if len(symbols) > 1:
            params['symbols'] = ','.join(symbols)
        else:
            params['symbol'] = symbols[0]
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
        # Bug #7: Fix inconsistent param key - should be 'symbol' not 'symbols'
        return self._request('GET', '/v1/indicators', params={'symbol': symbol, 'range': range_days})

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
        if strategy not in self.VALID_STRATEGIES:
            raise ValueError(f"Invalid strategy '{strategy}'. Must be one of: {', '.join(sorted(self.VALID_STRATEGIES))}")
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

    # ==================== ACCOUNT ====================

    def get_usage(self) -> Dict[str, Any]:
        """Get API key usage stats for today."""
        return self._request('GET', '/v1/usage')

    def key_info(self) -> Dict[str, Any]:
        """Get API key metadata: plan, status, usage, remaining quota, key prefix."""
        return self._request('GET', '/v1/api-keys/info')

    def health(self) -> Dict[str, Any]:
        """
        Check API health (unauthenticated).

        Note: Uses 5s timeout (shorter than other endpoints) for quick liveness checks.
        """
        response = requests.get(f"{self.base_url}/v1/health", timeout=5)
        try:
            return response.json()
        except ValueError:
            # Bug #21: Consistent error message (also truncated)
            sanitized_text = response.text[:100].replace('\n', ' ')
            raise RuntimeError(
                f"Invalid JSON from health endpoint "
                f"(HTTP {response.status_code}): {sanitized_text}"
            )

    # ==================== KEY MANAGEMENT ====================

    def rotate_key(self) -> Dict[str, Any]:
        """
        Rotate API key. Returns a new key with 24-hour grace period on the old one.

        Returns:
            Dict with: new_key, old_key_expires, message
        """
        data = self._request('POST', '/v1/api-keys/rotate')
        new_key = data.get('new_key') or data.get('api_key')
        if new_key:
            self.api_key = new_key
            self.session.headers['X-API-Key'] = new_key
        return data

    # ==================== WEBHOOKS ====================

    def subscribe_webhook(
        self,
        url: str,
        symbol: str,
        condition: str,
        threshold: float = None,
    ) -> Dict[str, Any]:
        """
        Subscribe a webhook URL to receive alerts when conditions are met.

        Args:
            url: HTTPS endpoint to receive POST requests
            symbol: Asset symbol (e.g., "BTC", "AAPL")
            condition: Alert condition. One of:
                confluence_gte, confluence_lte, rsi_gte, rsi_lte, price_gte, price_lte
            threshold: Numeric threshold for the condition

        Returns:
            Dict with: id, url, symbol, condition, threshold, status
        """
        if not url.startswith(('http://', 'https://')):
            raise ValueError("Webhook URL must start with http:// or https://")
        payload = {"url": url, "symbol": symbol, "condition": condition}
        if threshold is not None:
            payload["threshold"] = threshold
        return self._request('POST', '/v1/webhooks/subscribe', json=payload)

    def list_webhooks(self) -> List[Dict[str, Any]]:
        """List all registered webhooks for your API key."""
        data = self._request('GET', '/v1/webhooks')
        return data.get('webhooks', [])

    def delete_webhook(self, webhook_id: str) -> Dict[str, Any]:
        """Delete a webhook by ID."""
        return self._request('DELETE', f'/v1/webhooks/{webhook_id}')

    # ==================== REGIME DETECTION ====================

    def get_regime(self, symbol: str = None) -> Dict[str, Any]:
        """
        Get current market regime classification using probabilistic state detection.

        Returns regime state (calm, volatile, trending, crisis), confidence score,
        transition probabilities, and forecast for likely next state.

        Args:
            symbol: Asset symbol (default: overall market)

        Returns:
            Dict with: state, confidence, duration_minutes, transitions,
            most_likely_next, forecast_confidence
        """
        params = {'symbol': symbol} if symbol else {}
        return self._request('GET', '/v1/regime', params=params)

    # ==================== CROSS-ASSET INTELLIGENCE ====================

    def get_ecosystem(self) -> Dict[str, Any]:
        """
        Get cross-asset ecosystem analysis: inter-market correlations,
        sector momentum, leading/lagging sectors, and systemic risk score.

        Returns:
            Dict with: stock_crypto_corr, stock_forex_corr, crypto_forex_corr,
            sector_momentum, leading_sector, lagging_sector, avg_correlation,
            systemic_risk_score, conviction_score, narrative
        """
        return self._request('GET', '/v1/ecosystem')

    # ==================== ORDER FLOW ====================

    def get_flow(self, symbol: str) -> Dict[str, Any]:
        """
        Get institutional order flow metrics for a symbol.
        Requires Pro ($9.99/mo) plan.

        Derived from aggressor-side trade analysis and
        exchange trade direction. Includes flow imbalance,
        block trade detection, and VPIN.

        Args:
            symbol: Asset symbol (e.g., "AAPL", "BTC")

        Returns:
            Dict with: symbol, buy_volume, sell_volume, flow_imbalance,
            block_buy_volume, block_sell_volume, vpin, large_trade_ratio
        """
        return self._request('GET', f'/v1/flow/{symbol}')

    def get_flow_all(self) -> List[Dict[str, Any]]:
        """
        Get institutional order flow metrics for all tracked symbols.
        Requires Pro ($9.99/mo) plan.

        Returns:
            List of flow metric dicts sorted by absolute flow imbalance
        """
        data = self._request('GET', '/v1/flow')
        return data.get('flows', [])

    # ==================== OPTIONS ====================

    def get_options_signals(self, underlyings: List[str] = None) -> List[Dict[str, Any]]:
        """
        Get options environment signals (IV rank, flow direction, Greeks context).
        Requires Pro ($9.99/mo) plan.

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

    # ==================== FUNDAMENTALS ====================

    def get_fundamentals(self, symbol: str) -> Dict[str, Any]:
        """Get fundamental analysis data (sentiment, risk, growth scores from SEC filings)."""
        return self._request('GET', '/v1/fundamentals', params={'symbol': symbol})

    # ==================== SIGNALS HISTORY ====================

    def get_signals_history(self, symbol: str = None, limit: int = 50) -> Dict[str, Any]:
        """Get historical signal data."""
        params = {'limit': limit}
        if symbol:
            params['symbol'] = symbol
        return self._request('GET', '/v1/api/signals/history', params=params)

    # ==================== ADVANCED QUANT ====================

    def get_hurst_history(self, symbol: str = 'BTC', days: int = 365, window: int = 60) -> Dict[str, Any]:
        """Get historical Hurst exponent series for regime classification."""
        return self._request('GET', '/v1/hurst-history', params={
            'symbol': symbol, 'days': days, 'window': window,
        })

    def get_price_chart(self, symbol: str, days: int = 30) -> Dict[str, Any]:
        """Get OHLCV price chart data."""
        return self._request('GET', '/v1/price-chart', params={'symbol': symbol, 'days': days})

    def get_market_proficiency(self, symbol: str = None) -> Dict[str, Any]:
        """Get market proficiency scoring and analysis."""
        params = {'symbol': symbol} if symbol else {}
        return self._request('GET', '/v1/api/market/proficiency', params=params)

    def enhance_signal(self, symbol: str, signal: str, confidence: float) -> Dict[str, Any]:
        """Enhance a signal with LLM-powered contextual analysis."""
        return self._request('POST', '/v1/enhance-signal', json={
            'symbol': symbol, 'signal': signal, 'confidence': confidence,
        })

    def backtest_custom(self, symbol: str, strategy: Dict[str, Any], days: int = 365) -> Dict[str, Any]:
        """Run a custom backtest with user-defined strategy parameters."""
        return self._request('POST', '/v1/api/backtest/custom', json={
            'symbol': symbol, 'strategy': strategy, 'days': days,
        })

    def get_backtest_presets(self) -> Dict[str, Any]:
        """Get available backtest strategy presets."""
        return self._request('GET', '/v1/api/backtest/presets')

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
