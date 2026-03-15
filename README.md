# TinkClaw Python SDK

Official Python client for the [TinkClaw](https://tinkclaw.com) trading signals API.

Real-time AI-powered signals across 62 assets — stocks, crypto, forex, and commodities.

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

| Plan | Calls/Day | Symbols | Streaming | Price |
|------|-----------|---------|-----------|-------|
| **Free** | No API | SmartChart access | No | $0 |
| **Pro** | 50 | All 62 | WebSocket, real-time | $9.99/mo |
| **Pro+** | 100 | All 62 | WebSocket, real-time | $19.99/mo |

**Free** includes full SmartChart access with live signals — no API access.
**Pro** adds ML scoring, order flow (VPIN), regime detection, and email support.
**Pro+** adds full confluence analysis, signal history export (90 days), webhook alerts, and priority support.

## API Reference

| Method | Description |
|--------|-------------|
| `signals()` | Rule-based signals |
| `signals_ml()` | ML-enhanced signals |
| `analysis(symbol)` | Full market analysis |
| `confluence(symbol)` | 6-layer confluence score |
| `indicators(symbol)` | Technical indicators |
| `quant(symbol)` | MFDFA + Hurst exponent |
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
