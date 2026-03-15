# TinkClaw Python SDK

Official Python client for the [TinkClaw](https://tinkclaw.com) trading signals API.

Real-time AI-powered signals across 60+ assets — stocks, crypto, forex, and commodities.

## Install

```bash
pip install tinkclaw
```

## Quick Start

```python
from tinkclaw import TinkClaw

tc = TinkClaw(api_key="YOUR_KEY")

# Get signals
signals = tc.signals(symbols=["BTC", "ETH", "AAPL"])
for s in signals["signals"]:
    print(f"{s['symbol']}: {s['signal']} ({s['confidence']}%)")

# Confluence scoring
score = tc.confluence(symbol="BTC")
print(f"BTC confluence: {score['score']}/100")

# Quantitative analysis
risk = tc.risk_metrics(symbol="ETH")
print(f"ETH Sharpe: {risk['sharpe']}")
```

## Streaming

```python
from tinkclaw import StreamClient

stream = StreamClient(api_key="YOUR_KEY")

@stream.on("signal")
def on_signal(data):
    print(f"{data['symbol']}: {data['action']} @ {data['price']}")

stream.subscribe(["BTC", "ETH", "AAPL"])
stream.connect()
```

## Async

```python
from tinkclaw.client import AsyncTinkClaw

async def main():
    async with AsyncTinkClaw(api_key="YOUR_KEY") as tc:
        signals = await tc.signals(symbols=["BTC"])
        print(signals)
```

## Plans

| Plan | Credits/Month | Symbols | Streaming | Price |
|------|---------------|---------|-----------|-------|
| **Sandbox** | 100 | 5 (BTC, ETH, SOL, AAPL, EURUSD) | No | $0 |
| **Developer** | 5,000 | All 60+ | WebSocket, real-time | $29/mo |
| **Pro** | 15,000 | All 60+ | WebSocket, real-time | $79/mo |
| **Commercial** | 50,000 | All 60+ | WebSocket, real-time, priority | $299/mo |

**Sandbox** includes `/signals`, basic pattern detection, and community support.
**Developer** adds ML scoring, order flow (VPIN), regime detection, and email support.
**Pro** adds full confluence analysis, signal history export (90 days), webhook alerts, and priority support.
**Commercial** adds dedicated support, SLA guarantees, and custom integrations.

## API Reference

| Method | Description |
|--------|-------------|
| `signals()` | Rule-based signals |
| `signals_ml()` | ML-enhanced signals |
| `analysis(symbol)` | Full market analysis |
| `confluence(symbol)` | 6-layer confluence score |
| `indicators(symbol)` | Technical indicators |
| `quant(symbol)` | Fractal analysis + trend persistence |
| `risk_metrics(symbol)` | Sharpe, VaR, drawdown |
| `correlation()` | Cross-asset correlations |
| `screener()` | All assets ranked |
| `backtest(symbol, strategy)` | Strategy backtest |
| `market_summary()` | Full market overview |
| `news()` | Sentiment-scored news |
| `regime()` | Market regime detection |
| `webhook_subscribe()` | Alert webhooks |
| `usage()` | API usage stats |

Full docs: [tinkclaw.com/docs](https://tinkclaw.com/docs)

## Get an API Key

Sign up at [tinkclaw.com](https://tinkclaw.com) to get your free API key.
