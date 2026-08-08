"""
CyberGhost OSINT Enterprise — Database Models (V15.0)
SQLAlchemy 2.0 ORM — Multi-tenant, RBAC & Security Focus
"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Table,
    Column
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from backend.core.database import Base


def uuid_pk() -> Mapped[uuid.UUID]:
    """Standard UUID primary key factory."""
    return mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )


def utcnow() -> datetime:
    return datetime.now(UTC)


# ── Enums ─────────────────────────────────────────────────────────────────────

class ScanStatus(StrEnum):
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ScanType(StrEnum):
    FULL = "full"
    RECON = "recon"
    THREAT_INTEL = "threat_intel"
    SUBDOMAIN = "subdomain"
    PORT_SCAN = "port_scan"
    EMAIL = "email"
    SOCIAL = "social"
    GITHUB = "github"
    GEOINT = "geoint"
    BUSINESS = "business"
    DARK_WEB = "dark_web"
    CERT_TRANSPARENCY = "cert_transparency"
    ASN = "asn"
    PASSIVE_DNS = "passive_dns"


class Severity(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class IOCType(StrEnum):
    IP = "ip"
    DOMAIN = "domain"
    URL = "url"
    HASH_MD5 = "hash_md5"
    HASH_SHA1 = "hash_sha1"
    HASH_SHA256 = "hash_sha256"
    EMAIL = "email"
    ASN = "asn"
    CIDR = "cidr"
    CVE = "cve"
    FILENAME = "filename"
    MUTEX = "mutex"
    REGISTRY_KEY = "registry_key"

# ── Multi-Tenant Model ────────────────────────────────────────────────────────

class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = uuid_pk()
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    tier: Mapped[str] = mapped_column(String(50), default="standard") # standard, enterprise
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    
    users: Mapped[list["User"]] = relationship("User", back_populates="tenant")
    scans: Mapped[list["Scan"]] = relationship("Scan", back_populates="tenant")
    iocs: Mapped[list["IOC"]] = relationship("IOC", back_populates="tenant")

# ── RBAC Models ─────────────────────────────────────────────────────────────

# Many-to-Many para Roles e Permissions
role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column("permission_id", UUID(as_uuid=True), ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True),
)

class Permission(Base):
    __tablename__ = "permissions"
    
    id: Mapped[uuid.UUID] = uuid_pk()
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False) # ex: "scan:write"
    description: Mapped[str | None] = mapped_column(Text)
    
class Role(Base):
    __tablename__ = "roles"

    id: Mapped[uuid.UUID] = uuid_pk()
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True) # Null = System Role
    name: Mapped[str] = mapped_column(String(100), nullable=False) # Admin, Analyst
    description: Mapped[str | None] = mapped_column(Text)
    
    permissions: Mapped[list["Permission"]] = relationship(secondary=role_permissions)

# ── User Model ────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = uuid_pk()
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    role_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("roles.id", ondelete="RESTRICT"), nullable=False)
    
    username: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255))
    last_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    # Relationships
    tenant: Mapped[Tenant] = relationship("Tenant", back_populates="users")
    role: Mapped[Role] = relationship("Role")
    scans: Mapped[list["Scan"]] = relationship("Scan", back_populates="user", cascade="all, delete-orphan")
    api_keys: Mapped[list["APIKey"]] = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")
    audit_logs: Mapped[list["AuditLog"]] = relationship("AuditLog", back_populates="user")

    __table_args__ = (
        UniqueConstraint("tenant_id", "email", name="uq_tenant_email"),
        UniqueConstraint("tenant_id", "username", name="uq_tenant_username"),
    )


# ── API Key Model ─────────────────────────────────────────────────────────────


class APIKey(Base):
    __tablename__ = "api_keys"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    key_hash: Mapped[str] = mapped_column(String(255), nullable=False)  # bcrypt hash
    key_prefix: Mapped[str] = mapped_column(
        String(8), nullable=False
    )  # First 8 chars for display
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_used: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    usage_count: Mapped[int] = mapped_column(Integer, default=0)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )

    user: Mapped[User] = relationship("User", back_populates="api_keys")


# ── Scan Model ────────────────────────────────────────────────────────────────


class Scan(Base):
    __tablename__ = "scans"

    id: Mapped[uuid.UUID] = uuid_pk()
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    target: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    scan_type: Mapped[ScanType] = mapped_column(
        Enum(ScanType, name="scan_type"), nullable=False
    )
    status: Mapped[ScanStatus] = mapped_column(
        Enum(ScanStatus, name="scan_status"),
        default=ScanStatus.PENDING,
        nullable=False,
        index=True,
    )
    celery_task_id: Mapped[str | None] = mapped_column(String(255))
    priority: Mapped[int] = mapped_column(Integer, default=5)  # 1-10, 10=highest
    config: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    error_message: Mapped[str | None] = mapped_column(Text)
    ai_summary: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    duration_seconds: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )

    # Relationships
    tenant: Mapped[Tenant] = relationship("Tenant", back_populates="scans")
    user: Mapped[User | None] = relationship("User", back_populates="scans")
    results: Mapped[list["ScanResult"]] = relationship(
        "ScanResult", back_populates="scan", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_scans_tenant_user_status", "tenant_id", "user_id", "status"),
        Index("idx_scans_tenant_target", "tenant_id", "target"),
        Index("idx_scans_created", "created_at"),
    )


# ── Scan Result Model ─────────────────────────────────────────────────────────


class ScanResult(Base):
    __tablename__ = "scan_results"

    id: Mapped[uuid.UUID] = uuid_pk()
    scan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("scans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    module: Mapped[str] = mapped_column(String(100), nullable=False)
    severity: Mapped[Severity] = mapped_column(
        Enum(Severity, name="severity_level"),
        default=Severity.INFO,
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    data: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    raw_data: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    tags: Mapped[list[str] | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )

    scan: Mapped[Scan] = relationship("Scan", back_populates="results")

    __table_args__ = (
        Index("idx_results_scan_severity", "scan_id", "severity"),
        Index("idx_results_module", "module"),
    )


# ── IOC Model ─────────────────────────────────────────────────────────────────


class IOC(Base):
    __tablename__ = "iocs"

    id: Mapped[uuid.UUID] = uuid_pk()
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    value: Mapped[str] = mapped_column(String(512), nullable=False)
    ioc_type: Mapped[IOCType] = mapped_column(
        Enum(IOCType, name="ioc_type"), nullable=False, index=True
    )
    severity: Mapped[Severity] = mapped_column(
        Enum(Severity, name="ioc_severity"),
        default=Severity.INFO,
        nullable=False,
    )
    reputation_score: Mapped[int | None] = mapped_column(Integer)  # 0-100
    malicious: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    confidence: Mapped[int] = mapped_column(Integer, default=50)  # 0-100
    tags: Mapped[list[str] | None] = mapped_column(JSONB)
    tlp: Mapped[str] = mapped_column(String(10), default="AMBER")  # TLP marking
    stix_id: Mapped[str | None] = mapped_column(
        String(255), unique=True
    )  # STIX 2.1 ID
    enrichment_data: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    first_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )
    last_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )
    expiry: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )

    tenant: Mapped[Tenant] = relationship("Tenant", back_populates="iocs")

    __table_args__ = (
        UniqueConstraint("tenant_id", "value", "ioc_type", name="uq_tenant_ioc_value_type"),
        Index("idx_ioc_tenant_value", "tenant_id", "value"),
        Index("idx_ioc_malicious_type", "malicious", "ioc_type"),
    )


# ── Alert Model ───────────────────────────────────────────────────────────────


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[uuid.UUID] = uuid_pk()
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[Severity] = mapped_column(
        Enum(Severity, name="alert_severity"), nullable=False, index=True
    )
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    data: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    acknowledged: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    acknowledged_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, index=True
    )


# ── Audit Log Model ───────────────────────────────────────────────────────────


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = uuid_pk()
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    event: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    resource: Mapped[str | None] = mapped_column(String(255))
    ip_address: Mapped[str | None] = mapped_column(String(45))
    user_agent: Mapped[str | None] = mapped_column(String(512))
    details: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    success: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, index=True
    )

    user: Mapped[User | None] = relationship("User", back_populates="audit_logs")

    __table_args__ = (
        Index("idx_audit_tenant_user_event", "tenant_id", "user_id", "event"),
        Index("idx_audit_created", "created_at"),
    )
