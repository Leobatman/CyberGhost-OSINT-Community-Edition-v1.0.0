import uuid
from datetime import UTC, datetime
from sqlalchemy import String, DateTime, ForeignKey, Index, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from backend.core.database import Base

def utcnow() -> datetime:
    return datetime.now(UTC)

class StixObject(Base):
    """STIX 2.1 Domain Objects (SDO) and Cyber Observable Objects (SCO)"""
    __tablename__ = "stix_objects"
    
    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(50), nullable=False, index=True) # indicator, infrastructure, threat-actor, malware, campaign
    created: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    modified: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    
    name: Mapped[str | None] = mapped_column(String(255), index=True)
    description: Mapped[str | None] = mapped_column(Text)
    
    # Specific to Indicators
    pattern: Mapped[str | None] = mapped_column(Text)
    pattern_type: Mapped[str | None] = mapped_column(String(50))
    valid_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    
    # Full STIX JSON representation
    object_data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    
    __table_args__ = (
        Index("idx_stix_tenant_type", "tenant_id", "type"),
        Index("idx_stix_tenant_created", "tenant_id", "created"),
    )

class StixRelationship(Base):
    """STIX 2.1 Relationship Objects (SRO)"""
    __tablename__ = "stix_relationships"
    
    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(50), default="relationship", nullable=False)
    relationship_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    
    source_ref: Mapped[str] = mapped_column(String(255), ForeignKey("stix_objects.id", ondelete="CASCADE"), nullable=False, index=True)
    target_ref: Mapped[str] = mapped_column(String(255), ForeignKey("stix_objects.id", ondelete="CASCADE"), nullable=False, index=True)
    
    created: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    modified: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    description: Mapped[str | None] = mapped_column(Text)
    
    # Full STIX JSON representation
    object_data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    
    __table_args__ = (
        UniqueConstraint("tenant_id", "source_ref", "target_ref", "relationship_type", name="uq_tenant_stix_rel"),
    )
