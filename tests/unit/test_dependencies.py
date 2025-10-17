import os
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import jwt
import pytest
from api.dependencies import (
    ConnectionManager,
    SimulationManager,
    get_current_user,
    get_max_ws_connections_global,
)
from fastapi import HTTPException
from starlette.websockets import WebSocketDisconnect, WebSocketState

from simulation_orchestrator import SimulationOrchestrator  # Ensure import works


@pytest.mark.unit
class TestGetCurrentUser:
    @pytest.mark.asyncio
    async def test_auth_disabled_returns_none(self):
        os.environ["AUTH_ENABLED"] = "false"
        result = await get_current_user(None)
        assert result is None

    @pytest.mark.asyncio
    async def test_auth_enabled_no_header_returns_none(self):
        os.environ["AUTH_ENABLED"] = "true"
        result = await get_current_user(None)
        assert result is None

    @pytest.mark.asyncio
    async def test_auth_enabled_invalid_header_raises_401(self):
        os.environ["AUTH_ENABLED"] = "true"
        os.environ["JWT_SECRET_KEY"] = "test-secret"
        with pytest.raises(HTTPException) as exc:
            await get_current_user("Invalid")
        assert exc.value.status_code == 401
        assert "Invalid authorization header" in str(exc.value.detail)

    @pytest.mark.asyncio
    async def test_auth_enabled_invalid_token_raises_401(self):
        os.environ["AUTH_ENABLED"] = "true"
        os.environ["JWT_SECRET_KEY"] = "test-secret"
        invalid_token = "invalid.token.here"
        with pytest.raises(HTTPException) as exc:
            await get_current_user(f"Bearer {invalid_token}")
        assert exc.value.status_code == 401
        assert "Invalid token" in str(exc.value.detail)

    @pytest.mark.asyncio
    async def test_auth_enabled_expired_token_raises_401(self):
        os.environ["AUTH_ENABLED"] = "true"
        os.environ["JWT_SECRET_KEY"] = "test-secret"
        payload = {"sub": "user123", "exp": datetime.utcnow() - timedelta(seconds=1)}
        expired_token = jwt.encode(payload, "test-secret", algorithm="HS256")
        with pytest.raises(HTTPException) as exc:
            await get_current_user(f"Bearer {expired_token}")
        assert exc.value.status_code == 401
        assert "Token has expired" in str(exc.value.detail)

    @pytest.mark.asyncio
    async def test_auth_enabled_valid_token_returns_user_info(self):
        os.environ["AUTH_ENABLED"] = "true"
        os.environ["JWT_SECRET_KEY"] = "test-secret"
        payload = {
            "sub": "user123",
            "username": "testuser",
            "exp": datetime.utcnow() + timedelta(hours=1),
        }
        valid_token = jwt.encode(payload, "test-secret", algorithm="HS256")
        result = await get_current_user(f"Bearer {valid_token}")
        assert result == {"user_id": "user123", "username": "testuser"}

    @pytest.mark.asyncio
    async def test_auth_enabled_unexpected_error_raises_500(self):
        os.environ["AUTH_ENABLED"] = "true"
        with patch("api.dependencies.jwt.decode", side_effect=Exception("Unexpected")):
            with pytest.raises(HTTPException) as exc:
                await get_current_user("Bearer valid.token")
        assert exc.value.status_code == 500


@pytest.mark.unit
class TestConnectionManager:
    def setup_method(self):
        self.max_connections = 5
        self.manager = ConnectionManager(max_connections=self.max_connections)

    @pytest.mark.asyncio
    async def test_connect_success(self):
        websocket = AsyncMock()
        await websocket.accept()
        client_id = await self.manager.connect(websocket)
        assert client_id is not None
        assert len(self.manager.active_connections) == 1

    @pytest.mark.asyncio
    async def test_connect_at_capacity_rejects(self):
        # Fill capacity
        for _ in range(self.max_connections):
            ws = AsyncMock()
            await ws.accept()
            await self.manager.connect(ws)
        # New connection should be rejected
        websocket = AsyncMock()
        client_id = await self.manager.connect(websocket)
        assert client_id is None
        assert len(self.manager.active_connections) == self.max_connections

    def test_disconnect_removes_connection(self):
        websocket = MagicMock()
        self.manager.active_connections.append(websocket)
        self.manager.disconnect(websocket)
        assert websocket not in self.manager.active_connections

    @pytest.mark.asyncio
    async def test_periodic_heartbeat_sends_ping_and_updates_activity(self):
        websocket = AsyncMock()
        websocket.state = WebSocketState.CONNECTED
        self.manager.active_connections.append(websocket)
        self.manager.connection_metadata[websocket] = {
            "client_id": "test",
            "last_activity": "2023-01-01T00:00:00",
        }

        # Run one iteration
        await self.manager._periodic_heartbeat()
        websocket.ping.assert_called_once()
        # Check last_activity updated
        assert "last_activity" in self.manager.connection_metadata[websocket]
        assert datetime.fromisoformat(
            self.manager.connection_metadata[websocket]["last_activity"]
        ) > datetime.now() - timedelta(seconds=1)

    @pytest.mark.asyncio
    async def test_periodic_heartbeat_handles_disconnect(self):
        websocket = AsyncMock()
        websocket.ping.side_effect = WebSocketDisconnect()
        self.manager.active_connections.append(websocket)
        await self.manager._periodic_heartbeat()
        assert websocket not in self.manager.active_connections

    @pytest.mark.asyncio
    async def test_start_and_stop_heartbeat(self):
        await self.manager.start()
        assert self.manager._heartbeat_task is not None
        await self.manager.stop()
        assert self.manager._heartbeat_task is None
        assert len(self.manager.active_connections) == 0


@pytest.mark.unit
def test_get_max_ws_connections_global():
    os.environ["FBA_MAX_WS_CONNECTIONS"] = "10"
    assert get_max_ws_connections_global() == 10
    del os.environ["FBA_MAX_WS_CONNECTIONS"]
    assert get_max_ws_connections_global() == 100  # Default


@pytest.mark.unit
def test_simulation_manager_integration():
    # Basic test to ensure SimulationManager works post-fix
    manager = SimulationManager()
    orch = MagicMock(spec=SimulationOrchestrator)
    orch.get_status.return_value = {"status": "running"}
    # Add and get
    import asyncio

    loop = asyncio.get_event_loop()
    loop.run_until_complete(manager.add_orchestrator("test_sim", orch))
    retrieved = loop.run_until_complete(manager.get_orchestrator("test_sim"))
    assert retrieved == orch
    status = manager.get_simulation_status("test_sim")
    assert status == {"status": "running"}
    manager.get_all_simulation_ids() == ["test_sim"]
