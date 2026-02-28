# TinkClaw Python SDK

Official Python SDK for [TinkClaw](https://tinkclaw.com) quant intelligence API.

Build trading bots in minutes using confluence signals powered by Hurst exponent, autocorrelation, and regime detection.

## Features

- Simple API wrapper for all TinkClaw endpoints
- Strategy base class for custom bot logic
- Key management (info, rotation with 24h grace period)
- Webhook subscriptions for real-time alerts
- Alpaca paper trading integration
- Server-side backtesting via API
- Full typing support
- Zero heavy dependencies (just `requests`)

## Installation

```bash
pip install tinkclaw
```

## Quick Start (5 Minutes)

### 1. Get Your API Key

1. Visit [https://tinkclaw.com](https://tinkclaw.com)
2. Sign up for the Free tier (500 calls/day)
3. Copy your API key

### 2. Basic Usage

```python
from tinkclaw import TinkClawClient

client = TinkClawClient(api_key="tinkclaw_free_YOUR_KEY")

# Get trading signals
signals = client.get_signals(["BTC", "ETH"])
for s in signals:
    print(f"{s['symbol']}: {s['signal']} ({s['confidence']}%)")

# Get confluence score (6-layer weighted)
confluence = client.get_confluence("BTC")
print(f"Score: {confluence['score']}/100 — {confluence['recommendation']}")

# Check remaining calls
print(f"Calls remaining: {client.calls_remaining}")
```

### 3. Build a Trading Bot

```python
from tinkclaw import TinkClawClient, Strategy

class MomentumBot(Strategy):
    def on_signal(self, symbol, confluence):
        score = confluence['score']
        setup = confluence['setup_type']

        if score > 75 and setup == 'trending':
            self.buy(symbol, size=100)
        elif score < 40:
            self.sell(symbol, size=100)

client = TinkClawClient(api_key="tinkclaw_free_YOUR_KEY")
bot = MomentumBot(symbols=['BTC', 'ETH', 'SOL'], client=client)
bot.run(interval_hours=4)
```

### 4. Integrate with Alpaca Paper Trading

```python
from tinkclaw import TinkClawClient, Strategy
from tinkclaw.brokers import AlpacaBroker

broker = AlpacaBroker(
    api_key="your_alpaca_key",
    secret_key="your_alpaca_secret",
    paper=True
)

bot = MomentumBot(
    symbols=['AAPL', 'TSLA', 'NVDA'],
    client=client,
    broker=broker
)
bot.run(interval_hours=4)
```

## API Reference

### TinkClawClient

```python
client = TinkClawClient(api_key="tinkclaw_free_YOUR_KEY")

# Signals
signals = client.get_signals(["BTC", "ETH"])         # BUY/SELL/HOLD signals
ml_signals = client.get_signals_ml(["BTC"])           # ML-enhanced signals

# Analysis
analysis = client.get_analysis("BTC")                 # Technical analysis
confluence = client.get_confluence("BTC")              # 6-layer confluence score
indicators = client.get_indicators("ETH", range_days=30)

# Quant
risk = client.get_risk_metrics(["BTC", "ETH"])         # VaR, Sharpe, Sortino
correlation = client.get_correlation(["BTC", "ETH"])    # Correlation matrix
screener = client.get_screener()                        # All 34 assets at a glance
cross = client.get_cross_market("BTC")                  # Crypto-to-stock correlations

# Market Data
summary = client.get_market_summary()                   # Market overview
news = client.get_news("BTC")                           # Financial news
indices = client.get_indices()                           # Global stock indices
symbols = client.get_symbols()                           # Supported symbols

# Options (Pro+ / Enterprise only)
options = client.get_options_signals(["AAPL", "SPY"])  # IV rank, flow, Greeks signals

# Backtesting
result = client.backtest("BTC", strategy="hurst_momentum", days=365)

# Webhooks
client.subscribe_webhook("https://your-server.com/hook", "BTC", "confluence_gte", 80)
hooks = client.list_webhooks()
client.delete_webhook("wh_abc123")

# Account
usage = client.get_usage()                              # Daily usage stats
info = client.key_info()                                # Key metadata + quota
rotated = client.rotate_key()                           # Issue new key (24h grace)
health = client.health()                                # API health check
```

### Strategy Base Class

```python
class MyBot(Strategy):
    def on_signal(self, symbol, confluence):
        pass  # Your strategy logic

bot = MyBot(symbols=['BTC'], client=client, broker=None)
bot.run(interval_hours=4)
```

Methods:
- `on_signal(symbol, confluence)` - Override with your logic
- `buy(symbol, size, reason)` - Place buy order
- `sell(symbol, size, reason)` - Place sell order
- `get_position(symbol)` - Get current position
- `run(interval_hours, max_iterations)` - Run strategy loop

### AlpacaBroker

```python
from tinkclaw.brokers import AlpacaBroker

broker = AlpacaBroker(
    api_key="your_key",
    secret_key="your_secret",
    paper=True
)

broker.buy("AAPL", size=10)
broker.sell("AAPL", size=10)
position = broker.get_position("AAPL")
account = broker.get_account()
```

## Examples

See `examples/` directory:

- **momentum_bot.py** - Complete working bot using confluence signals
- **options_bot.py** - Options-aware bot with IV/Greeks signals (Pro+)
- **quickstart.md** - 5-minute integration guide

```bash
python examples/momentum_bot.py
```

## Rate Limits

| Plan | Calls/Day | Streaming | Options | Price | Use Case |
|------|-----------|-----------|---------|-------|----------|
| Free | 500 | None | No | $0 | Testing & prototyping |
| Starter | 5,000 | 1 conn, 3 symbols | No | $19/mo | Individual traders |
| Pro | 50,000 | 5 conn, 20 symbols | No | $59/mo | Production bots |
| Pro+ | 100,000 | 10 conn, all symbols | Yes | $149/mo | Professional firms |
| Enterprise | Unlimited | Unlimited | Yes | $499/mo | Institutional & white-label |

## Architecture

```
Your Bot
    |
TinkClaw SDK (pip install tinkclaw)
    |
TinkClaw API Gateway (api.tinkclaw.com)
    |
Quant Engine + ML Service
```

## Development

```bash
pip install -e ".[dev]"
pytest
```

## License

MIT License - see LICENSE file

## Support

- **Documentation**: [https://tinkclaw.com/docs](https://tinkclaw.com/docs)
- **API Status**: [https://api.tinkclaw.com/v1/health](https://api.tinkclaw.com/v1/health)
- **Issues**: [GitHub Issues](https://github.com/TinkClaw/tinkclaw-python/issues)

## Roadmap

- [x] Publish to PyPI
- [x] Key management (info, rotation)
- [x] WebSocket streaming for real-time signals (v0.4.0)
- [x] Options environment signals — IV rank, flow, Greeks (v0.5.0)
- [ ] Add more broker integrations (Interactive Brokers, Coinbase)
- [ ] Local backtesting engine with performance metrics (currently server-side)
- [ ] CLI tool for quick testing
- [ ] Jupyter notebook examples

## Disclaimer

TinkClaw is a publisher of algorithmic trading signals and quantitative market data for informational purposes only, pursuant to the Publisher's Exclusion under Section 202(a)(11)(D) of the Investment Advisers Act of 1940.

TinkClaw is **not** a registered investment adviser, broker-dealer, or financial planner. All signals, analysis, and data are general and impersonal — they are identical for all subscribers and are not tailored to any individual's financial situation, investment objectives, or risk tolerance. TinkClaw does not manage accounts, execute trades on behalf of users, or exercise discretionary authority over any subscriber's assets. No fiduciary relationship exists between TinkClaw and its users.

The optional broker integrations in this SDK are local developer utilities that run entirely on the user's machine using the user's own credentials. All trading and investment decisions are made solely by the user. Trading in securities involves substantial risk of loss. Past performance does not guarantee future results. Always consult a qualified financial professional before making investment decisions.

## Credits

Built by [TinkClaw](https://tinkclaw.com) — Quant intelligence for trading bots.
