"""
CyberGhost OSINT Enterprise — Pydantic Schemas
Input validation and output serialization
"""
from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, SecretStr


class _Base(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# ── Auth Schemas ──────────────────────────────────────────────────────────────


class RegisterRequest(_Base):
    username: str = Field(min_length=3, max_length=64, pattern=r"^[a-zA-Z0-9_-]+$")
    email: EmailStr
    password: SecretStr = Field(min_length=12, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)
    organization: str | None = Field(default=None, max_length=255)


class LoginResponse(_Base):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: "UserResponse"


class TokenResponse(_Base):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshRequest(_Base):
    refresh_token: str


class APIKeyCreateRequest(_Base):
    name: str = Field(min_length=1, max_length=100)
    expires_at: datetime | None = None


class APIKeyResponse(_Base):
    id: str
    name: str
    key: str | None = None  # Only in creation response
    prefix: str
    expires_at: datetime | None
    created_at: datetime
    last_used: datetime | None = None
    usage_count: int = 0
    is_active: bool = True


class UserResponse(_Base):
    id: UUID
    username: str
    email: str
    role: str
    is_active: bool
    full_name: str | None
    organization: str | None
    last_login: datetime | None
    created_at: datetime


# ── Scan Schemas ──────────────────────────────────────────────────────────────


class ScanCreateRequest(_Base):
    target: str = Field(min_length=1, max_length=512)
    scan_type: str = Field(default="full")
    priority: int = Field(default=5, ge=1, le=10)
    config: dict[str, Any] | None = None

    @property
    def normalized_target(self) -> str:
        """Return cleaned target — strips whitespace."""
        return self.target.strip()


class ScanResponse(_Base):
    id: UUID
    target: str
    scan_type: str
    status: str
    priority: int
    celery_task_id: str | None
    error_message: str | None
    started_at: datetime | None
    completed_at: datetime | None
    duration_seconds: int | None
    created_at: datetime


class ScanListResponse(_Base):
    items: list[ScanResponse]
    total: int
    page: int
    per_page: int
    pages: int


# ── Result Schemas ────────────────────────────────────────────────────────────


class ResultResponse(_Base):
    id: UUID
    scan_id: UUID
    module: str
    severity: str
    title: str
    description: str | None
    data: dict[str, Any]
    tags: list[str] | None
    created_at: datetime


# ── IOC Schemas ───────────────────────────────────────────────────────────────


class IOCResponse(_Base):
    id: UUID
    value: str
    ioc_type: str
    severity: str
    reputation_score: int | None
    malicious: bool
    confidence: int
    tags: list[str] | None
    tlp: str
    stix_id: str | None
    first_seen: datetime
    last_seen: datetime


class IOCCreateRequest(_Base):
    value: str = Field(min_length=1, max_length=512)
    ioc_type: str
    tags: list[str] | None = None
    tlp: str = Field(default="AMBER", pattern=r"^(WHITE|GREEN|AMBER|RED)$")


# ── Alert Schemas ─────────────────────────────────────────────────────────────


class AlertResponse(_Base):
    id: UUID
    title: str
    description: str
    severity: str
    source: str
    acknowledged: bool
    created_at: datetime


# ── Health Schemas ────────────────────────────────────────────────────────────


class HealthResponse(_Base):
    status: str
    version: str
    environment: str
    timestamp: datetime
    services: dict[str, str]
