from typing import List
from backend.schemas.taxii import TaxiiDiscovery, TaxiiApiRoot, TaxiiCollection, TaxiiCollections, TaxiiEnvelope
from backend.schemas.stix import StixIndicatorResponse
from backend.services.stix_service import StixService
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.models.stix import StixObject

class TaxiiService:
    DEFAULT_API_ROOT = "http://localhost:8000/api/v1/taxii/api1/"
    DEFAULT_COLLECTION_ID = "91a7b528-80eb-42ed-a74d-c6fbd5a26116"
    
    @classmethod
    def get_discovery(cls) -> TaxiiDiscovery:
        return TaxiiDiscovery(
            title="CyberGhost-OSINT TAXII Server",
            description="TAXII 2.1 Discovery Endpoint for Enterprise CTI",
            contact="soc@cyberghost.local",
            default=cls.DEFAULT_API_ROOT,
            api_roots=[cls.DEFAULT_API_ROOT]
        )
        
    @classmethod
    def get_api_root(cls) -> TaxiiApiRoot:
        return TaxiiApiRoot(
            title="CyberGhost Primary API Root",
            description="Default API root for CyberGhost Collections",
        )

    @classmethod
    def get_collections(cls) -> TaxiiCollections:
        c1 = TaxiiCollection(
            id=cls.DEFAULT_COLLECTION_ID,
            title="Default OSINT Indicators",
            description="Indicators collected by CyberGhost OSINT engines",
            can_read=True,
            can_write=True
        )
        return TaxiiCollections(collections=[c1])
        
    @classmethod
    def get_collection(cls, collection_id: str) -> TaxiiCollection | None:
        if collection_id == cls.DEFAULT_COLLECTION_ID:
            return cls.get_collections().collections[0]
        return None

    @classmethod
    async def get_objects(cls, session: AsyncSession, collection_id: str) -> TaxiiEnvelope:
        if collection_id != cls.DEFAULT_COLLECTION_ID:
            return TaxiiEnvelope()
            
        stmt = select(StixObject).limit(100)
        result = await session.execute(stmt)
        objects = result.scalars().all()
        
        return TaxiiEnvelope(
            more=False,
            objects=[obj.object_data for obj in objects]
        )
