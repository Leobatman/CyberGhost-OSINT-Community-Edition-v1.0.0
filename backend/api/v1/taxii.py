from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.database import get_db
from backend.schemas.taxii import TaxiiDiscovery, TaxiiApiRoot, TaxiiCollections, TaxiiCollection, TaxiiEnvelope
from backend.services.taxii_service import TaxiiService

router = APIRouter(prefix="/taxii", tags=["TAXII 2.1"])

TAXII_MEDIA_TYPE = "application/taxii+json;version=2.1"

def set_taxii_headers(response: Response):
    response.headers["Content-Type"] = TAXII_MEDIA_TYPE

@router.get("/taxii2/", response_model=TaxiiDiscovery)
async def get_discovery(response: Response):
    set_taxii_headers(response)
    return TaxiiService.get_discovery()

@router.get("/api1/", response_model=TaxiiApiRoot)
async def get_api_root(response: Response):
    set_taxii_headers(response)
    return TaxiiService.get_api_root()

@router.get("/api1/collections/", response_model=TaxiiCollections)
async def get_collections(response: Response):
    set_taxii_headers(response)
    return TaxiiService.get_collections()

@router.get("/api1/collections/{collection_id}/", response_model=TaxiiCollection)
async def get_collection(collection_id: str, response: Response):
    col = TaxiiService.get_collection(collection_id)
    if not col:
        raise HTTPException(status_code=404, detail="Collection not found")
    set_taxii_headers(response)
    return col

@router.get("/api1/collections/{collection_id}/objects/", response_model=TaxiiEnvelope)
async def get_objects(collection_id: str, response: Response, db: AsyncSession = Depends(get_db)):
    col = TaxiiService.get_collection(collection_id)
    if not col:
        raise HTTPException(status_code=404, detail="Collection not found")
    set_taxii_headers(response)
    return await TaxiiService.get_objects(db, collection_id)
