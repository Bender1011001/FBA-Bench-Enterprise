import asyncio
import json
import logging
import os
import uuid
from datetime import datetime
from functools import lru_cache
from threading import RLock
from typing import Any, Dict, List, Optional, Set

from fastapi import HTTPException, WebSocket
from starlette.websockets import WebSocketDisconnect
import jwt
from jwt import ExpiredSignatureError, InvalidTokenError, PyJWTError

# from simulation_orchestrator import SimulationOrchestrator  # Used for future integration

logger = logging.getLogger(__name__)


@lru_cache
def get_max_ws_connections_default() -> int:
    """
    Reads the default maximum WebSocket connections from environment variables.
    Defaults to 200 if not set or invalid.
    """
    try:
        return int(os.getenv("FBA_MAX_WS_CONNECTIONS_DEFAULT", "200"))
    except ValueError:
        logger.warning("Invalid value for FBA_MAX_WS_CONNECTIONS_DEFAULT, using default 200.")
        return 200


@lru_cache
def get_max_ws_connections_global() -> int:
    """
    Reads the maximum WebSocket connections for the global instance from environment variables.
    Defaults to 100 if not set or invalid.
    """
    try:
        return int(os.getenv("FBA_MAX_WS_CONNECTIONS", "100"))
    except ValueError:
        logger.warning("Invalid value for FBA_MAX_WS_CONNECTIONS, using default 100.")
        return 100


