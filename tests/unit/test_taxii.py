import pytest
from httpx import AsyncClient
from backend.main import app

@pytest.mark.asyncio
async def test_taxii_discovery():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/api/v1/taxii/taxii2/")
    assert response.status_code == 200
    data = response.json()
    assert "CyberGhost-OSINT TAXII Server" in data["title"]
    assert len(data["api_roots"]) > 0

@pytest.mark.asyncio
async def test_taxii_api_root():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/api/v1/taxii/api1/")
    assert response.status_code == 200
    data = response.json()
    assert "CyberGhost Primary API Root" in data["title"]
    assert "taxii-2.1" in data["versions"]

@pytest.mark.asyncio
async def test_taxii_collections():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/api/v1/taxii/api1/collections/")
    assert response.status_code == 200
    data = response.json()
    assert len(data["collections"]) > 0
    assert data["collections"][0]["can_read"] is True
