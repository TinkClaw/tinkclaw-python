"""
TinkClaw Streaming Bot Example

Real-time trading bot using WebSocket streaming for sub-second signal delivery.
Requires: pip install tinkclaw[streaming]

This example shows:
1. Connecting to real-time tick data
2. Handling candle closes
3. Acting on real-time trading signals
4. Using the Strategy class in streaming mode
"""

from tinkclaw import TinkClawClient, Strategy


# ── Example 1: Simple tick listener ──────────────────────────────

def simple_stream():
    """Basic example — print live BTC/ETH prices."""
    client = TinkClawClient(api_key="tinkclaw_pro_YOUR_KEY")
    stream = client.stream(["BTC", "ETH"])

    @stream.on_tick
    def on_tick(tick):
        print(f"  {tick['symbol']}: ${tick['price']:,.2f} (vol: {tick['volume']:.4f})")

    @stream.on_signal
    def on_signal(signal):
        print(f"\n  ** {signal['signal']} {signal['symbol']} "
              f"@ ${signal['price']:,.2f} "
              f"(confidence: {signal['confidence']:.0f}%) **\n")

    @stream.on_connect
    def on_connect(info):
        print(f"Connected! Plan: {info['plan']}")

    print("Starting stream...")
    stream.start()  # blocking


# ── Example 2: Strategy class with streaming ─────────────────────

class ScalpBot(Strategy):
    """Scalping bot that reacts to real-time signals and candle closes."""

    def on_signal(self, symbol, data):
        """Handle real-time trading signals."""
        if data.get("signal") == "SELL" and data.get("confidence", 0) > 80:
            print(f"HIGH CONFIDENCE SELL on {symbol}!")
            self.sell(symbol, size=0.1, reason="RT signal >80%")

    def on_tick(self, symbol, tick):
        """Handle raw tick data — useful for spread monitoring."""
        # Example: monitor bid-ask spread
        bid = tick.get("bid", 0)
        ask = tick.get("ask", 0)
        if bid and ask:
            spread_bps = (ask - bid) / bid * 10000
            if spread_bps > 50:
                print(f"  Wide spread on {symbol}: {spread_bps:.1f} bps")

    def on_candle(self, symbol, candle):
        """Handle 1-minute candle close."""
        change_pct = (candle["close"] - candle["open"]) / candle["open"] * 100
        if abs(change_pct) > 0.5:
            print(f"  {symbol} 1m candle: {change_pct:+.2f}% "
                  f"(O={candle['open']:.2f} H={candle['high']:.2f} "
                  f"L={candle['low']:.2f} C={candle['close']:.2f})")


def streaming_strategy():
    """Run the ScalpBot with real-time data."""
    client = TinkClawClient(api_key="tinkclaw_pro_YOUR_KEY")
    bot = ScalpBot(symbols=["BTC", "ETH", "SOL"], client=client)
    bot.run_streaming(channels=["tick", "candle:60", "signal"])


if __name__ == "__main__":
    # Choose which example to run:
    simple_stream()
    # streaming_strategy()
