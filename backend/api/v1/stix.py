from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.database import get_db
from backend.schemas.stix import StixIndicatorCreate, StixIndicatorResponse, StixRelationshipCreate, StixRelationshipResponse
from backend.services.stix_service import StixService

router = APIRouter(prefix="/stix", tags=["STIX 2.1"])

@router.post("/indicators", response_model=StixIndicatorResponse, status_code=status.HTTP_201_CREATED)
async def create_indicator(data: StixIndicatorCreate, db: AsyncSession = Depends(get_db)):
    obj = await StixService.create_indicator(db, data)
    return obj

@router.get("/objects/{stix_id}", response_model=StixIndicatorResponse)
async def get_object(stix_id: str, db: AsyncSession = Depends(get_db)):
    obj = await StixService.get_object(db, stix_id)
    if not obj:
        raise HTTPException(status_code=404, detail="STIX object not found")
    return obj

@router.post("/relationships", response_model=StixRelationshipResponse, status_code=status.HTTP_201_CREATED)
async def create_relationship(data: StixRelationshipCreate, db: AsyncSession = Depends(get_db)):
    try:
        rel = await StixService.create_relationship(db, data)
        return rel
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
