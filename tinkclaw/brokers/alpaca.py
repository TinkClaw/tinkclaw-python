"""
Alpaca Broker Integration

Paper and live trading via Alpaca Markets API.
"""

import requests
from typing import Optional


class AlpacaBroker:
    """
    Alpaca Markets broker integration for paper/live trading.

    Usage:
        broker = AlpacaBroker(
            api_key="your_key",
            secret_key="your_secret",
            paper=True
        )

        strategy = MyStrategy(symbols=['AAPL'], client=client, broker=broker)
        strategy.run()
    """

    def __init__(
        self,
        api_key: str,
        secret_key: str,
        paper: bool = True
    ):
        """
        Initialize Alpaca broker.

        Args:
            api_key: Alpaca API key
            secret_key: Alpaca secret key
            paper: Use paper trading (default: True)
        """
        self.api_key = api_key
        self.secret_key = secret_key
        self.paper = paper

        if paper:
            self.base_url = "https://paper-api.alpaca.markets"
        else:
            self.base_url = "https://api.alpaca.markets"

        self.headers = {
            'APCA-API-KEY-ID': api_key,
            'APCA-API-SECRET-KEY': secret_key
        }

    def _request(self, method: str, endpoint: str, **kwargs):
        """Make HTTP request to Alpaca API."""
        url = f"{self.base_url}{endpoint}"
        response = requests.request(method, url, headers=self.headers, **kwargs)
        response.raise_for_status()
        return response.json()

    def buy(self, symbol: str, size: float) -> dict:
        """
        Place market buy order.

        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            size: Number of shares or notional value in USD

        Returns:
            Order confirmation from Alpaca
        """
        order_data = {
            'symbol': symbol,
            'qty': size,
            'side': 'buy',
            'type': 'market',
            'time_in_force': 'day'
        }

        return self._request('POST', '/v2/orders', json=order_data)

    def sell(self, symbol: str, size: float) -> dict:
        """
        Place market sell order.

        Args:
            symbol: Stock symbol
            size: Number of shares or notional value in USD

        Returns:
            Order confirmation from Alpaca
        """
        order_data = {
            'symbol': symbol,
            'qty': size,
            'side': 'sell',
            'type': 'market',
            'time_in_force': 'day'
        }

        return self._request('POST', '/v2/orders', json=order_data)

    def get_position(self, symbol: str) -> Optional[dict]:
        """
        Get current position for a symbol.

        Args:
            symbol: Stock symbol

        Returns:
            Position data or None if no position
        """
        try:
            return self._request('GET', f'/v2/positions/{symbol}')
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return None
            raise

    def get_account(self) -> dict:
        """
        Get account information.

        Returns:
            Account data (cash, equity, buying power, etc.)
        """
        return self._request('GET', '/v2/account')

    def get_orders(self, status: str = 'open') -> list:
        """
        Get orders.

        Args:
            status: Order status ('open', 'closed', 'all')

        Returns:
            List of orders
        """
        params = {'status': status}
        return self._request('GET', '/v2/orders', params=params)
