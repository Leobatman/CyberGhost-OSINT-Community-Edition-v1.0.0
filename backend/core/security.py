"""
CyberGhost OSINT Enterprise — Security Layer
JWT, RBAC, Password Hashing, Audit Logging
"""
from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any

import structlog
from jose import JWTError, jwt
from passlib.context import CryptContext

from backend.core.config import settings

log = structlog.get_logger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ── Roles & Permissions ───────────────────────────────────────────────────────


class Role(StrEnum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    ANALYST = "analyst"
    VIEWER = "viewer"
    API_KEY = "api_key"


class Permission(StrEnum):
    # Scans
    SCAN_CREATE = "scan:create"
    SCAN_READ = "scan:read"
    SCAN_DELETE = "scan:delete"
    SCAN_STOP = "scan:stop"

    # Threat Intelligence
    INTEL_READ = "intel:read"
    INTEL_CREATE = "intel:create"
    INTEL_EXPORT = "intel:export"

    # User Management
    USER_READ = "user:read"
    USER_CREATE = "user:create"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"

    # Configuration
    CONFIG_READ = "config:read"
    CONFIG_WRITE = "config:write"

    # Reports
    REPORT_READ = "report:read"
    REPORT_CREATE = "report:create"
    REPORT_DELETE = "report:delete"

    # API Keys Management
    APIKEY_MANAGE = "apikey:manage"


# Role → Permissions mapping
ROLE_PERMISSIONS: dict[Role, set[Permission]] = {
    Role.SUPER_ADMIN: set(Permission),  # All permissions
    Role.ADMIN: {
        Permission.SCAN_CREATE,
        Permission.SCAN_READ,
        Permission.SCAN_DELETE,
        Permission.SCAN_STOP,
        Permission.INTEL_READ,
        Permission.INTEL_CREATE,
        Permission.INTEL_EXPORT,
        Permission.USER_READ,
        Permission.USER_CREATE,
        Permission.USER_UPDATE,
        Permission.CONFIG_READ,
        Permission.CONFIG_WRITE,
        Permission.REPORT_READ,
        Permission.REPORT_CREATE,
        Permission.REPORT_DELETE,
        Permission.APIKEY_MANAGE,
    },
    Role.ANALYST: {
        Permission.SCAN_CREATE,
        Permission.SCAN_READ,
        Permission.SCAN_STOP,
        Permission.INTEL_READ,
        Permission.INTEL_CREATE,
        Permission.INTEL_EXPORT,
        Permission.REPORT_READ,
        Permission.REPORT_CREATE,
    },
    Role.VIEWER: {
        Permission.SCAN_READ,
        Permission.INTEL_READ,
        Permission.REPORT_READ,
    },
    Role.API_KEY: {
        Permission.SCAN_CREATE,
        Permission.SCAN_READ,
        Permission.INTEL_READ,
    },
}


def get_role_permissions(role: Role) -> set[Permission]:
    return ROLE_PERMISSIONS.get(role, set())


def has_permission(role: Role, permission: Permission) -> bool:
    return permission in get_role_permissions(role)


# ── Password Hashing ──────────────────────────────────────────────────────────


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its bcrypt hash."""
    return pwd_context.verify(plain_password, hashed_password)


# ── JWT Tokens ────────────────────────────────────────────────────────────────


class TokenType(StrEnum):
    ACCESS = "access"
    REFRESH = "refresh"


def create_access_token(
    subject: str,
    role: Role,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """Create a signed JWT access token."""
    now = datetime.now(UTC)
    expire = now + timedelta(
        minutes=settings.jwt.access_token_expire_minutes
    )
    claims: dict[str, Any] = {
        "sub": subject,
        "role": role.value,
        "type": TokenType.ACCESS,
        "iat": now,
        "exp": expire,
        "jti": secrets.token_urlsafe(16),
    }
    if extra_claims:
        claims.update(extra_claims)

    return jwt.encode(
        claims,
        settings.jwt.secret_key.get_secret_value(),
        algorithm=settings.jwt.algorithm,
    )


def create_refresh_token(subject: str, role: Role) -> str:
    """Create a signed JWT refresh token with longer expiry."""
    now = datetime.now(UTC)
    expire = now + timedelta(days=settings.jwt.refresh_token_expire_days)
    claims: dict[str, Any] = {
        "sub": subject,
        "role": role.value,
        "type": TokenType.REFRESH,
        "iat": now,
        "exp": expire,
        "jti": secrets.token_urlsafe(16),
    }
    return jwt.encode(
        claims,
        settings.jwt.secret_key.get_secret_value(),
        algorithm=settings.jwt.algorithm,
    )


def decode_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT token. Raises JWTError on failure."""
    try:
        payload = jwt.decode(
            token,
            settings.jwt.secret_key.get_secret_value(),
            algorithms=[settings.jwt.algorithm],
        )
        return payload
    except JWTError as e:
        log.warning("jwt_decode_failed", error=str(e))
        raise


# ── API Key Generation ────────────────────────────────────────────────────────


def generate_api_key() -> tuple[str, str]:
    """
    Generate a new API key pair.
    Returns (raw_key, hashed_key) — store only the hash.
    """
    raw_key = f"cg_{secrets.token_urlsafe(32)}"
    hashed_key = hash_password(raw_key)
    return raw_key, hashed_key


def verify_api_key(raw_key: str, hashed_key: str) -> bool:
    """Verify an API key against its stored hash."""
    return verify_password(raw_key, hashed_key)


# ── Audit Logging ─────────────────────────────────────────────────────────────


def audit_log(
    event: str,
    user_id: str | None,
    ip_address: str | None,
    resource: str | None = None,
    details: dict[str, Any] | None = None,
    success: bool = True,
) -> None:
    """Structured audit log entry — all security events MUST use this."""
    log.info(
        "audit_event",
        event=event,
        user_id=user_id,
        ip_address=ip_address,
        resource=resource,
        details=details or {},
        success=success,
        timestamp=datetime.now(UTC).isoformat(),
    )
