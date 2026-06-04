from sqlalchemy.ext.asyncio import AsyncSession
from backend.repositories.stix_repo import StixRepository
from backend.schemas.stix import StixIndicatorCreate, StixRelationshipCreate
from backend.models.stix import StixObject, StixRelationship

class StixService:
    @staticmethod
    async def create_indicator(session: AsyncSession, data: StixIndicatorCreate) -> StixObject:
        repo = StixRepository(session)
        return await repo.create_indicator(data)
        
    @staticmethod
    async def get_object(session: AsyncSession, stix_id: str) -> StixObject | None:
        repo = StixRepository(session)
        return await repo.get_object(stix_id)
        
    @staticmethod
    async def create_relationship(session: AsyncSession, data: StixRelationshipCreate) -> StixRelationship:
        repo = StixRepository(session)
        # Verify source and target exist
        source = await repo.get_object(data.source_ref)
        target = await repo.get_object(data.target_ref)
        if not source or not target:
            raise ValueError("Source or target object does not exist")
        return await repo.create_relationship(data)
