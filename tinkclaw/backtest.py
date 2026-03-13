"""
Backtesting Harness

Local backtesting for TinkClaw strategies using historical data.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

log = logging.getLogger("tinkclaw.backtest")


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
        # Bug #10: Validate initial_capital > 0
        if initial_capital <= 0:
            raise ValueError(f"initial_capital must be > 0, got {initial_capital}")
        self.strategy = strategy
        self.start_date = datetime.fromisoformat(start_date)
        self.end_date = datetime.fromisoformat(end_date)
        # Bug #14: Validate end_date > start_date
        if self.end_date <= self.start_date:
            raise ValueError(f"end_date ({end_date}) must be after start_date ({start_date})")
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.trades = []
        self.equity_curve = []

    def run(self) -> Dict[str, Any]:
        """Run backtest and return performance metrics."""
        # Bug #20: Use logging instead of print
        log.info("Running from %s to %s", self.start_date.date(), self.end_date.date())
        log.info("Initial capital: $%.2f", self.initial_capital)

        for symbol in self.strategy.symbols:
            try:
                # Use server-side backtest API
                # Bug #18: Use strategy from self.strategy if available
                strategy_name = getattr(self.strategy, 'strategy', 'hurst_momentum')
                result = self.strategy.client.backtest(
                    symbol=symbol,
                    strategy=strategy_name,
                    days=(self.end_date - self.start_date).days,
                )
                self._process_backtest_result(symbol, result)
            except Exception as e:
                log.error("Error for %s: %s", symbol, str(e))

        return self._calculate_metrics()

    def _process_backtest_result(self, symbol: str, result: Dict[str, Any]) -> None:
        """Process server-side backtest result."""
        if 'trades' in result:
            self.trades.extend(result['trades'])
            for trade in result['trades']:
                pnl = trade.get('pnl', trade.get('profit', 0))
                if pnl:
                    self.capital += float(pnl)
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
