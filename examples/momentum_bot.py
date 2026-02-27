"""
Momentum Bot Example

Simple trading bot using TinkClaw confluence signals.
Buys on strong trending confluence, sells on weak signals.
"""

from tinkclaw import TinkClawClient, Strategy


class MomentumBot(Strategy):
    """
    Momentum trading strategy using TinkClaw confluence.

    Strategy logic:
    - BUY when score > 75 AND setup is trending
    - SELL when score < 40 OR setup is mean-reverting
    - Hold otherwise
    """

    def on_signal(self, symbol, confluence):
        score = confluence['score']
        setup = confluence['setup_type']
        signal = confluence['signal']

        current_position = self.get_position(symbol)

        # Entry logic: Buy on strong confluence + trending regime
        if score > 75 and setup == 'trending' and current_position == 0:
            self.buy(symbol, size=100, reason=f"Strong trending signal (score={score})")

        # Exit logic: Sell on weak confluence or mean-reverting regime
        elif (score < 40 or setup == 'mean_reverting') and current_position > 0:
            self.sell(symbol, size=current_position, reason=f"Weak signal (score={score})")

        # Hold logic
        else:
            print(f"[HOLD] {symbol}: position={current_position}, score={score}, setup={setup}")


if __name__ == "__main__":
    # Initialize TinkClaw client
    client = TinkClawClient(api_key="tinkclaw_free_YOUR_API_KEY")

    # Initialize bot
    bot = MomentumBot(
        symbols=['BTC', 'ETH', 'SOL'],
        client=client
    )

    # Run bot (checks every 4 hours)
    print("Starting Momentum Bot...")
    print("Watching: BTC, ETH, SOL")
    print("Interval: 4 hours")
    print("\nPress Ctrl+C to stop\n")

    try:
        bot.run(interval_hours=4)
    except KeyboardInterrupt:
        print("\n\nBot stopped by user")
        print(f"Final positions: {bot.positions}")
