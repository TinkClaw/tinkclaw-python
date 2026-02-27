"""
Backtesting Harness

Local backtesting for TinkClaw strategies using historical data.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta


class BacktestEngine:
    """
    Simple backtesting engine for TinkClaw strategies.

    Usage:
        engine = BacktestEngine(strategy, start_date="2025-01-01", end_date="2026-01-01")
        results = engine.run()
        print(f"Total return: {results['total_return']}%")
    """

    def __init__(
        self,
        strategy,
        start_date: str,
        end_date: str,
        initial_capital: float = 10000.0
    ):
        self.strategy = strategy
        self.start_date = datetime.fromisoformat(start_date)
        self.end_date = datetime.fromisoformat(end_date)
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.trades = []
        self.equity_curve = []

    def run(self) -> Dict[str, Any]:
        """Run backtest and return performance metrics."""
        print(f"[BACKTEST] Running from {self.start_date.date()} to {self.end_date.date()}")
        print(f"[BACKTEST] Initial capital: ${self.initial_capital:,.2f}")

        for symbol in self.strategy.symbols:
            try:
                # Use server-side backtest API
                result = self.strategy.client.backtest(
                    symbol=symbol,
                    strategy='hurst_momentum',
                    days=(self.end_date - self.start_date).days,
                )
                self._process_backtest_result(symbol, result)
            except Exception as e:
                print(f"[BACKTEST] Error for {symbol}: {str(e)}")

        return self._calculate_metrics()

    def _process_backtest_result(self, symbol: str, result: Dict[str, Any]) -> None:
        """Process server-side backtest result."""
        if 'trades' in result:
            self.trades.extend(result['trades'])
        if 'equity_curve' in result:
            self.equity_curve.extend(result['equity_curve'])

    def _calculate_metrics(self) -> Dict[str, Any]:
        total_return = ((self.capital - self.initial_capital) / self.initial_capital) * 100
        return {
            'initial_capital': self.initial_capital,
            'final_capital': self.capital,
            'total_return': round(total_return, 2),
            'num_trades': len(self.trades),
            'equity_curve': self.equity_curve,
        }
