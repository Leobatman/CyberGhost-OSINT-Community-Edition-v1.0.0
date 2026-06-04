"""
CyberGhost OSINT Enterprise — Authentication Router
Login, Register, Refresh, Logout, API Keys
"""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db
from backend.core.deps import get_active_user, get_client_ip, require_permission
from backend.core.security import (
    Permission,
    Role,
    TokenType,
    audit_log,
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_api_key,
    hash_password,
    verify_password,
)
from backend.models.models import APIKey, AuditLog, User
from backend.schemas.auth import (
    APIKeyCreateRequest,
    APIKeyResponse,
    LoginResponse,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)

log = structlog.get_logger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])

MAX_FAILED_ATTEMPTS = 5
LOCKOUT_MINUTES = 30


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(
    request: Request,
    body: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> User:
    """Register a new user account."""
    ip = get_client_ip(request)

    # Check uniqueness
    existing = await db.execute(
        select(User).where(
            (User.username == body.username) | (User.email == body.email)
        )
    )
    if existing.scalar_one_or_none():
        audit_log("register_duplicate", None, ip, success=False)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username or email already exists",
        )

    user = User(
        username=body.username,
        email=str(body.email),
        hashed_password=hash_password(body.password.get_secret_value()),
        full_name=body.full_name,
        organization=body.organization,
        role=Role.VIEWER,  # New users are viewers by default
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)

    audit_log("register_success", str(user.id), ip, resource=body.username)
    log.info("user_registered", user_id=str(user.id), username=body.username)
    return user


@router.post("/login", response_model=LoginResponse)
async def login(
    request: Request,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: AsyncSession = Depends(get_db),
) -> LoginResponse:
    """Authenticate and receive JWT tokens."""
    ip = get_client_ip(request)
    now = datetime.now(UTC)

    # Find user by username or email
    result = await db.execute(
        select(User).where(
            (User.username == form_data.username)
            | (User.email == form_data.username)
        )
    )
    user = result.scalar_one_or_none()

    if not user:
        audit_log("login_user_not_found", None, ip, success=False)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check lock
    if user.locked_until and user.locked_until > now:
        audit_log("login_account_locked", str(user.id), ip, success=False)
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=f"Account locked until {user.locked_until.isoformat()}",
        )

    # Verify password
    if not verify_password(form_data.password, user.hashed_password):
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= MAX_FAILED_ATTEMPTS:
            from datetime import timedelta
            user.locked_until = now + timedelta(minutes=LOCKOUT_MINUTES)
            log.warning(
                "user_locked",
                user_id=str(user.id),
                attempts=user.failed_login_attempts,
            )
        await db.commit()
        audit_log("login_invalid_password", str(user.id), ip, success=False)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    if not user.is_active:
        audit_log("login_inactive_user", str(user.id), ip, success=False)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Account disabled"
        )

    # Success — reset failed attempts
    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login = now
    await db.commit()

    access_token = create_access_token(str(user.id), Role(user.role))
    refresh_token = create_refresh_token(str(user.id), Role(user.role))

    audit_log("login_success", str(user.id), ip)
    log.info("user_logged_in", user_id=str(user.id))

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=30 * 60,
        user=UserResponse.model_validate(user),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: Request,
    body: RefreshRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Exchange refresh token for new access token."""
    ip = get_client_ip(request)
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid refresh token",
    )

    try:
        payload = decode_token(body.refresh_token)
    except Exception:
        audit_log("refresh_invalid_token", None, ip, success=False)
        raise credentials_exception

    if payload.get("type") != TokenType.REFRESH:
        raise credentials_exception

    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise credentials_exception

    access_token = create_access_token(str(user.id), Role(user.role))
    audit_log("token_refreshed", str(user.id), ip)

    return TokenResponse(access_token=access_token, token_type="bearer", expires_in=30 * 60)


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: Annotated[User, Depends(get_active_user)],
) -> User:
    """Get current authenticated user's profile."""
    return current_user


@router.post("/api-keys", response_model=APIKeyResponse, status_code=201)
async def create_api_key(
    request: Request,
    body: APIKeyCreateRequest,
    current_user: Annotated[User, Depends(require_permission(Permission.APIKEY_MANAGE))],
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Create a new API key. The raw key is only shown once."""
    raw_key, hashed_key = generate_api_key()

    api_key = APIKey(
        user_id=current_user.id,
        name=body.name,
        key_hash=hashed_key,
        key_prefix=raw_key[:8],
        expires_at=body.expires_at,
    )
    db.add(api_key)
    await db.flush()

    audit_log(
        "api_key_created", str(current_user.id), get_client_ip(request),
        resource=body.name
    )

    return {
        "id": str(api_key.id),
        "name": api_key.name,
        "key": raw_key,  # Only time raw key is returned
        "prefix": raw_key[:8],
        "expires_at": api_key.expires_at,
        "created_at": api_key.created_at,
    }


@router.get("/api-keys", response_model=list[APIKeyResponse])
async def list_api_keys(
    current_user: Annotated[User, Depends(get_active_user)],
    db: AsyncSession = Depends(get_db),
) -> list[APIKey]:
    """List all API keys for the current user."""
    result = await db.execute(
        select(APIKey)
        .where(APIKey.user_id == current_user.id)
        .order_by(APIKey.created_at.desc())
    )
    return list(result.scalars().all())


@router.delete("/api-keys/{key_id}", status_code=204)
async def revoke_api_key(
    request: Request,
    key_id: str,
    current_user: Annotated[User, Depends(get_active_user)],
    db: AsyncSession = Depends(get_db),
) -> None:
    """Revoke an API key."""
    result = await db.execute(
        select(APIKey).where(
            APIKey.id == key_id,
            APIKey.user_id == current_user.id,
        )
    )
    api_key = result.scalar_one_or_none()
    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")

    api_key.is_active = False
    audit_log("api_key_revoked", str(current_user.id), get_client_ip(request))
