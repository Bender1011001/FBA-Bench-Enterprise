"""
Centralized dependency wiring for FastAPI.
Provides singletons of ConnectionManager, ExperimentManager, and SimulationManager.
"""

from fba_bench_api.api.connection import ConnectionManager
from fba_bench_api.api.experiment import ExperimentManager
from fba_bench_api.api.simulation import SimulationManager

# Shared singletons
connection_manager = ConnectionManager()
experiment_manager = ExperimentManager()
simulation_manager = SimulationManager()

__all__ = [
    "ConnectionManager",
    "ExperimentManager",
    "SimulationManager",
    "connection_manager",
    "experiment_manager",
    "simulation_manager",
]

from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os

security = HTTPBearer(auto_error=False)

def get_current_user(token: str = Depends(security)) -> Optional[Dict[str, Any]]:
    """
    Get current user dependency. In test mode (AUTH_ENABLED=false), returns anonymous user.
    """
    if os.getenv("AUTH_ENABLED", "false").lower() != "true":
        return {"sub": "anonymous", "roles": []}
    # TODO: Implement full JWT verification for production
    raise HTTPException(status_code=401, detail="Authentication required")


# Phase 0 Spike: TenantContext Dependency (Mock for Demonstration)
# In production, integrate with Auth0 JWT validation to extract real tenant claims.
from pydantic import BaseModel

class TenantContext(BaseModel):
    tenant_id: str
    user_id: str
    roles: list[str]

async def get_tenant_context(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> TenantContext:
    """
    Spike implementation: Extract tenant context from Authorization header.
    Demo format: 'Bearer tenant:{id}|user:{id}|roles:admin,viewer'
    In full IAM (Auth0), decode JWT claims for tenant_id, user_id, roles.
    """
    token = credentials.credentials
    try:
        # Mock parsing (replace with jwt.decode(credentials.credentials, key, algorithms=["RS256"]) in prod)
        parts = token.split('|')
        if len(parts) < 3:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token format for tenant context"
            )
        tenant_id = parts[0].replace('tenant:', '')
        user_id = parts[1].replace('user:', '')
        roles_str = parts[2].replace('roles:', '')
        roles = [r.strip() for r in roles_str.split(',') if r.strip()]
        
        return TenantContext(
            tenant_id=tenant_id,
            user_id=user_id,
            roles=roles
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate tenant context: {str(e)}"
        )

# Usage example in routers:
# def some_endpoint(ctx: TenantContext = Depends(get_tenant_context)):
#     if 'admin' not in ctx.roles:
#         raise HTTPException(status_code=403, detail="Admin role required")
#     # Proceed with tenant-scoped operations


# Phase 0 Spike: TenantContext Dependency (Mock for Demonstration)
# In production, integrate with Auth0 JWT validation to extract real tenant claims.
from typing import Optional
from pydantic import BaseModel
from fastapi import HTTPException, status

class TenantContext(BaseModel):
    tenant_id: str
    user_id: str
    roles: list[str]

async def get_tenant_context(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> TenantContext:
    """
    Spike implementation: Extract tenant context from Authorization header.
    Demo format: 'Bearer tenant:{id}|user:{id}|roles:admin,viewer'
    In full IAM (Auth0), decode JWT claims for tenant_id, user_id, roles.
    """
    token = credentials.credentials
    try:
        # Mock parsing (replace with jwt.decode(credentials.credentials, key, algorithms=["RS256"]) in prod)
        parts = token.split('|')
        if len(parts) < 3:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token format for tenant context"
            )
        tenant_id = parts[0].replace('tenant:', '')
        user_id = parts[1].replace('user:', '')
        roles_str = parts[2].replace('roles:', '')
        roles = [r.strip() for r in roles_str.split(',') if r.strip()]
        
        return TenantContext(
            tenant_id=tenant_id,
            user_id=user_id,
            roles=roles
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate tenant context: {str(e)}"
        )

# Usage example in routers:
# def some_endpoint(ctx: TenantContext = Depends(get_tenant_context)):
#     if 'admin' not in ctx.roles:
#         raise HTTPException(status_code=403, detail="Admin role required")
#     # Proceed with tenant-scoped operations
