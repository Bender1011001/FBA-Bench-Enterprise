"""
FBA-Bench v3 Jupyter Connector - Observer Mode

This module provides a secure, read-only interface for connecting Jupyter notebooks
to live FBA-Bench simulations. The connector operates in strict observer mode,
ensuring no notebook can alter simulation state.

Core Architecture:
- Leverages existing DashboardAPIService via FastAPI endpoints
- Maintains real-time sync with simulation via WebSocket
- Exposes Pandas-friendly data structures for analysis
- Zero write capabilities - pure observer pattern
"""

import asyncio
import json
import logging
import os
import threading
import time
from collections import deque
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

import pandas as pd
import requests
import websockets
from websockets.exceptions import ConnectionClosed

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    A simple token bucket rate limiter for controlling API call frequency.
    """

    def __init__(self, rate_per_second: float, burst: int):
        self.rate = rate_per_second
        self.burst = burst
        self.tokens = burst
        self.last_refill = time.monotonic()
        self._lock = threading.Lock()

    def _refill(self):
        now = time.monotonic()
        time_passed = now - self.last_refill
        new_tokens = time_passed * self.rate
        self.tokens = min(self.burst, self.tokens + new_tokens)
        self.last_refill = now

    def acquire(self, amount: int = 1) -> bool:
        """
        Acquires a specified amount of tokens from the bucket.
        Returns True if tokens were acquired, False otherwise.
        """
        with self._lock:
            self._refill()
            if self.tokens >= amount:
                self.tokens -= amount
                return True
            return False

    async def wait_for_token(self, amount: int = 1, timeout: Optional[float] = None) -> bool:
        """
        Waits for a specified amount of tokens to become available.
        Returns True if tokens were acquired within the timeout, False otherwise.
        """
        start_time = time.monotonic()
        while not self.acquire(amount):
            if timeout is not None and time.monotonic() - start_time > timeout:
                return False
            await asyncio.sleep(0.05)
        return True

    def wait_for_token_sync(self, amount: int = 1, timeout: Optional[float] = None) -> bool:
        """
        Synchronous variant of wait_for_token. Blocks the current thread until tokens are available
        or timeout elapses.

        Returns:
            True if tokens were acquired within the timeout, False otherwise.
        """
        start_time = time.monotonic()
        while not self.acquire(amount):
            if timeout is not None and time.monotonic() - start_time > timeout:
                return False
            time.sleep(0.05)
        return True


class JupyterConnector:
    """
    Secure, read-only connector for FBA-Bench simulation analysis.

    This class connects to a running api_server.py instance and provides
    real-time access to simulation data via Pandas DataFrames and event streams.

    Features:
    - Automatic WebSocket reconnection
    - Thread-safe data access
    - Real-time event buffering
    - Multiple data export formats (DataFrame, JSON, dict)
    - Zero simulation write capabilities (observer mode)
    """

    def __init__(
        self,
        api_base_url: str = os.getenv("FBA_API_BASE_URL", "http://localhost:8000"),
        websocket_url: str = os.getenv("FBA_WEBSOCKET_URL", "ws://localhost:8000/ws/events"),
        api_key: Optional[str] = os.getenv("FBA_API_KEY"),
        event_buffer_size: int = 1000,
        api_call_rate_limit: float = 10.0,  # 10 calls per second
        api_call_burst: int = 20,  # Burst capacity for rate limiter
        api_timeout_seconds: float = 30.0,  # Default API timeout
        websocket_reconnect_delay: float = 5.0,
    ):  # Delay before WebSocket reconnection
        """
        Initialize Jupyter connector to FBA-Bench simulation.

        Args:
            api_base_url: Base URL of the FastAPI server
            websocket_url: WebSocket endpoint for real-time events
            api_key: Optional API key for authentication with the FBA-Bench API.
            event_buffer_size: Maximum events to keep in memory buffer
            api_call_rate_limit: Rate limit for API calls (calls per second)
            api_call_burst: Burst capacity for the API rate limiter
            api_timeout_seconds: Timeout for API HTTP requests in seconds
            websocket_reconnect_delay: Delay in seconds before attempting WebSocket reconnection
        """
        # Ensure URLs are properly formatted
        if not (api_base_url.startswith("http://") or api_base_url.startswith("https://")):
            raise ValueError("API base URL must start with 'http://' or 'https://'")
        if not (websocket_url.startswith("ws://") or websocket_url.startswith("wss://")):
            raise ValueError("WebSocket URL must start with 'ws://' or 'wss://'")

        self.api_base_url = api_base_url.rstrip("/")
        self.websocket_url = websocket_url
        self.api_key = api_key
        self.event_buffer_size = event_buffer_size
        self.api_timeout_seconds = api_timeout_seconds
        self.websocket_reconnect_delay = websocket_reconnect_delay

        # Initialize rate limiter for API calls
        self._rate_limiter = RateLimiter(api_call_rate_limit, api_call_burst)

        # Log when using fallback defaults; in production prefer env/config
        if "FBA_API_BASE_URL" not in os.environ and (
            "localhost" in self.api_base_url or "127.0.0.1" in self.api_base_url
        ):
            logger.debug(
                "Using default API base URL %s; set FBA_API_BASE_URL to override in production",
                self.api_base_url,
            )
        if "FBA_WEBSOCKET_URL" not in os.environ and (
            "localhost" in self.websocket_url or "127.0.0.1" in self.websocket_url
        ):
            logger.debug(
                "Using default WebSocket URL %s; set FBA_WEBSOCKET_URL to override in production",
                self.websocket_url,
            )
        if self.api_key is None:
            logger.warning(
                "FBA_API_KEY not set. API calls and WebSocket connections might fail if authentication is required."
            )

        # Thread-safe data storage
        self._lock = threading.RLock()
        self._current_snapshot: Optional[Dict[str, Any]] = None
        self._event_buffer: deque = deque(maxlen=event_buffer_size)
        self._last_update: Optional[datetime] = None

        # WebSocket connection management
        self._websocket_task: Optional[asyncio.Task] = None
        self._websocket_loop: Optional[asyncio.AbstractEventLoop] = None
        self._websocket_thread: Optional[threading.Thread] = None
        self._is_connected = False
        self._connection_callbacks: List[Callable] = []
        self._reconnect_attempts = 0  # Initialize reconnection attempt counter
        # Graceful shutdown and active websocket handle
        self._shutdown_flag: bool = False
        self._active_websocket: Optional[Any] = None

        # Start WebSocket connection in background
        self._start_websocket_thread()

        logger.info(f"JupyterConnector initialized for {api_base_url}")

    def _start_websocket_thread(self):
        """Start WebSocket connection in a background thread."""

        def run_websocket():
            self._websocket_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._websocket_loop)
            self._websocket_loop.run_until_complete(self._websocket_handler())

        self._websocket_thread = threading.Thread(target=run_websocket, daemon=True)
        self._websocket_thread.start()

    async def _websocket_handler(self):
        """Handle WebSocket connection with automatic reconnection."""
        while not self._shutdown_flag:
            try:
                logger.info(f"Connecting to WebSocket: {self.websocket_url}")

                # Prepare WebSocket headers with API key if provided
                ws_headers: Optional[Dict[str, str]] = None
                if self.api_key:
                    ws_headers = {"X-API-Key": self.api_key}

                async def _connect_with_headers():
                    # Prefer extra_headers, fall back to additional_headers (version drift)
                    try:
                        return await websockets.connect(
                            self.websocket_url,
                            **({"extra_headers": ws_headers} if ws_headers else {}),
                            ping_interval=None,
                        )
                    except TypeError:
                        return await websockets.connect(
                            self.websocket_url,
                            **({"additional_headers": ws_headers} if ws_headers else {}),
                            ping_interval=None,
                        )

                websocket = await _connect_with_headers()
                self._active_websocket = websocket
                self._is_connected = True
                logger.info("WebSocket connected successfully")

                # Notify connection callbacks
                for callback in self._connection_callbacks:
                    try:
                        callback(True)
                    except Exception as cb_e:
                        logger.exception(f"Connection callback error: {cb_e}")

                # Reset reconnection attempt counter on successful connection
                self._reconnect_attempts = 0

                # Listen for events
                async with websocket:
                    async for message in websocket:
                        try:
                            event_data = json.loads(message)
                            with self._lock:
                                self._event_buffer.append(
                                    {"timestamp": datetime.now(), "data": event_data}
                                )
                        except json.JSONDecodeError as e:
                            logger.warning(f"Failed to parse WebSocket message: {e}")
                        except Exception as e:
                            logger.error(f"Unexpected error processing WebSocket message: {e}")

            except asyncio.CancelledError:
                logger.info("WebSocket handler cancelled; shutting down")
                break
            except ConnectionClosed as e:
                self._is_connected = False
                if self._shutdown_flag:
                    logger.info("WebSocket connection closed due to shutdown request: %s", e)
                    break

                self._reconnect_attempts += 1
                logger.warning(
                    "WebSocket connection closed unexpectedly (code: %s, reason: %s). Reconnecting in %s seconds. Attempt %s...",
                    getattr(e, "code", None),
                    getattr(e, "reason", None),
                    self.websocket_reconnect_delay,
                    self._reconnect_attempts,
                )

                # Exponential backoff for reconnection attempts (with jitter)
                delay = min(
                    self.websocket_reconnect_delay * (2 ** (self._reconnect_attempts - 1)), 60
                ) + (0.5 * self._reconnect_attempts * (0.5 - time.monotonic() % 1))
                await asyncio.sleep(delay)

            except websockets.exceptions.InvalidURI as e:
                logger.critical(
                    f"Invalid WebSocket URI: {self.websocket_url}. Please correct the URI. Error: {e}"
                )
                raise  # This is a critical configuration error, stop attempts
            except (ConnectionRefusedError, OSError) as e:
                logger.error(
                    f"WebSocket connection failed: {e}. Is the server running and accessible?"
                )
                await asyncio.sleep(self.websocket_reconnect_delay)
            except websockets.exceptions.WebSocketException as e:
                logger.error(
                    f"WebSocket protocol error: {e}. Reconnecting in {self.websocket_reconnect_delay} seconds..."
                )
                await asyncio.sleep(self.websocket_reconnect_delay)
            except json.JSONDecodeError as e:
                logger.warning(f"WebSocket JSON decoding error: {e}. Message might be malformed.")
                await asyncio.sleep(1)
            except Exception as e:
                logger.exception(
                    f"Unexpected WebSocket error during connection/message processing: {e}. Reconnecting in {self.websocket_reconnect_delay} seconds..."
                )
                self._is_connected = False
                await asyncio.sleep(self.websocket_reconnect_delay)
            finally:
                self._active_websocket = None
                self._is_connected = False

    async def _close_active_websocket(self):
        """Close the active websocket connection if open."""
        ws = self._active_websocket
        if ws is not None:
            try:
                await ws.close(code=1000, reason="Client shutdown")
            except Exception as e:
                logger.debug(f"Error while closing websocket: {e}")

    async def refresh_snapshot(self) -> bool:
        """
        Fetch the latest simulation snapshot from the API.

        Returns:
            bool: True if successful, False otherwise
        """
        # Acquire a token from the rate limiter
        if not await self._rate_limiter.wait_for_token(timeout=self.api_timeout_seconds):
            logger.warning("Rate limit exceeded for snapshot refresh. Skipping request.")
            return False

        headers = {}
        if self.api_key:
            headers["X-API-Key"] = self.api_key

        try:
            # Use asyncio.to_thread for blocking requests.get call
            response = await asyncio.to_thread(
                requests.get,
                f"{self.api_base_url}/api/v1/simulation/snapshot",
                headers=headers,
                timeout=self.api_timeout_seconds,
            )
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)

            with self._lock:
                self._current_snapshot = response.json()
                self._last_update = datetime.now()

            logger.debug("Snapshot refreshed successfully")
            return True

        except requests.RequestException as e:
            logger.error(f"Failed to refresh snapshot: {e}")
            return False

    def refresh_snapshot_sync(self) -> bool:
        """
        Synchronous variant of refresh_snapshot for use in non-async contexts (e.g., classic notebook cells).
        Respects the internal rate limiter and blocks the calling thread until completion or timeout.

        Returns:
            bool: True if successful, False otherwise
        """
        # Acquire a token from the rate limiter (synchronous)
        if not self._rate_limiter.wait_for_token_sync(timeout=self.api_timeout_seconds):
            logger.warning("Rate limit exceeded for snapshot refresh. Skipping request.")
            return False

        headers = {}
        if self.api_key:
            headers["X-API-Key"] = self.api_key

        try:
            response = requests.get(
                f"{self.api_base_url}/api/v1/simulation/snapshot",
                headers=headers,
                timeout=self.api_timeout_seconds,
            )
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)

            with self._lock:
                self._current_snapshot = response.json()
                self._last_update = datetime.now()

            logger.debug("Snapshot refreshed successfully (sync)")
            return True

        except requests.RequestException as e:
            logger.error(f"Failed to refresh snapshot (sync): {e}")
            return False

    def get_snapshot_dict(self) -> Optional[Dict[str, Any]]:
        """
        Get the current simulation snapshot as a dictionary.

        Returns:
            Dict containing simulation state or None if not available
        """
        with self._lock:
            return self._current_snapshot.copy() if self._current_snapshot else None

    def get_snapshot_df(self) -> pd.DataFrame:
        """
        Get the current simulation snapshot as a Pandas DataFrame.

        Returns:
            DataFrame with key simulation metrics flattened for analysis
        """
        snapshot = self.get_snapshot_dict()
        if not snapshot:
            return pd.DataFrame()

        # Flatten key metrics into a single-row DataFrame
        flattened = {}

        # Basic metrics
        if "tick" in snapshot:
            flattened["tick"] = snapshot["tick"]
        if "timestamp" in snapshot:
            flattened["timestamp"] = snapshot["timestamp"]

        # Financial metrics
        if "metrics" in snapshot:
            metrics = snapshot["metrics"]
            for key, value in metrics.items():
                if isinstance(value, dict) and "amount" in value:
                    # Handle Money type
                    flattened[f"metrics_{key}"] = float(value["amount"])
                else:
                    flattened[f"metrics_{key}"] = value

        # Agent data
        if "agents" in snapshot:
            agents = snapshot["agents"]
            for agent_id, agent_data in agents.items():
                for key, value in agent_data.items():
                    if isinstance(value, dict) and "amount" in value:
                        # Handle Money type
                        flattened[f"agent_{agent_id}_{key}"] = float(value["amount"])
                    else:
                        flattened[f"agent_{agent_id}_{key}"] = value

        # Competitor data
        if "competitors" in snapshot:
            competitors = snapshot["competitors"]
            for comp_name, comp_data in competitors.items():
                for key, value in comp_data.items():
                    if isinstance(value, dict) and "amount" in value:
                        # Handle Money type
                        flattened[f"competitor_{comp_name}_{key}"] = float(value["amount"])
                    else:
                        flattened[f"competitor_{comp_name}_{key}"] = value

        return pd.DataFrame([flattened])

    def get_events_df(self, limit: Optional[int] = None) -> pd.DataFrame:
        """
        Get recent events as a Pandas DataFrame.

        Args:
            limit: Maximum number of events to return (default: all buffered)

        Returns:
            DataFrame with event data and timestamps
        """
        with self._lock:
            events = list(self._event_buffer)

        if limit:
            events = events[-limit:]

        if not events:
            return pd.DataFrame()

        # Convert events to DataFrame
        rows = []
        for event in events:
            row = {
                "timestamp": event["timestamp"],
                "event_type": event["data"].get("event_type", "Unknown"),
            }

            # Flatten event data
            event_data = event["data"].get("data", {})
            for key, value in event_data.items():
                if isinstance(value, dict) and "amount" in value:
                    # Handle Money type
                    row[key] = float(value["amount"])
                else:
                    row[key] = value

            rows.append(row)

        return pd.DataFrame(rows)

    def get_event_stream(self, event_types: Optional[List[str]] = None) -> List[Dict]:
        """
        Get recent events from the live stream.

        Args:
            event_types: Filter events by type (default: all events)

        Returns:
            List of event dictionaries
        """
        with self._lock:
            events = list(self._event_buffer)

        if event_types:
            events = [e for e in events if e["data"].get("event_type") in event_types]

        return events

    def get_financial_history_df(self) -> pd.DataFrame:
        """
        Extract financial transaction history from events.

        Returns:
            DataFrame with sales and price change history
        """
        events = self.get_event_stream(["SaleOccurred", "ProductPriceUpdated"])

        if not events:
            return pd.DataFrame()

        rows = []
        for event in events:
            event_data = event["data"]
            row = {
                "timestamp": event["timestamp"],
                "event_type": event_data.get("event_type"),
            }

            # Extract event-specific data
            data = event_data.get("data", {})
            for key, value in data.items():
                if isinstance(value, dict) and "amount" in value:
                    row[key] = float(value["amount"])
                else:
                    row[key] = value

            rows.append(row)

        return pd.DataFrame(rows)

    def is_connected(self) -> bool:
        """Check if WebSocket connection is active."""
        return self._is_connected

    def get_connection_status(self) -> Dict[str, Any]:
        """
        Get detailed connection status information.

        Returns:
            Dictionary with connection details
        """
        with self._lock:
            return {
                "websocket_connected": self._is_connected,
                "last_snapshot_update": self._last_update,
                "events_buffered": len(self._event_buffer),
                "has_snapshot_data": self._current_snapshot is not None,
                "api_base_url": self.api_base_url,
                "websocket_url": self.websocket_url,
            }

    def add_connection_callback(self, callback: Callable[[bool], None]):
        """
        Add callback to be called when connection status changes.

        Args:
            callback: Function that takes connection status (bool) as parameter
        """
        self._connection_callbacks.append(callback)

    def wait_for_connection(self, timeout: float = 30.0) -> bool:
        """
        Wait for WebSocket connection to be established.

        Args:
            timeout: Maximum time to wait in seconds

        Returns:
            True if connected within timeout, False otherwise
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.is_connected():
                return True
            time.sleep(0.1)
        return False

    def close(self):
        """Clean up resources and close connections."""
        self._shutdown_flag = True

        loop = self._websocket_loop
        if loop and loop.is_running():
            try:
                # Cancel the websocket task to ensure clean shutdown
                if self._websocket_task:
                    self._websocket_task.cancel()

                # Close the active websocket connection
                fut = asyncio.run_coroutine_threadsafe(self._close_active_websocket(), loop)
                # Wait briefly for the socket to close to break recv loop
                fut.result(timeout=2)

                # Shutdown all async generators to ensure clean exit
                asyncio.run_coroutine_threadsafe(loop.shutdown_asyncgens(), loop)
            except Exception as e:
                logger.debug(f"WebSocket close during shutdown encountered: {e}")

        if self._websocket_thread and self._websocket_thread.is_alive():
            self._websocket_thread.join(timeout=3)

        logger.info("JupyterConnector closed")


