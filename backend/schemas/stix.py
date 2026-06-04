from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class StixObjectBase(BaseModel):
    id: str
    type: str
    created: datetime
    modified: datetime
    name: Optional[str] = None
    description: Optional[str] = None
    object_data: Dict[str, Any]

class StixIndicatorCreate(BaseModel):
    name: str
    description: Optional[str] = None
    pattern: str
    pattern_type: str
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None

class StixIndicatorResponse(StixObjectBase):
    pattern: Optional[str] = None
    pattern_type: Optional[str] = None
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None

class StixRelationshipCreate(BaseModel):
    relationship_type: str
    source_ref: str
    target_ref: str
    description: Optional[str] = None

class StixRelationshipResponse(BaseModel):
    id: str
    type: str
    relationship_type: str
    source_ref: str
    target_ref: str
    created: datetime
    modified: datetime
    description: Optional[str] = None
