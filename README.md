# TinkClaw Python SDK

Official Python SDK for [TinkClaw](https://tinkclaw.com) quant intelligence API.

Build trading bots in minutes using confluence signals powered by Hurst exponent, autocorrelation, and regime detection.

## Features

- Simple API wrapper for TinkClaw endpoints
- Strategy base class for custom bot logic
- Alpaca paper trading integration
- Local backtesting harness
- Full typing support
- Zero heavy dependencies (just `requests`)

## Installation

```bash
pip install -e .
```

Or from PyPI (coming soon):

```bash
pip install tinkclaw
```

## Quick Start (5 Minutes)

### 1. Get Your API Key

1. Visit [https://tinkclaw.com](https://tinkclaw.com)
2. Sign up for free Developer tier (50 calls/day)
3. Copy your API key

### 2. Basic Usage

```python
from tinkclaw import TinkClawClient

# Initialize client
client = TinkClawClient(api_key="your_key_here")

# Get confluence score
confluence = client.get_confluence("BTC")

print(f"Symbol: {confluence['symbol']}")
print(f"Score: {confluence['score']}")        # 0-100
print(f"Signal: {confluence['signal']}")      # strong_buy, buy, hold, sell, strong_sell
print(f"Setup: {confluence['setup_type']}")   # trending, mean_reverting, uncertain
```

### 3. Build a Trading Bot

```python
from tinkclaw import TinkClawClient, Strategy

class MomentumBot(Strategy):
    def on_signal(self, symbol, confluence):
        score = confluence['score']
        setup = confluence['setup_type']

        # Buy on strong confluence + trending regime
        if score > 75 and setup == 'trending':
            self.buy(symbol, size=100)

        # Sell on weak confluence
        elif score < 40:
            self.sell(symbol, size=100)

# Run bot
client = TinkClawClient(api_key="your_key_here")
bot = MomentumBot(symbols=['BTC', 'ETH', 'SOL'], client=client)
bot.run(interval_hours=4)  # Check every 4 hours
```

Output:
```
[TINKCLAW] Starting strategy for 3 symbols
[TINKCLAW] Check interval: 4 hours

[TINKCLAW] Iteration 1 - 2026-02-21T10:00:00
[SIGNAL] BTC: score=78, signal=strong_buy, setup=trending
[SIGNAL] Buy 100 BTC (Strong trending signal (score=78))
[SIGNAL] ETH: score=65, signal=buy, setup=trending
[HOLD] ETH: position=0, score=65, setup=trending
[SIGNAL] SOL: score=42, signal=hold, setup=uncertain
[HOLD] SOL: position=0, score=42, setup=uncertain
```

### 4. Integrate with Alpaca Paper Trading

```python
from tinkclaw import TinkClawClient, Strategy
from tinkclaw.brokers import AlpacaBroker

# Initialize broker
broker = AlpacaBroker(
    api_key="your_alpaca_key",
    secret_key="your_alpaca_secret",
    paper=True  # Paper trading
)

# Initialize strategy with broker
bot = MomentumBot(
    symbols=['AAPL', 'TSLA', 'NVDA'],
    client=client,
    broker=broker  # Trades will execute on Alpaca
)

bot.run(interval_hours=4)
```

Output:
```
[EXECUTE] Buy 100 AAPL via AlpacaBroker
[EXECUTE] Sell 50 TSLA via AlpacaBroker
```

## API Reference

### TinkClawClient

```python
client = TinkClawClient(api_key="your_key")

# Get confluence score
confluence = client.get_confluence("BTC")

# Multi-timeframe analysis
confluence = client.get_confluence("BTC", timeframes=[7, 30, 90, 365])

# Get technical indicators
indicators = client.get_indicators("ETH", range_days=30)

# Get historical signals
history = client.get_history("SOL", limit=100)

# Get top signals across all assets
top = client.get_top_signals(min_score=70, limit=10)

# Health check
health = client.health()
```

### Strategy Base Class

```python
class MyBot(Strategy):
    def on_signal(self, symbol, confluence):
        # Your strategy logic here
        pass

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
    paper=True  # Use paper trading
)

# Place orders
broker.buy("AAPL", size=10)
broker.sell("AAPL", size=10)

# Get position
position = broker.get_position("AAPL")

# Get account info
account = broker.get_account()
```

## Examples

See `examples/` directory:

- **momentum_bot.py** - Complete working bot using confluence signals
- **quickstart.md** - 5-minute integration guide

Run the example:

```bash
python examples/momentum_bot.py
```

## Rate Limits

| Tier | Calls/Day | Price | Use Case |
|------|-----------|-------|----------|
| Developer | 50 | Free | Testing (3 assets x 6 checks/day) |
| Builder | 5,000 | $29/mo | Prod bots (10 assets x 24 checks/day) |
| Pro | 50,000 | $99/mo | Multi-strategy systems |
| Enterprise | Custom | Custom | Institutional use |

**Developer Tier Optimization:**
- Check every 4-6 hours (not hourly)
- Monitor 3-5 assets max
- 50 calls/day = 3 assets x 6 checks/day (every 4 hours)

## Advanced Features

### Multi-Timeframe Analysis

```python
confluence = client.get_confluence(
    symbol="BTC",
    timeframes=[7, 30, 90, 365]  # 1w, 1m, 3m, 1y
)

# Returns confluence across all timeframes
print(confluence['multi_timeframe'])
```

### Backtesting (Coming Soon)

```python
from tinkclaw import BacktestEngine

engine = BacktestEngine(
    strategy=bot,
    start_date="2025-01-01",
    end_date="2026-01-01",
    initial_capital=10000
)

results = engine.run()
print(f"Total return: {results['total_return']}%")
```

## Architecture

```
Your Bot
    |
TinkClaw SDK
    |
TinkClaw API (meshcue-api.dieubuhendwa.workers.dev)
    |
TinkClaw Backend (Cloudflare Workers + KV)
```

## Development

Install dev dependencies:

```bash
pip install -e ".[dev]"
```

Run tests:

```bash
pytest
```

Format code:

```bash
black tinkclaw/
```

## License

MIT License - see LICENSE file

## Support

- **Documentation**: [https://tinkclaw.com/docs](https://tinkclaw.com/docs)
- **API Status**: [https://meshcue-api.dieubuhendwa.workers.dev/api/signals/health](https://meshcue-api.dieubuhendwa.workers.dev/api/signals/health)
- **Issues**: [GitHub Issues](https://github.com/tinkclaw/tinkclaw-python/issues)

## Roadmap

- [ ] Publish to PyPI
- [ ] Add more broker integrations (Interactive Brokers, Coinbase)
- [ ] Complete backtesting engine with performance metrics
- [ ] Add WebSocket streaming for real-time signals
- [ ] CLI tool for quick testing
- [ ] Jupyter notebook examples

## Credits

Built by [Meshcue](https://meshcue.com) - Global platform for quant intelligence.
