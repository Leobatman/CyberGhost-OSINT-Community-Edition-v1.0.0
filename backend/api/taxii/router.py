from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import Any

from backend.core.database import get_db
from backend.models.stix import StixObject
from backend.core.security.rbac import require_permissions

router = APIRouter(prefix="/taxii2", tags=["taxii"])

# MIME types specific to TAXII 2.1
TAXII_21_CONTENT_TYPE = "application/taxii+json;version=2.1"
STIX_21_CONTENT_TYPE = "application/stix+json;version=2.1"

@router.get("/", summary="Server Discovery")
async def server_discovery() -> dict[str, Any]:
    """TAXII 2.1 Server Discovery Endpoint."""
    return {
        "title": "CyberGhost OSINT TAXII 2.1 Server",
        "description": "Enterprise CTI Platform Feeds",
        "contact": "soc@cyberghost.local",
        "default": "https://api.cyberghost.local/taxii2/api1/",
        "api_roots": [
            "https://api.cyberghost.local/taxii2/api1/"
        ]
    }

@router.get("/api1/collections/", summary="Get Collections")
@require_permissions("taxii:read")
async def get_collections(request: Request) -> dict[str, Any]:
    """Get list of STIX collections available to this Tenant."""
    # Dummy static collection for the tenant
    tenant_id = request.state.tenant_id
    
    return {
        "collections": [
            {
                "id": "c1a93d40-7e1d-4861-b4fa-4ce2f56ccbf5",
                "title": f"CyberGhost Master Intel (Tenant {tenant_id})",
                "description": "Contains all OSINT Indicators and Threat Actors discovered.",
                "can_read": True,
                "can_write": False,
                "media_types": [
                    STIX_21_CONTENT_TYPE
                ]
            }
        ]
    }

@router.get("/api1/collections/{collection_id}/objects/", summary="Get Objects")
@require_permissions("taxii:read")
async def get_objects(
    collection_id: str,
    request: Request,
    db: Session = Depends(get_db)
) -> dict[str, Any]:
    """Fetch STIX 2.1 objects from the database (TAXII Envelope)."""
    tenant_id = request.state.tenant_id
    
    # Query STIX Objects from DB
    stmt = select(StixObject).where(StixObject.tenant_id == tenant_id).limit(100)
    stix_records = db.execute(stmt).scalars().all()
    
    objects = [record.object_data for record in stix_records]
    
    return {
        "more": False,
        "objects": objects
    }
