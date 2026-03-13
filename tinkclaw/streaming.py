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
        # Bug #5: Use threading.Event instead of bare bool for thread-safe flag
        self._running = threading.Event()
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
        # Bug #9: Validate callback is callable
        if not callable(func):
            raise TypeError(f"on_tick callback must be callable, got {type(func)}")
        self._on_tick = func
        return func

    def on_candle(self, func: Callable) -> Callable:
        """Register a callback for candle data. Receives dict with symbol, interval, OHLCV."""
        # Bug #9: Validate callback is callable
        if not callable(func):
            raise TypeError(f"on_candle callback must be callable, got {type(func)}")
        self._on_candle = func
        return func

    def on_signal(self, func: Callable) -> Callable:
        """Register a callback for trading signals. Receives dict with symbol, signal, confidence."""
        # Bug #9: Validate callback is callable
        if not callable(func):
            raise TypeError(f"on_signal callback must be callable, got {type(func)}")
        self._on_signal = func
        return func

    def on_options_signal(self, func: Callable) -> Callable:
        """Register a callback for options signals. Receives dict with underlying, signal_type, iv, greeks."""
        # Bug #9: Validate callback is callable
        if not callable(func):
            raise TypeError(f"on_options_signal callback must be callable, got {type(func)}")
        self._on_options_signal = func
        return func

    def on_connect(self, func: Callable) -> Callable:
        """Register a callback for successful connection. Receives auth response dict."""
        # Bug #9: Validate callback is callable
        if not callable(func):
            raise TypeError(f"on_connect callback must be callable, got {type(func)}")
        self._on_connect = func
        return func

    def on_disconnect(self, func: Callable) -> Callable:
        """Register a callback for disconnection. Receives reason string."""
        # Bug #9: Validate callback is callable
        if not callable(func):
            raise TypeError(f"on_disconnect callback must be callable, got {type(func)}")
        self._on_disconnect = func
        return func

    def on_error(self, func: Callable) -> Callable:
        """Register a callback for errors. Receives error dict."""
        # Bug #9: Validate callback is callable
        if not callable(func):
            raise TypeError(f"on_error callback must be callable, got {type(func)}")
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
        # Bug #8: Validate that symbol list is not empty
        if not symbols:
            raise ValueError("symbols list cannot be empty")
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
        self._running.set()
        self._reconnect_delay = 1.0
        # Bug #2: Add max retry limit for auth failures specifically
        auth_failure_count = 0
        MAX_AUTH_FAILURES = 5

        while self._running.is_set():
            try:
                await self._connect_and_listen()
                auth_failure_count = 0  # Reset on success
            except PermissionError as e:
                # Bug #2: Track auth failures and give up after max retries
                auth_failure_count += 1
                if not self._running.is_set():
                    break
                log.error("Authentication failed: %s (attempt %d/%d)", e, auth_failure_count, MAX_AUTH_FAILURES)
                if auth_failure_count >= MAX_AUTH_FAILURES:
                    log.error("Max auth failures reached (%d). Stopping.", MAX_AUTH_FAILURES)
                    self._running.clear()
                    break
                if self._on_disconnect:
                    self._on_disconnect(str(e))
                if not self.reconnect:
                    break
                log.info("Reconnecting in %.1fs...", self._reconnect_delay)
                await asyncio.sleep(self._reconnect_delay)
                self._reconnect_delay = min(self._reconnect_delay * 2, self.max_reconnect_delay)
            except Exception as e:
                if not self._running.is_set():
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
        # Bug #5: Use threading.Event for thread-safe flag
        self._running.clear()
        if self._ws:
            try:
                loop = asyncio.get_running_loop()
                loop.call_soon_threadsafe(
                    lambda: asyncio.ensure_future(self._ws.close())
                )
            except RuntimeError:
                # No running loop — force close via new loop
                try:
                    asyncio.run(self._ws.close())
                except Exception:
                    pass

    # ── Internal ──────────────────────────────────────────────────

    async def _connect_and_listen(self):
        """Connect, authenticate, subscribe, and listen for messages."""
        ws = None
        try:
            async with websockets.connect(
                self.ws_url,
                ping_interval=30,
                ping_timeout=10,
                open_timeout=10,
                close_timeout=5,
            ) as ws:
                self._ws = ws

                # 1. Authenticate
                await ws.send(json.dumps({"type": "auth", "token": self.token}))
                # Bug #4: Wrap JSON parsing in try/catch
                try:
                    auth_response = json.loads(await ws.recv())
                except json.JSONDecodeError as e:
                    raise RuntimeError(f"Invalid JSON in auth response: {e}")

                if auth_response.get("type") == "error":
                    raise PermissionError(auth_response.get("message", "Authentication failed"))
                if auth_response.get("type") != "auth_ok":
                    raise RuntimeError(f"Unexpected auth response: {auth_response}")

                log.info("Authenticated: plan=%s", auth_response.get("plan"))
                self._reconnect_delay = 1.0  # Reset on successful connect

                if self._on_connect:
                    try:
                        self._on_connect(auth_response)
                    except Exception as e:
                        log.error("Error in on_connect callback: %s", e, exc_info=True)

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
                    if not self._running.is_set():
                        break
                    self._dispatch(raw)
        finally:
            # Bug #2: Ensure ws is closed in finally block
            self._ws = None
            if ws is not None:
                try:
                    await ws.close()
                except Exception:
                    pass

    def _dispatch(self, raw: str):
        """Route incoming message to the appropriate callback."""
        try:
            msg = json.loads(raw)
        except json.JSONDecodeError:
            # Bug #16: Add debug log for decode errors
            log.debug("JSON decode error in message: %s", raw[:200])
            return

        msg_type = msg.get("type")

        if msg_type == "data":
            channel = msg.get("channel", "")
            data = msg.get("data", {})

            # Bug #6: Wrap callback invocations in try/except
            if channel == "tick" and self._on_tick:
                try:
                    self._on_tick(data)
                except Exception as e:
                    log.error("Error in on_tick callback: %s", e, exc_info=True)
            elif channel.startswith("candle") and self._on_candle:
                try:
                    self._on_candle(data)
                except Exception as e:
                    log.error("Error in on_candle callback: %s", e, exc_info=True)
            elif channel == "signal" and self._on_signal:
                try:
                    self._on_signal(data)
                except Exception as e:
                    log.error("Error in on_signal callback: %s", e, exc_info=True)
            elif channel == "options_signal" and self._on_options_signal:
                try:
                    self._on_options_signal(data)
                except Exception as e:
                    log.error("Error in on_options_signal callback: %s", e, exc_info=True)

        elif msg_type == "error":
            log.warning("Server error: %s", msg.get("message"))
            if self._on_error:
                try:
                    self._on_error(msg)
                except Exception as e:
                    log.error("Error in on_error callback: %s", e, exc_info=True)

        elif msg_type == "pong":
            pass  # heartbeat response
