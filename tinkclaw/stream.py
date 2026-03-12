"""WebSocket streaming client for real-time TinkClaw signals."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Callable

import websockets
import websockets.exceptions

_DEFAULT_WS_URL = "wss://stream.tinkclaw.com"
_RECONNECT_DELAY = 5
_MAX_RECONNECT_DELAY = 60

log = logging.getLogger("tinkclaw.stream")


class StreamClient:
    """Real-time WebSocket signal stream.

    Usage::

        stream = StreamClient(api_key="YOUR_KEY")

        @stream.on("signal")
        def handle(signal):
            print(signal["symbol"], signal["action"])

        stream.subscribe(["BTC", "ETH", "AAPL"])
        stream.connect()  # blocks forever
    """

    def __init__(
        self,
        api_key: str,
        *,
        url: str = _DEFAULT_WS_URL,
        auto_reconnect: bool = True,
    ) -> None:
        self._api_key = api_key
        self._url = url
        self._auto_reconnect = auto_reconnect
        self._symbols: list[str] = []
        self._handlers: dict[str, list[Callable]] = {}
        self._ws: websockets.WebSocketClientProtocol | None = None

    # ── public API ─────────────────────────────────────────

    def subscribe(self, symbols: list[str]) -> None:
        """Set the symbols to subscribe to on connect."""
        self._symbols = [s.upper() for s in symbols]

    def on(self, event: str) -> Callable:
        """Decorator to register an event handler.

        Events: ``signal``, ``connected``, ``disconnected``, ``error``
        """
        def decorator(fn: Callable) -> Callable:
            self._handlers.setdefault(event, []).append(fn)
            return fn
        return decorator

    def connect(self) -> None:
        """Connect and block forever (runs the asyncio event loop)."""
        asyncio.run(self.connect_async())

    async def connect_async(self) -> None:
        """Async connect — use this if you already have a running loop."""
        delay = _RECONNECT_DELAY
        while True:
            try:
                async with websockets.connect(self._url) as ws:
                    self._ws = ws
                    delay = _RECONNECT_DELAY

                    # Authenticate
                    await ws.send(json.dumps({
                        "action": "auth",
                        "api_key": self._api_key,
                    }))

                    # Subscribe
                    if self._symbols:
                        await ws.send(json.dumps({
                            "action": "subscribe",
                            "symbols": self._symbols,
                        }))

                    self._emit("connected", {})
                    log.info("Connected to %s", self._url)

                    async for raw in ws:
                        try:
                            msg = json.loads(raw)
                        except json.JSONDecodeError:
                            continue

                        event_type = msg.get("type", msg.get("event", "signal"))
                        self._emit(event_type, msg)

            except (
                websockets.exceptions.ConnectionClosed,
                websockets.exceptions.InvalidURI,
                OSError,
            ) as exc:
                self._ws = None
                self._emit("disconnected", {"reason": str(exc)})
                log.warning("Disconnected: %s", exc)

                if not self._auto_reconnect:
                    break

                log.info("Reconnecting in %ds…", delay)
                await asyncio.sleep(delay)
                delay = min(delay * 2, _MAX_RECONNECT_DELAY)

            except asyncio.CancelledError:
                break

        self._ws = None

    async def close(self) -> None:
        if self._ws:
            await self._ws.close()
            self._ws = None

    # ── internals ──────────────────────────────────────────

    def _emit(self, event: str, data: dict) -> None:
        for handler in self._handlers.get(event, []):
            try:
                handler(data)
            except Exception:
                log.exception("Handler error for event %s", event)