# Convenience function for quick notebook setup (synchronous for tests)
def connect_to_simulation(
    api_url: str = os.getenv("FBA_API_BASE_URL", "http://localhost:8000"),
    api_key: Optional[str] = os.getenv("FBA_API_KEY"),
    announce: bool = True,
) -> bool:
    """
    Quick connection setup for Jupyter notebooks (synchronous).
    Returns True if the connector thread started and connection established within timeout.
    """
    connector = JupyterConnector(api_base_url=api_url, api_key=api_key)

    # Wait for connection and refresh snapshot (best-effort)
    ok = connector.wait_for_connection(timeout=10)
    if ok:
        try:
            connector.refresh_snapshot_sync()
        except Exception:
            pass
        status = connector.get_connection_status()
        msg_ok = f"Connected to FBA-Bench simulation at {api_url}"
        msg_events = f"Events buffered: {status['events_buffered']}"
        msg_snap = f"Snapshot available: {status['has_snapshot_data']}"
        logger.info(msg_ok)
        logger.info(msg_events)
        logger.info(msg_snap)
        if announce:
            print(f"[OK] {msg_ok}")
            print(f"[Stats] {msg_events}")
            print(f"[Snapshot] {msg_snap}")
    else:
        msg_timeout = f"Connection timeout or authentication failed - check that API server is running at {api_url} and API key is correct."
        logger.warning(msg_timeout)
        if announce:
            print(f"[Warn] {msg_timeout}")

    return ok
