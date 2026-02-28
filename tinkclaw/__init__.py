"""
TinkClaw Python SDK - Official API Client

Quant intelligence for trading bots. Signals, confluence scoring, and market analysis.

DISCLAIMER: TinkClaw provides algorithmic signals and data for informational
purposes only. TinkClaw is not a registered investment adviser, broker-dealer,
or financial planner. Signals are impersonal and not tailored to individual
financial situations. Trading involves substantial risk of loss. Past performance
does not guarantee future results. Consult a qualified financial professional
before making investment decisions.
"""

__version__ = "0.5.0"

from .client import TinkClawClient
from .strategy import Strategy
from .backtest import BacktestEngine

__all__ = ["TinkClawClient", "Strategy", "BacktestEngine"]
