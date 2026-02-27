"""
TinkClaw Python SDK - Official API Client

Quant intelligence for trading bots. Signals, confluence scoring, and market analysis.
"""

__version__ = "0.3.0"

from .client import TinkClawClient
from .strategy import Strategy
from .backtest import BacktestEngine

__all__ = ["TinkClawClient", "Strategy", "BacktestEngine"]
