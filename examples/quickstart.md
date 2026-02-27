# TinkClaw Quick Start

Get started with TinkClaw in 5 minutes.

## 1. Install TinkClaw

```bash
pip install tinkclaw
```

## 2. Get Your API Key

1. Visit [https://tinkclaw.com](https://tinkclaw.com)
2. Sign up for free Developer tier (50 calls/day)
3. Copy your API key

## 3. Basic Usage

```python
from tinkclaw import TinkClawClient

# Initialize client
client = TinkClawClient(api_key="your_key_here")

# Get confluence score
confluence = client.get_confluence("BTC")

print(f"Symbol: {confluence['symbol']}")
print(f"Score: {confluence['score']}")
print(f"Signal: {confluence['signal']}")
print(f"Setup: {confluence['setup_type']}")
```

## 4. Build a Simple Bot

```python
from tinkclaw import TinkClawClient, Strategy

class SimpleBot(Strategy):
    def on_signal(self, symbol, confluence):
        score = confluence['score']

        # Buy on strong signals
        if score > 75:
            self.buy(symbol, size=100)

        # Sell on weak signals
        elif score < 40:
            self.sell(symbol, size=100)

# Run bot
client = TinkClawClient(api_key="your_key_here")
bot = SimpleBot(symbols=['BTC', 'ETH'], client=client)
bot.run(interval_hours=4)
```

## 5. Integrate with Alpaca (Paper Trading)

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
bot = SimpleBot(
    symbols=['AAPL', 'TSLA'],
    client=client,
    broker=broker  # Trades will execute on Alpaca
)

bot.run(interval_hours=4)
```

## Rate Limits (Developer Tier)

- **50 calls/day** = 16 assets x 1 check/day OR 3 assets x 6 checks/day
- Recommended: Check every 4-6 hours for 3-5 assets

## Multi-Timeframe Analysis

```python
# Get confluence across multiple timeframes
confluence = client.get_confluence(
    symbol="BTC",
    timeframes=[7, 30, 90, 365]  # 1w, 1m, 3m, 1y
)

print(confluence)
```

## Next Steps

- See `examples/momentum_bot.py` for a complete working bot
- Explore other endpoints: `get_indicators()`, `get_history()`, `get_top_signals()`
- Upgrade to Builder tier ($29/mo) for 5,000 calls/day

## Support

- Docs: [https://tinkclaw.com/docs](https://tinkclaw.com/docs)
- Issues: [GitHub Issues](https://github.com/tinkclaw/tinkclaw-python/issues)
