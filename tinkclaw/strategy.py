"""
Strategy Base Class

Abstract base class for building trading strategies with TinkClaw signals.
"""

import time
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime


class Strategy(ABC):
    """
    Base class for trading strategies using TinkClaw confluence signals.

    Usage:
        class MyBot(Strategy):
            def on_signal(self, symbol, confluence):
                if confluence['score'] > 75:
                    self.buy(symbol, size=100)

        bot = MyBot(symbols=['BTC', 'ETH'], client=client)
        bot.run(interval_hours=4)
    """

    def __init__(
        self,
        symbols: List[str],
        client,
        broker=None
    ):
        self.symbols = symbols
        self.client = client
        self.broker = broker
        self.positions = {}
        self.signal_history = []

    @abstractmethod
    def on_signal(self, symbol: str, confluence: Dict[str, Any]) -> None:
        """Handle confluence signal for a symbol. Override with your strategy logic."""
        pass

    def run(self, interval_hours: float = 4, max_iterations: Optional[int] = None) -> None:
        """
        Run strategy in a loop.

        Args:
            interval_hours: Hours between signal checks (default: 4)
            max_iterations: Optional max iterations (default: infinite)
        """
        iteration = 0
        print(f"[TINKCLAW] Starting strategy for {len(self.symbols)} symbols")
        print(f"[TINKCLAW] Check interval: {interval_hours} hours")

        while True:
            if max_iterations and iteration >= max_iterations:
                break

            print(f"\n[TINKCLAW] Iteration {iteration + 1} - {datetime.now().isoformat()}")

            for symbol in self.symbols:
                try:
                    confluence = self.client.get_confluence(symbol)
                    self._log_signal(symbol, confluence)
                    self.on_signal(symbol, confluence)
                except Exception as e:
                    print(f"[ERROR] Failed to process {symbol}: {str(e)}")

            iteration += 1
            if max_iterations and iteration >= max_iterations:
                break

            time.sleep(interval_hours * 3600)

    def buy(self, symbol: str, size: float, reason: str = "") -> None:
        """Place buy order (via broker if configured, otherwise logs signal)."""
        if self.broker:
            self.broker.buy(symbol, size)
            print(f"[EXECUTE] Buy {size} {symbol} via {self.broker.__class__.__name__}")
        else:
            print(f"[SIGNAL] Buy {size} {symbol} {f'({reason})' if reason else ''}")
        self.positions[symbol] = self.positions.get(symbol, 0) + size

    def sell(self, symbol: str, size: float, reason: str = "") -> None:
        """Place sell order (via broker if configured, otherwise logs signal)."""
        if self.broker:
            self.broker.sell(symbol, size)
            print(f"[EXECUTE] Sell {size} {symbol} via {self.broker.__class__.__name__}")
        else:
            print(f"[SIGNAL] Sell {size} {symbol} {f'({reason})' if reason else ''}")
        self.positions[symbol] = self.positions.get(symbol, 0) - size

    def get_position(self, symbol: str) -> float:
        """Get current position size (positive = long, negative = short)."""
        return self.positions.get(symbol, 0)

    def _log_signal(self, symbol: str, confluence: Dict[str, Any]) -> None:
        self.signal_history.append({
            'timestamp': datetime.now().isoformat(),
            'symbol': symbol,
            'score': confluence.get('score'),
            'signal': confluence.get('signal'),
            'setup_type': confluence.get('setup_type')
        })
        print(f"[SIGNAL] {symbol}: score={confluence.get('score')}, "
              f"signal={confluence.get('signal')}, "
              f"setup={confluence.get('setup_type')}")
