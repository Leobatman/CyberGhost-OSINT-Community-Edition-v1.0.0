from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.models.stix import StixObject, StixRelationship
from backend.schemas.stix import StixIndicatorCreate, StixRelationshipCreate
import uuid
from datetime import UTC, datetime

class StixRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_indicator(self, data: StixIndicatorCreate) -> StixObject:
        stix_id = f"indicator--{uuid.uuid4()}"
        now = datetime.now(UTC)
        
        raw_data = {
            "type": "indicator",
            "spec_version": "2.1",
            "id": stix_id,
            "created": now.isoformat(),
            "modified": now.isoformat(),
            "name": data.name,
            "description": data.description,
            "pattern": data.pattern,
            "pattern_type": data.pattern_type,
            "valid_from": data.valid_from.isoformat() if data.valid_from else now.isoformat()
        }
        
        obj = StixObject(
            id=stix_id,
            type="indicator",
            name=data.name,
            description=data.description,
            pattern=data.pattern,
            pattern_type=data.pattern_type,
            valid_from=data.valid_from or now,
            valid_until=data.valid_until,
            object_data=raw_data
        )
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def get_object(self, stix_id: str) -> StixObject | None:
        stmt = select(StixObject).where(StixObject.id == stix_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def create_relationship(self, data: StixRelationshipCreate) -> StixRelationship:
        rel_id = f"relationship--{uuid.uuid4()}"
        now = datetime.now(UTC)
        
        raw_data = {
            "type": "relationship",
            "spec_version": "2.1",
            "id": rel_id,
            "created": now.isoformat(),
            "modified": now.isoformat(),
            "relationship_type": data.relationship_type,
            "source_ref": data.source_ref,
            "target_ref": data.target_ref,
            "description": data.description
        }
        
        rel = StixRelationship(
            id=rel_id,
            relationship_type=data.relationship_type,
            source_ref=data.source_ref,
            target_ref=data.target_ref,
            description=data.description,
            object_data=raw_data
        )
        self.session.add(rel)
        await self.session.commit()
        await self.session.refresh(rel)
        return rel
