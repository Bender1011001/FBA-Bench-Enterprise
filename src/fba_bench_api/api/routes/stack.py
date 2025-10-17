from __future__ import annotations

import logging
from typing import Optional, Union

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from fba_bench_api.core import stack_manager as sm

logger = logging.getLogger("fba_bench_api.stack.routes")

# Full, normalized prefix for Phase 1 parity
router = APIRouter(prefix="/api/v1/stack/clearml", tags=["Stack", "ClearML"])


# ---------------------------
# Pydantic models (contracts)
# ---------------------------
class StartRequest(BaseModel):
    composePath: Optional[str] = Field(
        default=None, description="Optional path to docker-compose.clearml.yml"
    )
    detach: bool = Field(
        default=True,
        description="Ignored by server; always enforced as detached for safety",
    )


class StartResponse(BaseModel):
    started: bool
    compose_file: str
    message: str


class PortStatus(BaseModel):
    port: int
    open: bool


class Ports(BaseModel):
    web: PortStatus
    api: PortStatus
    file: PortStatus


class StatusResponse(BaseModel):
    running: bool
    web_url: str
    api_url: str
    file_url: str
    ports: Ports
    compose_file: str


class StopRequest(BaseModel):
    composePath: Optional[str] = Field(
        default=None, description="Optional path to docker-compose.clearml.yml"
    )


class StopResponse(BaseModel):
    stopped: bool
    message: str


def _forbidden_json(message: str) -> JSONResponse:
    return JSONResponse(status_code=403, content={"error": message})


def _is_allowed() -> bool:
    allowed = sm.stack_control_allowed()
    if not allowed:
        logger.warning("Stack control requested but ALLOW_STACK_CONTROL is not enabled")
    return allowed


# ---------------------------
# Endpoints
# ---------------------------
@router.post("/start", response_model=StartResponse)
async def start_stack(req: StartRequest) -> Union[StartResponse, JSONResponse]:
    """
    Start the ClearML Docker Compose stack, reusing CLI logic for parity.

    Security:
    - Requires ALLOW_STACK_CONTROL=true (403 otherwise).
    """
    if not _is_allowed():
        return _forbidden_json(
            "Stack control disabled; set ALLOW_STACK_CONTROL=true to enable."
        )

    started, compose_file, message, variant = sm.start_stack(
        req.composePath, detach=True
    )
    logger.info(
        "stack.start: compose=%s variant=%s started=%s",
        str(compose_file) if compose_file else "None",
        variant,
        started,
    )
    return StartResponse(
        started=bool(started),
        compose_file=str(compose_file) if compose_file else "",
        message=message,
    )


@router.get("/status", response_model=StatusResponse)
async def stack_status(
    composePath: Optional[str] = Query(
        default=None, description="Optional path to docker-compose.clearml.yml"
    ),
) -> Union[StatusResponse, JSONResponse]:
    """
    Non-blocking status report of ClearML services and ports.

    Security:
    - Requires ALLOW_STACK_CONTROL=true (403 otherwise).
    """
    if not _is_allowed():
        return _forbidden_json(
            "Stack control disabled; set ALLOW_STACK_CONTROL=true to enable."
        )

    payload = sm.status(composePath)
    logger.info(
        "stack.status: running=%s compose=%s web=%s api=%s file=%s",
        payload.get("running"),
        payload.get("compose_file"),
        payload.get("web_url"),
        payload.get("api_url"),
        payload.get("file_url"),
    )
    # Pydantic model conversion
    ports = payload["ports"]
    return StatusResponse(
        running=bool(payload["running"]),
        web_url=str(payload["web_url"]),
        api_url=str(payload["api_url"]),
        file_url=str(payload["file_url"]),
        ports=Ports(
            web=PortStatus(**ports["web"]),
            api=PortStatus(**ports["api"]),
            file=PortStatus(**ports["file"]),
        ),
        compose_file=str(payload["compose_file"]),
    )


@router.post("/stop", response_model=StopResponse)
async def stop_stack(req: StopRequest) -> Union[StopResponse, JSONResponse]:
    """
    Stop the ClearML Docker Compose stack, reusing CLI logic for parity.

    Security:
    - Requires ALLOW_STACK_CONTROL=true (403 otherwise).
    """
    if not _is_allowed():
        return _forbidden_json(
            "Stack control disabled; set ALLOW_STACK_CONTROL=true to enable."
        )

    stopped, compose_file, message, variant = sm.stop_stack(req.composePath)
    logger.info(
        "stack.stop: compose=%s variant=%s stopped=%s",
        str(compose_file) if compose_file else "None",
        variant,
        stopped,
    )
    return StopResponse(stopped=bool(stopped), message=message)
