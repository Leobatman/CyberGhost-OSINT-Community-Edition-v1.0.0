"""
CyberGhost OSINT Enterprise — FastAPI Dependencies
Auth, RBAC, Rate Limiting, IP Extraction
"""
from __future__ import annotations

import time
from collections.abc import Callable
from functools import wraps
from typing import Annotated, Any

import structlog
from fastapi import Depends, HTTPException, Request, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db
from backend.core.security import (
    Permission,
    Role,
    TokenType,
    audit_log,
    decode_token,
    has_permission,
    verify_api_key,
)
from backend.models.models import APIKey, AuditLog, User

log = structlog.get_logger(__name__)

bearer_scheme = HTTPBearer(auto_error=False)

# ── Current User ──────────────────────────────────────────────────────────────


async def get_current_user(
    request: Request,
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Security(bearer_scheme)
    ] = None,
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Authenticate request via JWT Bearer token or API key.
    Raises 401 if unauthenticated.
    """
    ip = get_client_ip(request)
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        # Try API key from header
        api_key_header = request.headers.get("X-API-Key")
        if api_key_header:
            return await _authenticate_api_key(api_key_header, db, ip)
        audit_log("auth_missing_credentials", None, ip, success=False)
        raise credentials_exception

    token = credentials.credentials

    # Try API key format
    if token.startswith("cg_"):
        return await _authenticate_api_key(token, db, ip)

    # JWT authentication
    try:
        payload = decode_token(token)
    except JWTError:
        audit_log("auth_invalid_token", None, ip, success=False)
        raise credentials_exception

    if payload.get("type") != TokenType.ACCESS:
        audit_log("auth_wrong_token_type", None, ip, success=False)
        raise credentials_exception

    user_id: str | None = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        audit_log(
            "auth_user_not_found_or_inactive", user_id, ip, success=False
        )
        raise credentials_exception

    # Check account lock
    if user.locked_until and user.locked_until > _utcnow():
        audit_log("auth_account_locked", str(user.id), ip, success=False)
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=f"Account locked until {user.locked_until.isoformat()}",
        )

    return user


async def _authenticate_api_key(
    raw_key: str, db: AsyncSession, ip: str
) -> User:
    """Authenticate via API key."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid API key",
    )

    # Find key by prefix (first 8 chars)
    prefix = raw_key[:8]
    result = await db.execute(
        select(APIKey)
        .where(APIKey.key_prefix == prefix)
        .where(APIKey.is_active == True)  # noqa: E712
    )
    api_keys = result.scalars().all()

    for api_key in api_keys:
        if verify_api_key(raw_key, api_key.key_hash):
            # Update usage stats
            api_key.last_used = _utcnow()
            api_key.usage_count += 1
            await db.commit()

            result = await db.execute(
                select(User).where(User.id == api_key.user_id)
            )
            user = result.scalar_one_or_none()
            if user and user.is_active:
                return user

    audit_log("auth_invalid_api_key", None, ip, success=False)
    raise credentials_exception


async def get_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Ensures user is active (redundant safety check)."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user"
        )
    return current_user


# ── RBAC Permission Checker ───────────────────────────────────────────────────


def require_permission(permission: Permission) -> Callable[..., Any]:
    """
    Dependency factory for permission-based access control.
    Usage: Depends(require_permission(Permission.SCAN_CREATE))
    """

    async def permission_checker(
        request: Request,
        current_user: Annotated[User, Depends(get_active_user)],
    ) -> User:
        if not has_permission(Role(current_user.role), permission):
            audit_log(
                "authz_permission_denied",
                str(current_user.id),
                get_client_ip(request),
                resource=str(request.url),
                details={"required_permission": permission},
                success=False,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {permission} required",
            )
        return current_user

    return permission_checker


def require_role(min_role: Role) -> Callable[..., Any]:
    """
    Dependency factory for role-based access control.
    Roles are ordered: VIEWER < ANALYST < ADMIN < SUPER_ADMIN
    """
    role_order = [Role.VIEWER, Role.ANALYST, Role.ADMIN, Role.SUPER_ADMIN]

    async def role_checker(
        request: Request,
        current_user: Annotated[User, Depends(get_active_user)],
    ) -> User:
        try:
            user_role_idx = role_order.index(Role(current_user.role))
            required_idx = role_order.index(min_role)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role"
            )

        if user_role_idx < required_idx:
            audit_log(
                "authz_role_denied",
                str(current_user.id),
                get_client_ip(request),
                details={"required_role": min_role, "user_role": current_user.role},
                success=False,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role {min_role} or higher required",
            )
        return current_user

    return role_checker


# ── Utilities ─────────────────────────────────────────────────────────────────


def get_client_ip(request: Request) -> str:
    """Extract real client IP from request (handles proxies)."""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    return request.client.host if request.client else "unknown"


def _utcnow() -> Any:
    from datetime import UTC, datetime
    return datetime.now(UTC)
