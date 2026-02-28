"""
TinkClaw Streaming Client

WebSocket client for real-time market data from TinkClaw.

Usage:
    from tinkclaw import TinkClawClient
    from tinkclaw.streaming import TinkClawStream

    client = TinkClawClient(api_key="tinkclaw_pro_xxx")
    stream = client.stream()

    @stream.on_tick
    def handle_tick(tick):
        print(f"{tick['symbol']}: ${tick['price']}")

    @stream.on_signal
    def handle_signal(signal):
        if signal['signal'] == 'SELL' and signal['confidence'] > 80:
            print(f"SELL {signal['symbol']}!")

    stream.subscribe(["BTC", "ETH"])
    stream.start()  # blocking

    # Or async:
    # await stream.start_async()
"""

import asyncio
import json
import logging
import threading
import time
from typing import Callable, Optional

try:
    import websockets
except ImportError:
    raise ImportError(
        "WebSocket streaming requires the 'websockets' package. "
        "Install it with: pip install tinkclaw[streaming]"
    )

log = logging.getLogger("tinkclaw.stream")


class TinkClawStream:
    """
    Real-time WebSocket streaming client for TinkClaw market data.

    Connects to stream.tinkclaw.com, authenticates with a JWT token,
    and dispatches ticks, candles, and signals to registered callbacks.
    """

    def __init__(
        self,
        token: str,
        ws_url: str = "wss://stream.tinkclaw.com",
        reconnect: bool = True,
        max_reconnect_delay: float = 60.0,
    ):
        self.token = token
        self.ws_url = ws_url
        self.reconnect = reconnect
        self.max_reconnect_delay = max_reconnect_delay

        self._ws = None
        self._running = False
        self._subscribed_symbols: list[str] = []
        self._channels: list[str] = ["tick", "candle:60", "signal"]
        self._reconnect_delay = 1.0

        # Callbacks
        self._on_tick: Optional[Callable] = None
        self._on_candle: Optional[Callable] = None
        self._on_signal: Optional[Callable] = None
        self._on_options_signal: Optional[Callable] = None
        self._on_connect: Optional[Callable] = None
        self._on_disconnect: Optional[Callable] = None
        self._on_error: Optional[Callable] = None

    # ── Decorators for registering callbacks ──────────────────────

    def on_tick(self, func: Callable) -> Callable:
        """Register a callback for tick data. Receives dict with symbol, price, volume, etc."""
        self._on_tick = func
        return func

    def on_candle(self, func: Callable) -> Callable:
        """Register a callback for candle data. Receives dict with symbol, interval, OHLCV."""
        self._on_candle = func
        return func

    def on_signal(self, func: Callable) -> Callable:
        """Register a callback for trading signals. Receives dict with symbol, signal, confidence."""
        self._on_signal = func
        return func

    def on_options_signal(self, func: Callable) -> Callable:
        """Register a callback for options signals. Receives dict with underlying, signal_type, iv, greeks."""
        self._on_options_signal = func
        return func

    def on_connect(self, func: Callable) -> Callable:
        """Register a callback for successful connection. Receives auth response dict."""
        self._on_connect = func
        return func

    def on_disconnect(self, func: Callable) -> Callable:
        """Register a callback for disconnection. Receives reason string."""
        self._on_disconnect = func
        return func

    def on_error(self, func: Callable) -> Callable:
        """Register a callback for errors. Receives error dict."""
        self._on_error = func
        return func

    # ── Configuration ─────────────────────────────────────────────

    def subscribe(self, symbols: list[str], channels: list[str] = None):
        """
        Set symbols and channels to subscribe to.

        Args:
            symbols: List of symbols (e.g., ["BTC", "ETH"])
            channels: List of channels (default: ["tick", "candle:60", "signal"])
                      Available: "tick", "candle:1", "candle:5", "candle:15", "candle:60", "candle:300", "signal"
        """
        self._subscribed_symbols = symbols
        if channels:
            self._channels = channels
        return self

    # ── Start/Stop ────────────────────────────────────────────────

    def start(self):
        """Start streaming in the current thread (blocking)."""
        asyncio.run(self.start_async())

    def start_background(self) -> threading.Thread:
        """Start streaming in a background thread. Returns the thread."""
        thread = threading.Thread(target=self.start, daemon=True)
        thread.start()
        return thread

    async def start_async(self):
        """Start streaming (async). Handles reconnection automatically."""
        self._running = True
        self._reconnect_delay = 1.0

        while self._running:
            try:
                await self._connect_and_listen()
            except Exception as e:
                if not self._running:
                    break
                log.warning("Connection lost: %s", e)
                if self._on_disconnect:
                    self._on_disconnect(str(e))
                if not self.reconnect:
                    break
                log.info("Reconnecting in %.1fs...", self._reconnect_delay)
                await asyncio.sleep(self._reconnect_delay)
                self._reconnect_delay = min(self._reconnect_delay * 2, self.max_reconnect_delay)

    def stop(self):
        """Stop streaming."""
        self._running = False
        if self._ws:
            asyncio.get_event_loop().call_soon_threadsafe(
                lambda: asyncio.ensure_future(self._ws.close())
            )

    # ── Internal ──────────────────────────────────────────────────

    async def _connect_and_listen(self):
        """Connect, authenticate, subscribe, and listen for messages."""
        async with websockets.connect(
            self.ws_url,
            ping_interval=30,
            ping_timeout=10,
        ) as ws:
            self._ws = ws

            # 1. Authenticate
            await ws.send(json.dumps({"type": "auth", "token": self.token}))
            auth_response = json.loads(await ws.recv())

            if auth_response.get("type") == "error":
                raise PermissionError(auth_response.get("message", "Authentication failed"))
            if auth_response.get("type") != "auth_ok":
                raise RuntimeError(f"Unexpected auth response: {auth_response}")

            log.info("Authenticated: plan=%s", auth_response.get("plan"))
            self._reconnect_delay = 1.0  # Reset on successful connect

            if self._on_connect:
                self._on_connect(auth_response)

            # 2. Subscribe
            if self._subscribed_symbols:
                await ws.send(json.dumps({
                    "type": "subscribe",
                    "symbols": self._subscribed_symbols,
                    "channels": self._channels,
                }))
                sub_response = json.loads(await ws.recv())
                log.info("Subscribed: %s", sub_response.get("symbols"))

            # 3. Listen
            async for raw in ws:
                if not self._running:
                    break
                self._dispatch(raw)

    def _dispatch(self, raw: str):
        """Route incoming message to the appropriate callback."""
        try:
            msg = json.loads(raw)
        except json.JSONDecodeError:
            return

        msg_type = msg.get("type")

        if msg_type == "data":
            channel = msg.get("channel", "")
            data = msg.get("data", {})

            if channel == "tick" and self._on_tick:
                self._on_tick(data)
            elif channel.startswith("candle") and self._on_candle:
                self._on_candle(data)
            elif channel == "signal" and self._on_signal:
                self._on_signal(data)
            elif channel == "options_signal" and self._on_options_signal:
                self._on_options_signal(data)

        elif msg_type == "error":
            log.warning("Server error: %s", msg.get("message"))
            if self._on_error:
                self._on_error(msg)

        elif msg_type == "pong":
            pass  # heartbeat response
