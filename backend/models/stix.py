import uuid
from datetime import UTC, datetime
from sqlalchemy import String, DateTime, ForeignKey, Index, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from backend.core.database import Base

def utcnow() -> datetime:
    return datetime.now(UTC)

class StixObject(Base):
    __tablename__ = "stix_objects"
    
    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    created: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    modified: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    name: Mapped[str | None] = mapped_column(String(255), index=True)
    description: Mapped[str | None] = mapped_column(Text)
    pattern: Mapped[str | None] = mapped_column(Text)
    pattern_type: Mapped[str | None] = mapped_column(String(50))
    valid_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    object_data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    
    __table_args__ = (
        Index("idx_stix_obj_type", "type"),
        Index("idx_stix_obj_created", "created"),
    )

class StixRelationship(Base):
    __tablename__ = "stix_relationships"
    
    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    type: Mapped[str] = mapped_column(String(50), default="relationship", nullable=False)
    relationship_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    source_ref: Mapped[str] = mapped_column(String(255), ForeignKey("stix_objects.id", ondelete="CASCADE"), nullable=False, index=True)
    target_ref: Mapped[str] = mapped_column(String(255), ForeignKey("stix_objects.id", ondelete="CASCADE"), nullable=False, index=True)
    created: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    modified: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    description: Mapped[str | None] = mapped_column(Text)
    object_data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    
    __table_args__ = (
        UniqueConstraint("source_ref", "target_ref", "relationship_type", name="uq_stix_rel"),
    )
