from pydantic import BaseModel, HttpUrl
from typing import List, Optional, Any

class TaxiiApiRoot(BaseModel):
    title: str
    description: Optional[str] = None
    versions: List[str] = ["taxii-2.1"]
    max_content_length: int = 104857600

class TaxiiDiscovery(BaseModel):
    title: str
    description: Optional[str] = None
    contact: Optional[str] = None
    default: Optional[str] = None
    api_roots: List[str] = []

class TaxiiCollection(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    can_read: bool = True
    can_write: bool = True
    media_types: List[str] = ["application/taxii+json;version=2.1"]

class TaxiiCollections(BaseModel):
    collections: List[TaxiiCollection]

class TaxiiEnvelope(BaseModel):
    more: bool = False
    objects: List[Any] = []
