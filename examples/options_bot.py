#!/usr/bin/env python3
"""
TinkClaw Options-Aware Trading Bot Example

Demonstrates how to receive and act on options environment signals
(IV spikes, flow direction, Greeks anomalies) alongside regular
stock/crypto signals.

Requires: Pro+ ($149/mo) or Enterprise plan for options signals.

Usage:
    export TINKCLAW_API_KEY="tinkclaw_pro_plus_YOUR_KEY"
    pip install tinkclaw[streaming]
    python options_bot.py
"""

import os
from tinkclaw import TinkClawClient, Strategy


class OptionsAwareBot(Strategy):
    """A strategy that combines stock signals with options environment data."""

    def on_signal(self, symbol, data):
        """Handle regular stock/crypto BUY/SELL/HOLD signals."""
        signal = data.get("signal", "HOLD")
        confidence = data.get("confidence", 0)
        price = data.get("price", 0)

        if signal == "BUY" and confidence > 0.8:
            print(f"  [STOCK] {symbol} BUY at ${price:.2f} (confidence: {confidence:.0%})")
            self.buy(symbol, size=10, reason=f"confidence {confidence:.0%}")
        elif signal == "SELL" and confidence > 0.8:
            print(f"  [STOCK] {symbol} SELL at ${price:.2f} (confidence: {confidence:.0%})")
            self.sell(symbol, size=10, reason=f"confidence {confidence:.0%}")

    def on_options_signal(self, underlying, signal):
        """Handle options environment signals — IV rank, flow, Greeks."""
        signal_type = signal.get("signal_type", "")
        severity = signal.get("severity", "low")
        iv = signal.get("iv", 0)
        iv_rank = signal.get("iv_rank", 0)
        confidence = signal.get("confidence", 0)

        print(f"\n  [OPTIONS] {underlying}: {signal_type} (severity: {severity})")
        print(f"           IV: {iv:.1%} | IV Rank: {iv_rank:.0f} | Confidence: {confidence:.0%}")
        print(f"           Delta: {signal.get('delta', 0):.4f} | "
              f"Gamma: {signal.get('gamma', 0):.4f} | "
              f"Theta: {signal.get('theta', 0):.4f}")

        # React to high-severity options events
        if signal_type == "IV_SPIKE" and severity == "high":
            print(f"  ** ALERT: {underlying} IV spiking — consider selling premium **")

        elif signal_type == "IV_CRUSH" and severity in ("high", "medium"):
            print(f"  ** OPPORTUNITY: {underlying} IV crushed — consider buying premium **")

        elif signal_type == "GAMMA_SQUEEZE":
            print(f"  ** WARNING: {underlying} gamma squeeze — expect amplified moves **")

        elif signal_type == "BULLISH_FLOW":
            print(f"  ** INFO: {underlying} bullish options flow detected **")

        elif signal_type == "BEARISH_FLOW":
            print(f"  ** INFO: {underlying} bearish options flow detected **")


def main():
    api_key = os.getenv("TINKCLAW_API_KEY", "tinkclaw_pro_plus_YOUR_KEY")
    client = TinkClawClient(api_key=api_key)

    # Symbols to track (options signals available for: AAPL, MSFT, NVDA, TSLA, AMZN, SPY, QQQ)
    symbols = ["AAPL", "NVDA", "SPY"]

    # --- REST API example ---
    print("=== Options Signals (REST) ===")
    try:
        options_signals = client.get_options_signals(symbols)
        for sig in options_signals:
            print(f"  {sig['underlying']}: {sig['signal_type']} "
                  f"(IV rank: {sig['iv_rank']:.0f}, confidence: {sig['confidence']:.0%})")
    except Exception as e:
        print(f"  REST error (need Pro+ plan): {e}")

    # --- Streaming example ---
    print("\n=== Starting Streaming Bot ===")
    bot = OptionsAwareBot(symbols=symbols, client=client)

    # Subscribe to both regular signals and options signals
    bot.run_streaming(channels=["signal", "options_signal"])


if __name__ == "__main__":
    main()