class ConnectionManager:
    """Manages WebSocket connections for real-time event streaming."""

    def __init__(self, max_connections: int = get_max_ws_connections_default()):
        self.active_connections: List[WebSocket] = []
        self.connection_subscriptions: Dict[
            WebSocket, Set[str]
        ] = {}  # Track what each connection subscribes to
        self.connection_metadata: Dict[
            WebSocket, Dict[str, Any]
        ] = {}  # Additional metadata for each connection
        self.max_connections = max_connections
        self._heartbeat_task = None
        self._lock = RLock()  # Protects access to connection collections

    async def start(self):
        """Starts any background tasks for the ConnectionManager, e.g., heartbeats."""
        logger.info("ConnectionManager: Starting background tasks.")
        # Example: Start a periodic heartbeat task
        self._heartbeat_task = asyncio.create_task(self._periodic_heartbeat())

    async def stop(self):
        """Stops all background tasks and gracefully closes connections."""
        logger.info("ConnectionManager: Stopping background tasks and closing connections.")
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                logger.info("ConnectionManager: Heartbeat task cancelled.")
        # Snapshot connections under lock
        with self._lock:
            connections = list(self.active_connections)
        for connection in connections:
            try:
                await connection.close(code=1000, reason="Server shutting down")
            except Exception as e:
                logger.error(f"Error closing WebSocket during shutdown: {e}")
        with self._lock:
            self.active_connections.clear()
            self.connection_subscriptions.clear()
            self.connection_metadata.clear()
        logger.info("ConnectionManager: All connections closed.")

    async def _periodic_heartbeat(self):
        """Sends periodic heartbeats to all connected websockets."""
        while True:
            await asyncio.sleep(30)  # Send heartbeat every 30 seconds
            # Snapshot connections under lock for safe iteration
            with self._lock:
                connections = list(self.active_connections)
                metadata_snapshot = {
                    c: dict(self.connection_metadata.get(c, {})) for c in connections
                }

            disconnected = []
            for connection in connections:
                client_id = metadata_snapshot.get(connection, {}).get("client_id", "unknown")
                try:
                    await connection.ping()  # Send binary ping frame
                    # Update last_activity on successful ping
                    with self._lock:
                        if connection in self.connection_metadata:
                            self.connection_metadata[connection][
                                "last_activity"
                            ] = datetime.now().isoformat()
                except WebSocketDisconnect:
                    logger.info(
                        f"WebSocket {client_id} disconnected during heartbeat, cleaning up."
                    )
                    disconnected.append(connection)
                except Exception as e:
                    logger.warning(f"Error sending heartbeat to client {client_id}: {e}")
                    disconnected.append(connection)

            # Clean up disconnected clients
            for connection in disconnected:
                self.disconnect(connection)

    async def connect(self, websocket: WebSocket, origin: Optional[str] = None):
        """Accept new WebSocket connection with capacity enforcement and thread-safety."""
        # Fast pre-check to avoid unnecessary accept when clearly at capacity
        with self._lock:
            at_capacity = len(self.active_connections) >= self.max_connections
        if at_capacity:
            logger.warning(f"Connection rejected for Origin: {origin} - max connections reached.")
            await websocket.close(code=1008, reason="Maximum connections reached")
            return None
        # Accept, then enforce capacity again under lock to avoid race
        await websocket.accept()
        with self._lock:
            if len(self.active_connections) >= self.max_connections:
                # Another connection acquired the last slot—reject this one
                logger.warning(
                    f"Connection rejected post-accept for Origin: {origin} - max connections reached."
                )
                # Best-effort close; ignore errors
                try:
                    await websocket.close(code=1008, reason="Maximum connections reached")
                except Exception:
                    pass
                return None
            client_id = str(uuid.uuid4())
            self.active_connections.append(websocket)
            self.connection_subscriptions[websocket] = set()
            self.connection_metadata[websocket] = {
                "connected_at": datetime.now().isoformat(),
                "last_activity": datetime.now().isoformat(),
                "client_id": client_id,
                "origin": origin,
            }
            active_count = len(self.active_connections)
        logger.info(
            f"📡 WebSocket connected (Client ID: {client_id}, Origin: {origin}). Active connections: {active_count}"
        )
        return client_id

    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection."""
        with self._lock:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
            if websocket in self.connection_subscriptions:
                del self.connection_subscriptions[websocket]
            if websocket in self.connection_metadata:
                del self.connection_metadata[websocket]
            active_count = len(self.active_connections)
        logger.info(f"📡 WebSocket disconnected. Active connections: {active_count}")

    async def send_to_connection(self, websocket: WebSocket, event_data: Dict[str, Any]) -> bool:
        """Send event to a specific WebSocket connection. Returns True on success."""
        try:
            # Snapshot and membership check under lock
            with self._lock:
                is_active = websocket in self.active_connections
                client_id = self.connection_metadata.get(websocket, {}).get("client_id", "unknown")
            if not is_active:
                logger.warning("Attempted to send to a closed or inactive WebSocket connection")
                return False
            message = json.dumps(event_data)
            await websocket.send_text(message)
            with self._lock:
                if websocket in self.connection_metadata:
                    self.connection_metadata[websocket][
                        "last_activity"
                    ] = datetime.now().isoformat()
            return True
        except WebSocketDisconnect:
            logger.info(
                f"WebSocket {client_id} disconnected during send_to_connection, cleaning up."
            )
            self.disconnect(websocket)
            return False
        except (TypeError, ValueError) as e:
            event_type_summary = (
                event_data.get("type", "unknown") if isinstance(event_data, dict) else "unknown"
            )
            logger.warning(
                f"Serialization error sending event type '{event_type_summary}' to client {client_id}: {e}"
            )
            return False
        except Exception as e:
            logger.error(
                f"Unexpected error sending data to WebSocket client {client_id}: {e}", exc_info=True
            )
            self.disconnect(websocket)
            return False

    async def broadcast_event(
        self, event_data: Dict[str, Any], event_type: Optional[str] = None
    ) -> None:
        """Broadcast event to all connected WebSocket clients with optional subscription filter."""
        # Fast exit if no connections
        with self._lock:
            if not self.active_connections:
                return
            connections = list(self.active_connections)
            # Snapshot subscriptions for consistent view
            subscriptions = {
                c: set(self.connection_subscriptions.get(c, set())) for c in connections
            }
            metadata_snapshot = {c: dict(self.connection_metadata.get(c, {})) for c in connections}
        # Attempt to serialize once outside the loop for efficiency and to catch global serialization errors
        try:
            message = json.dumps(event_data)
        except (TypeError, ValueError, json.JSONDecodeError) as e:
            event_type_summary = (
                event_type
                if event_type
                else (
                    event_data.get("type", "unknown") if isinstance(event_data, dict) else "unknown"
                )
            )
            logger.error(
                f"Failed to serialize event type '{event_type_summary}' for broadcast: {e}",
                exc_info=True,
            )
            return
        disconnected: List[WebSocket] = []
        for connection in connections:
            client_id = metadata_snapshot.get(connection, {}).get("client_id", "unknown")
            try:
                if event_type:
                    if event_type in subscriptions.get(connection, set()):
                        await connection.send_text(message)
                        with self._lock:
                            if connection in self.connection_metadata:
                                self.connection_metadata[connection][
                                    "last_activity"
                                ] = datetime.now().isoformat()
                else:
                    await connection.send_text(message)
                    with self._lock:
                        if connection in self.connection_metadata:
                            self.connection_metadata[connection][
                                "last_activity"
                            ] = datetime.now().isoformat()
            except WebSocketDisconnect:
                logger.info(
                    f"WebSocket {client_id} disconnected during broadcast_event, cleaning up."
                )
                disconnected.append(connection)
            except (TypeError, ValueError) as e:
                event_type_summary = (
                    event_type
                    if event_type
                    else (
                        event_data.get("type", "unknown")
                        if isinstance(event_data, dict)
                        else "unknown"
                    )
                )
                logger.warning(
                    f"Serialization error sending event type '{event_type_summary}' to client {client_id} during broadcast: {e}"
                )
            except Exception as e:
                logger.error(
                    f"Unexpected error broadcasting event to client {client_id}: {e}", exc_info=True
                )
                disconnected.append(connection)
        # Clean up disconnected/errored clients
        for connection in disconnected:
            self.disconnect(connection)

    def add_subscription(self, websocket: WebSocket, event_type: str):
        """Add a subscription for a specific event type to a WebSocket connection."""
        with self._lock:
            if websocket in self.connection_subscriptions:
                self.connection_subscriptions[websocket].add(event_type)

    def remove_subscription(self, websocket: WebSocket, event_type: str):
        """Remove a subscription for a specific event type from a WebSocket connection."""
        with self._lock:
            if websocket in self.connection_subscriptions:
                self.connection_subscriptions[websocket].discard(event_type)

    def get_connection_stats(self) -> Dict[str, Any]:
        """Get statistics about current WebSocket connections (thread-safe snapshot)."""
        with self._lock:
            total = len(self.active_connections)
            subs_map = {conn: set(subs) for conn, subs in self.connection_subscriptions.items()}
            meta_map = {conn: dict(md) for conn, md in self.connection_metadata.items()}
        sub_types = sorted({t for subs in subs_map.values() for t in subs})
        return {
            "total_connections": total,
            "subscriptions": {
                event_type: sum(1 for subs in subs_map.values() if event_type in subs)
                for event_type in sub_types
            },
            "connections": [
                {
                    "client_id": metadata.get("client_id"),
                    "connected_at": metadata.get("connected_at"),
                    "last_activity": metadata.get("last_activity"),
                    "subscriptions": list(subs_map.get(conn, set())),
                }
                for conn, metadata in meta_map.items()
            ],
        }


class SimulationManager:
    """Manages the lifecycle and state of simulation orchestrator instances."""

    def __init__(self):
        self.orchestrators: Dict[str, Any] = {}
        self.orchestrator_lock = asyncio.Lock()  # For thread safety

    async def get_orchestrator(self, sim_id: str) -> Any:
        async with self.orchestrator_lock:
            orchestrator = self.orchestrators.get(sim_id)
            if not orchestrator:
                raise HTTPException(
                    status_code=404, detail=f"Simulation with ID '{sim_id}' not found."
                )
            return orchestrator

    async def add_orchestrator(self, sim_id: str, orchestrator: Any):
        async with self.orchestrator_lock:
            if sim_id in self.orchestrators:
                logger.warning(f"Simulation with ID '{sim_id}' already exists. Overwriting.")
            self.orchestrators[sim_id] = orchestrator
            logger.info(f"Added simulation orchestrator with ID: {sim_id}")

    async def remove_orchestrator(self, sim_id: str):
        async with self.orchestrator_lock:
            if sim_id in self.orchestrators:
                del self.orchestrators[sim_id]
                logger.info(f"Removed simulation orchestrator with ID: {sim_id}")

    def get_simulation_status(self, sim_id: str) -> Optional[Dict[str, Any]]:
        orchestrator = self.orchestrators.get(sim_id)
        if orchestrator:
            return getattr(orchestrator, "get_status", lambda: {"status": "unknown"})()
        return None

    def get_all_simulation_ids(self) -> List[str]:
        return list(self.orchestrators.keys())


# Global managers (encapsulated; no raw mutable module-level dicts)
connection_manager = ConnectionManager(max_connections=get_max_ws_connections_global())
simulation_manager = SimulationManager()


class ExperimentManager:
    """Manages experiment manager instances and state."""

    def __init__(self):
        self._experiments: Dict[str, Any] = {}
        self._lock = asyncio.Lock()

    async def get(self, experiment_id: str) -> Any:
        async with self._lock:
            exp = self._experiments.get(experiment_id)
            if exp is None:
                raise HTTPException(
                    status_code=404, detail=f"Experiment '{experiment_id}' not found."
                )
            return exp

    async def set(self, experiment_id: str, manager: Any) -> None:
        async with self._lock:
            self._experiments[experiment_id] = manager

    async def remove(self, experiment_id: str) -> None:
        async with self._lock:
            self._experiments.pop(experiment_id, None)

    def list_ids(self) -> List[str]:
        return list(self._experiments.keys())


experiment_manager = ExperimentManager()


# Authentication dependency functions
async def get_current_user(authorization: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Optional authentication dependency that returns user info if available.

    In development mode with AUTH_ENABLED=false, this always returns None
    to allow unauthenticated access. In production with AUTH_ENABLED=true,
    this would validate JWT tokens and return user info.

    Args:
        authorization: Optional Authorization header value

    Returns:
        User info dict if authenticated, None if not authenticated or auth disabled
    """
    # Check if auth is enabled via environment variable
    auth_enabled = os.getenv("AUTH_ENABLED", "false").lower() == "true"

    if not auth_enabled:
        # Auth disabled - allow all requests through
        return None

    # Auth enabled but no authorization header provided
    if not authorization:
        return None

    try:
        # Extract token from Bearer prefix
        if not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid authorization header")
        token = authorization.split(" ")[1]

        # Get secret key from env, fallback for dev
        secret_key = os.getenv("JWT_SECRET_KEY", "dev-secret-key-change-in-production")
        if not secret_key or secret_key == "dev-secret-key-change-in-production":
            logger.warning("Using default JWT secret key; set JWT_SECRET_KEY in production")

        # Decode and verify token
        payload = jwt.decode(
            token,
            secret_key,
            algorithms=["HS256"],
            options={"verify_exp": True, "verify_signature": True},
        )
        return {"user_id": payload.get("sub"), "username": payload.get("username", "unknown")}
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected JWT error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
